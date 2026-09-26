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

import json

import pytest

from nemoguardrails.server.experimental._buffered_kernel import OperationProjectionFailed
from nemoguardrails.server.experimental._content_checker import ContentAllowed, StreamBufferingPolicy
from nemoguardrails.server.experimental._guarded_stream import StreamProcessingFailed, StreamUpstreamFailed
from nemoguardrails.server.experimental._http_kernel import BufferedHttpRequest, BufferedHttpResponse
from nemoguardrails.server.experimental._streaming_http import StreamingHttpResponse, execute_streaming_http
from nemoguardrails.server.experimental.provider.sse import ServerSentEvent
from nemoguardrails.server.experimental.provider.stream import (
    ClassifiedStreamAdapter,
    GuardedStreamEvent,
    StreamCapabilityProfile,
    StreamEventRole,
    StreamProjectionContract,
    StreamShapeCoverage,
)
from nemoguardrails.server.experimental.provider.types import GuardedMessage

CONTRACT = StreamProjectionContract(
    projection_id="test.stream",
    profile=StreamCapabilityProfile.SINGLE_TEXT_DELTA_V1,
    shapes=StreamShapeCoverage(
        guarded_shapes=frozenset({"text"}),
        opaque_shapes=frozenset({"end"}),
    ),
)


class Checker:
    def __init__(self):
        self.calls = []

    async def check_output(self, check):
        self.calls.append(check)
        return ContentAllowed()


class Classifier:
    contract = CONTRACT

    def classify_event(self, event: ServerSentEvent):
        if event.data == b"[END]":
            return GuardedStreamEvent("end", StreamEventRole.OPAQUE_METADATA)
        payload = json.loads(event.data or b"")
        return GuardedStreamEvent("text", StreamEventRole.GUARDED_TEXT, payload["text"])


class Hooks:
    def observe_event(self, event, classified):
        pass

    def validate_end_of_stream(self):
        pass

    def encode_error(self, body):
        return (b"data: " + body + b"\n\n", b"data: [END]\n\n")


class Source:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.chunks)
        except StopIteration:
            raise StopAsyncIteration

    async def aclose(self):
        self.closed = True


REQUEST = BufferedHttpRequest("POST", "/v1/generate", b"/v1/generate", b"", (), b"request")


def render_outcome(outcome):
    if isinstance(outcome, OperationProjectionFailed):
        code = "projection_failed"
    elif isinstance(outcome, StreamUpstreamFailed):
        code = "upstream_failed"
    elif isinstance(outcome, StreamProcessingFailed):
        code = "processing_failed"
    else:
        code = "stream_failure"
    return BufferedHttpResponse(502, ((b"content-type", b"text/plain"),), code.encode())


async def response_body(response):
    body = getattr(response, "body", None)
    if isinstance(body, bytes):
        return body
    return b"".join([chunk async for chunk in response.body_iterator])


async def execute(dispatch, *, policy=StreamBufferingPolicy(1, 0), checker=None, **limits):
    return await execute_streaming_http(
        REQUEST,
        dispatch=dispatch,
        checker=checker or Checker(),
        streaming_policy=policy,
        input_message=GuardedMessage("user", "question"),
        adapter=ClassifiedStreamAdapter(Classifier(), Hooks()),
        render_outcome=render_outcome,
        max_event_bytes=limits.get("max_event_bytes", 1024),
        max_pending_bytes=limits.get("max_pending_bytes", 1024),
    )


@pytest.mark.asyncio
async def test_inspected_stream_preserves_events_and_removes_stale_content_length():
    stream = b'data: {"text":"answer"}\n\ndata: [END]\n\n'
    source = Source([stream[:7], stream[7:]])
    checker = Checker()

    async def dispatch(_request):
        return StreamingHttpResponse(
            200,
            (
                (b"content-type", b"text/event-stream"),
                (b"content-length", str(len(stream)).encode()),
                (b"x-provider-id", b"stream-id"),
            ),
            source,
        )

    response = await execute(dispatch, checker=checker)

    assert await response_body(response) == stream
    assert (b"x-provider-id", b"stream-id") in response.raw_headers
    assert all(name.lower() != b"content-length" for name, _ in response.raw_headers)
    assert checker.calls[0].output_content == "answer"
    assert source.closed is True


@pytest.mark.asyncio
async def test_uninspected_stream_preserves_opaque_bytes_and_original_length():
    stream = b"opaque provider bytes"
    source = Source([stream])

    async def dispatch(_request):
        return StreamingHttpResponse(
            200,
            ((b"content-type", b"text/event-stream"), (b"content-length", str(len(stream)).encode())),
            source,
        )

    response = await execute(dispatch, policy=None)

    assert await response_body(response) == stream
    assert (b"content-length", str(len(stream)).encode()) in response.raw_headers
    assert source.closed is True


@pytest.mark.asyncio
async def test_provider_http_error_is_bounded_and_preserved_without_event_inspection():
    async def dispatch(_request):
        return BufferedHttpResponse(429, ((b"content-type", b"application/json"),), b'{"error":"busy"}')

    response = await execute(dispatch)

    assert response.status_code == 429
    assert await response_body(response) == b'{"error":"busy"}'

    oversized = await execute(dispatch, max_pending_bytes=4)
    assert oversized.status_code == 502
    assert await response_body(oversized) == b"upstream_failed"


@pytest.mark.asyncio
async def test_buffered_success_cannot_bypass_stream_inspection():
    async def dispatch(_request):
        return BufferedHttpResponse(200, ((b"content-type", b"text/plain"),), b"unchecked success")

    response = await execute(dispatch)

    assert response.status_code == 502
    assert await response_body(response) == b"projection_failed"


@pytest.mark.asyncio
async def test_dispatch_failure_is_rendered_before_streaming_starts():
    async def dispatch(_request):
        raise RuntimeError("private upstream detail")

    response = await execute(dispatch)

    assert response.status_code == 502
    assert await response_body(response) == b"upstream_failed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        ((b"content-type", b"application/json"),),
        ((b"content-type", b"text/event-stream"), (b"content-encoding", b"gzip")),
        ((b"content-type", b"text/event-stream"), (b"content-type", b"text/event-stream")),
    ],
)
async def test_unsupported_inspected_success_closes_source_before_headers(headers):
    source = Source([b"hidden provider content"])

    async def dispatch(_request):
        return StreamingHttpResponse(200, headers, source)

    response = await execute(dispatch)

    assert response.status_code == 502
    assert await response_body(response) == b"projection_failed"
    assert source.closed is True


@pytest.mark.asyncio
async def test_unsafe_stream_policy_is_rejected_before_dispatch():
    calls = []

    async def dispatch(_request):
        calls.append(True)
        raise AssertionError("unsafe policy must stop before dispatch")

    with pytest.raises(ValueError, match="cannot release"):
        await execute(dispatch, policy=StreamBufferingPolicy(1, 0, True))

    assert calls == []
