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

"""Build and install the two distributions without editable checkout imports."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def run_uv(*args, cwd, env=None):
    """Run offline package tooling and retain diagnostics on failure."""
    result = subprocess.run(["uv", *map(str, args)], cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.fixture(scope="session")
def distributions(tmp_path_factory):
    """Build both wheels and source distributions once per test process."""
    destination = tmp_path_factory.mktemp("proxy-distributions")
    run_uv("build", "--offline", "--all-packages", "--out-dir", destination, cwd=ROOT)
    return destination


@pytest.fixture(scope="session")
def installed_proxy(distributions, tmp_path_factory):
    """Install only locked runtime dependencies and local wheels in a fresh venv."""
    directory = tmp_path_factory.mktemp("installed-proxy")
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("UV_", "PYTHON"))}
    environment["NEMO_GUARDRAILS_NO_USAGE_STATS"] = "1"
    venv = directory / "venv"
    run_uv("venv", "--offline", venv, cwd=directory, env=environment)
    run_uv(
        "sync",
        "--locked",
        "--offline",
        "--package",
        "guardrails-proxy",
        "--no-dev",
        "--no-install-workspace",
        cwd=ROOT,
        env={**environment, "UV_PROJECT_ENVIRONMENT": str(venv)},
    )
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run_uv(
        "pip",
        "install",
        "--offline",
        "--python",
        python,
        "--no-deps",
        *sorted(distributions.glob("*.whl")),
        cwd=directory,
        env=environment,
    )
    return directory, python, environment
