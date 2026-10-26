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

"""Local Chat fixture for demonstrating output blocking without a model service."""

import json

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat(request: Request) -> Response:
    payload = await request.json()
    text = "Contact person@example.com"
    if payload.get("stream") is True:
        chunk = {
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}],
        }

        async def events():
            yield f"data: {json.dumps(chunk)}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")
    return JSONResponse({"choices": [{"message": {"role": "assistant", "content": text}}]})
