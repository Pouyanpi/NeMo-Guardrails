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

"""Reuse the repository's recording sanitizer and replay lifecycle fixtures.

Recordings are shared development infrastructure, not a server runtime dependency.
Keep credential redaction and cassette serialization in their existing owner.
"""

from tests.recorded.conftest import (
    close_owned_http_clients as close_owned_http_clients,
)
from tests.recorded.conftest import (
    nvidia_inference_key as nvidia_inference_key,
)
from tests.recorded.conftest import (
    openai_api_key as openai_api_key,
)
from tests.recorded.conftest import (
    pytest_recording_configure as pytest_recording_configure,
)
from tests.recorded.conftest import (
    recorded_cassette_path as recorded_cassette_path,
)
from tests.recorded.conftest import (
    service_api_key as service_api_key,
)
from tests.recorded.conftest import (
    strip_proxy_env_during_replay as strip_proxy_env_during_replay,
)
from tests.recorded.conftest import (
    vcr_cassette_dir as vcr_cassette_dir,
)
from tests.recorded.conftest import (
    vcr_config as vcr_config,
)
