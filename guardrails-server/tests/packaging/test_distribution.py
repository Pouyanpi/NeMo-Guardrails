# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Check package ownership, runtime assets and standalone source builds."""

import json
import subprocess
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest
from packaging.requirements import Requirement


def test_distribution_ownership_and_dependencies(distributions):
    """The library keeps its legacy server but never embeds or requires the proxy."""
    library = next(distributions.glob("nemoguardrails-*.whl"))
    proxy = next(distributions.glob("guardrails_proxy-*.whl"))
    with zipfile.ZipFile(library) as archive:
        names = archive.namelist()
        assert "nemoguardrails/server/api.py" in names
        assert not any("guardrails_proxy/" in name or "/server/experimental/" in name for name in names)
        metadata = Parser().parsestr(archive.read(next(n for n in names if n.endswith("/METADATA"))).decode())
        assert not any(Requirement(value).name == "guardrails-proxy" for value in metadata.get_all("Requires-Dist"))
    with zipfile.ZipFile(proxy) as archive:
        names = archive.namelist()
        assert "guardrails_proxy/__main__.py" in names
        assert "guardrails_proxy/examples/basic/proxy.yaml" in names
        assert "guardrails_proxy/examples/basic/rails/config.yml" in names
        assert "guardrails_proxy/application.md" in names
        assert any(name.endswith(".schema.json") for name in names)
        assert any(name.endswith("chat-completions.guard.yaml") for name in names)
        assert not any(name.startswith(("nemoguardrails/", "tests/")) or "/cassettes/" in name for name in names)
        metadata = Parser().parsestr(archive.read(next(n for n in names if n.endswith("/METADATA"))).decode())
        requirement = next(
            Requirement(value)
            for value in metadata.get_all("Requires-Dist")
            if Requirement(value).name == "nemoguardrails"
        )
        assert not requirement.extras
        assert requirement.url is None
        assert str(requirement.specifier) == "<0.26,>=0.25.0.dev0"


@pytest.mark.parametrize("package", ["guardrails_proxy", "nemoguardrails"])
def test_sdist_builds_without_repository(distributions, tmp_path, package):
    """Neither source distribution needs its workspace sibling to build."""
    source = next(distributions.glob(f"{package}-*.tar.gz"))
    with tarfile.open(source) as archive:
        names = archive.getnames()
        excluded = "/nemoguardrails/" if package == "guardrails_proxy" else "/guardrails-server/"
        assert not any(excluded in name for name in names)
        archive.extractall(tmp_path, filter="data")
    directory = next(tmp_path.glob(f"{package}-*"))
    result = subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(tmp_path / "dist")],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    original = next(distributions.glob(f"{package}-*.whl"))
    rebuilt = next((tmp_path / "dist").glob("*.whl"))
    with zipfile.ZipFile(original) as left, zipfile.ZipFile(rebuilt) as right:
        assert set(left.namelist()) == set(right.namelist())
        assert all(left.read(name) == right.read(name) for name in left.namelist())


def test_installed_imports_and_assets_are_outside_checkout(installed_proxy):
    """A clean runtime-only installation resolves both packages and bundled assets."""
    directory, python, environment = installed_proxy
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            """
import json
from importlib.resources import files
import guardrails_proxy
import nemoguardrails
from guardrails_proxy.application import create_proxy_application
from guardrails_proxy._application_manifest import load_manifest
example = files('guardrails_proxy') / 'examples/basic/proxy.yaml'
application = create_proxy_application(load_manifest(example))
print(json.dumps([guardrails_proxy.__file__, nemoguardrails.__file__, str(example)]))
""",
        ],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for path in json.loads(result.stdout):
        assert Path(path).is_relative_to(directory / "venv")
