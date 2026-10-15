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

"""Keep shared tooling and publication boundaries correct across both packages."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.25.0"
WHEEL = f"nemoguardrails-{VERSION}-py3-none-any.whl"
SDIST = f"nemoguardrails-{VERSION}.tar.gz"


def workflow(name):
    """Read a checked-in workflow without executing GitHub actions."""
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"))


def test_shared_license_and_recorded_type_coverage():
    """Moved sources retain the library license and recorded-test typing coverage."""
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"guardrails-server/tests/recorded/**"' in project
    assert (ROOT / "LICENSE-Apache-2.0.txt").read_bytes() == (
        ROOT / "guardrails-server/LICENSE-Apache-2.0.txt"
    ).read_bytes()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("tests/test_example.py", 0),
        ("benchmark/tests/test_example.py", 0),
        ("guardrails-server/tests/proxy_tests/test_example.py", 0),
        ("guardrails-server/tests/packaging/conftest.py", 0),
        ("guardrails-server/src/guardrails_proxy/cli.py", 1),
        ("guardrails-server/tests-not-a-test/example.py", 1),
    ],
)
def test_regression_proof_recognizes_package_tests(path, expected):
    """Run the workflow's actual shell predicate without its history rewrite."""
    steps = workflow("pr-fix-regression-proof.yml")["jobs"]["regression-proof"]["steps"]
    script = next(step["run"] for step in steps if step.get("id") == "prove")
    predicate = script[script.index("is_testdir()") : script.index("is_testmod()")]
    result = subprocess.run(["bash", "-c", predicate + '\nis_testdir "$1"', "test", path], timeout=10)
    assert result.returncode == expected


def test_size_labels_recognize_both_test_trees():
    """Evaluate the inline classifier without API access or PR code checkout."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to execute the GitHub-script classifier")
    steps = workflow("pr-size-label.yml")["jobs"]["size-label"]["steps"]
    script = steps[0]["with"]["script"]
    predicate = script[script.index("const isTests") : script.index("let code")]
    result = subprocess.run(
        [
            node,
            "-e",
            predicate
            + """
const assert = require('node:assert/strict');
assert(isTests('tests/test_example.py'));
assert(isTests('benchmark/tests/test_example.py'));
assert(isTests('guardrails-server/tests/packaging/test_example.py'));
assert(!isTests('guardrails-server/src/guardrails_proxy/cli.py'));
assert(!isTests('guardrails-server/tests-not-a-test/example.py'));
""",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


def test_packaging_acceptance_has_its_own_serial_job():
    """Ordinary matrix runs exclude package builds, which retain an explicit owner."""
    steps = workflow("_test.yml")["jobs"]["tests"]["steps"]
    for step in steps:
        run = step.get("run", "")
        if "uv sync" in run:
            assert all("--all-packages" in line for line in run.splitlines() if "uv sync" in line)
        if run.startswith("make test"):
            assert "--ignore=guardrails-server/tests/packaging" in run
    package = workflow("proxy-package.yml")
    assert package["permissions"] == {"contents": "read"}
    steps = package["jobs"]["package"]["steps"]
    assert any(step.get("run") == "uv sync --locked --all-packages --group dev" for step in steps)
    assert steps[-1]["run"] == "make test-proxy-package"
    result = subprocess.run(["make", "-n", "test-proxy-package"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "-n 0 guardrails-server/tests/packaging" in result.stdout
    assert "--block-network --allowed-hosts=127.0.0.1" in result.stdout
    assert "-u NVIDIA_INFERENCE_KEY" in result.stdout


@pytest.mark.parametrize("version", [VERSION, "0.25.0.dev0", "0.25.0rc1"])
def test_library_artifact_gate_accepts_only_the_requested_pair(tmp_path, version):
    """Normal release and development builds have one pure wheel and one sdist."""
    for name in (f"nemoguardrails-{version}-py3-none-any.whl", f"nemoguardrails-{version}.tar.gz"):
        (tmp_path / name).touch()
    result = subprocess.run(
        ["bash", str(ROOT / ".github/scripts/check-library-artifacts.sh"), str(tmp_path), version],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("fault", ["proxy", "stale", "empty", "missing", "hidden", "directory", "symlink"])
def test_library_artifact_gate_fails_closed(tmp_path, fault):
    """Never publish mixed workspace outputs, unexpected files or redirected files."""
    directory = tmp_path / "artifacts"
    directory.mkdir()
    (directory / WHEEL).touch()
    (directory / SDIST).touch()
    if fault == "proxy":
        (directory / "guardrails_proxy-0.1.0a1-py3-none-any.whl").touch()
    elif fault == "stale":
        (directory / WHEEL).rename(directory / "nemoguardrails-0.24.0-py3-none-any.whl")
    elif fault in ("empty", "missing"):
        (directory / WHEEL).unlink()
        if fault == "empty":
            (directory / SDIST).unlink()
    elif fault == "hidden":
        (directory / ".unexpected").touch()
    elif fault == "directory":
        (directory / WHEEL).unlink()
        (directory / WHEEL).mkdir()
    elif fault == "symlink":
        (directory / WHEEL).unlink()
        (tmp_path / "other.whl").touch()
        (directory / WHEEL).symlink_to(tmp_path / "other.whl")
    result = subprocess.run(
        ["bash", str(ROOT / ".github/scripts/check-library-artifacts.sh"), str(directory), VERSION],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0


@pytest.mark.parametrize("fault", [None, "proxy", "stale", "empty", "extra"])
def test_manual_publisher_restricts_the_downloaded_wheel(tmp_path, fault):
    """The legacy manual publisher applies its gate without checking out PR code."""
    directory = tmp_path / "dist/nemoguardrails"
    directory.mkdir(parents=True)
    if fault != "empty":
        name = WHEEL
        if fault == "proxy":
            name = "guardrails_proxy-0.1.0a1-py3-none-any.whl"
        elif fault == "stale":
            name = "nemoguardrails-0.24.0-py3-none-any.whl"
        (directory / name).touch()
    if fault == "extra":
        (directory / SDIST).touch()
    steps = workflow("publish-wheel.yml")["jobs"]["publish-wheel"]["steps"]
    gate = next(step for step in steps if step["name"] == "Validate library-only wheel")
    result = subprocess.run(
        ["bash", "-eu", "-c", gate["run"]],
        cwd=tmp_path,
        env={**os.environ, "LIBRARY_VERSION": VERSION},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) == (fault is None), result.stderr


@pytest.mark.parametrize("version", [VERSION, "v0.25.0", "0.25.0.dev0", "../0.25.0", "0.25.0$(touch injected)"])
def test_manual_publisher_validates_version_before_download(tmp_path, version):
    """Untrusted dispatch input is treated as data and limited to release versions."""
    steps = workflow("publish-wheel.yml")["jobs"]["publish-wheel"]["steps"]
    assert steps[0]["name"] == "Validate version"
    result = subprocess.run(
        ["bash", "-eu", "-c", steps[0]["run"]],
        cwd=tmp_path,
        env={**os.environ, "LIBRARY_VERSION": version},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) == (version == VERSION)
    assert not (tmp_path / "injected").exists()


def test_publishers_do_not_upload_the_workspace_distribution_directory():
    """Both publishing routes explicitly scope output and retain pre-publish gates."""
    for name, job, gate in (
        ("publish-pypi-approval.yml", "publish-pypi", "Validate library-only artifacts"),
        ("publish-wheel.yml", "publish-wheel", "Validate library-only wheel"),
    ):
        steps = workflow(name)["jobs"][job]["steps"]
        publish_index = next(i for i, step in enumerate(steps) if "pypi-publish@" in step.get("uses", ""))
        assert steps[publish_index]["with"]["packages-dir"] == "dist/nemoguardrails/"
        assert next(i for i, step in enumerate(steps) if step.get("name") == gate) < publish_index
    build = (ROOT / ".github/scripts/build.sh").read_text(encoding="utf-8")
    assert "uv build --package nemoguardrails --out-dir dist/nemoguardrails" in build
    assert "check-library-artifacts.sh" in build
