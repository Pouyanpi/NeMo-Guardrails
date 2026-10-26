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

from pathlib import Path

import httpx
import pytest

from nemoguardrails.server.experimental.application import ConfigEntry, create_proxy_application
from nemoguardrails.server.experimental.examples.offline_upstream import app as upstream
from nemoguardrails.server.experimental.providers.openai.integration import create_openai_chat_integration


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_quickstart_fixture_blocks_output_and_checks_input_before_dispatch(stream):
    calls = []

    class UpstreamTransport(httpx.ASGITransport):
        async def handle_async_request(self, request):
            calls.append(request)
            return await super().handle_async_request(request)

    rails_path = Path(__file__).parents[3] / "nemoguardrails/server/experimental/examples/basic/rails"
    application = create_proxy_application(
        providers=(create_openai_chat_integration(base_url="http://offline/v1"),),
        rails_configs=(ConfigEntry("standard", rails_path),),
        http_transport_factory=lambda: UpstreamTransport(app=upstream),
    )
    async with application.router.lifespan_context(application):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://proxy") as client:
            response = await client.post(
                "/v1/chat/completions",
                json={"model": "offline", "messages": [{"role": "user", "content": "Hello!"}], "stream": stream},
            )
            assert response.status_code == (200 if stream else 400)
            assert "content_blocked" in response.text
            assert "person@example.com" not in response.text
            assert len(calls) == 1
            blocked_input = await client.post(
                "/v1/chat/completions",
                json={"model": "offline", "messages": [{"role": "user", "content": "person@example.com"}]},
            )
            assert blocked_input.status_code == 400
            assert blocked_input.json()["error"]["code"] == "content_blocked"
            assert len(calls) == 1
