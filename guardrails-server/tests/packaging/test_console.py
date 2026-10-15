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

"""Exercise the installed CLI and packaged example without source-path imports."""

import json
import os
import subprocess
from functools import partial
from pathlib import Path

import pytest
from proxy_tests import test_proxy_launcher as launcher


@pytest.fixture(scope="session")
def installed_commands(installed_proxy):
    """Locate entry points and example assets in the wheel-only environment."""
    directory, python, environment = installed_proxy
    console = python.parent / ("guardrails-proxy.exe" if os.name == "nt" else "guardrails-proxy")
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "from importlib.resources import files; print(files('guardrails_proxy') / 'examples/basic')",
        ],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    example = Path(result.stdout.strip())
    assert example.is_relative_to(directory / "venv")
    return (str(console),), (str(python), "-I", "-m", "guardrails_proxy"), example


@pytest.mark.parametrize("command", ["--help", "schema", "validate", "inspect"])
def test_installed_console_matches_module(installed_proxy, installed_commands, command):
    """Both entry points expose the same commands and declaration semantics."""
    directory, _, environment = installed_proxy
    console, module, example = installed_commands
    outputs = []
    for prefix in (console, module):
        arguments = [command]
        if command in ("validate", "inspect"):
            arguments.append(str(example / "proxy.yaml"))
        result = subprocess.run(
            [*prefix, *arguments],
            cwd=directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(result.stdout)
    if command in ("schema", "inspect"):
        assert json.loads(outputs[0]) == json.loads(outputs[1])
    elif command == "validate":
        assert outputs[0] == outputs[1]
        assert "Valid declaration." in outputs[0]
    else:
        for output in outputs:
            assert all(name in output for name in ("validate", "inspect", "schema", "serve"))


@pytest.fixture
def installed_launcher(installed_commands, monkeypatch):
    """Reuse socket assertions with an installed executable and installed Rails assets."""
    console, _, example = installed_commands
    monkeypatch.setattr(launcher, "launched_proxy", partial(launcher.launched_proxy, command=console, example=example))


@pytest.mark.asyncio
@pytest.mark.parametrize("dialect", [None, "litellm"])
async def test_installed_buffered_streaming_and_blocking(tmp_path, installed_launcher, dialect):
    """The wheel preserves Chat/Responses and native/LiteLLM allow/block behavior."""
    await launcher.test_localhost_launcher_buffered_streaming_and_blocking(tmp_path, dialect)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["chat_completions", "responses", "passthrough"])
async def test_installed_disconnect_closes_upstream(tmp_path, installed_launcher, operation):
    """Installed server disconnects release real outbound HTTP sockets."""
    await launcher.test_localhost_disconnect_closes_upstream_socket(tmp_path, operation)
