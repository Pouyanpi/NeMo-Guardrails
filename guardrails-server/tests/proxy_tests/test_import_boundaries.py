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

"""Test that private proxy modules remain independently importable."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "guardrails_proxy",
        "guardrails_proxy._buffered_kernel",
        "guardrails_proxy._content_checker",
        "guardrails_proxy._guarded_operation",
        "guardrails_proxy._http_kernel",
        "guardrails_proxy.provider.types",
    ],
)
def test_private_kernel_modules_import_in_a_fresh_interpreter(module):
    """Import each private module without relying on ambient import state."""

    completed = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
    )

    assert completed.returncode == 0, completed.stderr
