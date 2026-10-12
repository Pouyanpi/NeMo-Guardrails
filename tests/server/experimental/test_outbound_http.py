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

import httpx
import pytest

from nemoguardrails.server.experimental._http_kernel import (
    BufferedHttpRequest,
    BufferedHttpResponse,
    ResponseBodyTooLarge,
)
from nemoguardrails.server.experimental._outbound_http import ApplicationHttpDispatcher
from nemoguardrails.server.experimental._streaming_http import StreamingHttpResponse


class TrackedStream(httpx.AsyncByteStream):
    def __init__(self, chunks, failure=None):
        self._chunks = iter(chunks)
        self._failure = failure
        self.closed = False

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk
        if self._failure is not None:
            raise self._failure

    async def aclose(self):
        self.closed = True


def buffered_request(path="/v1/chat/completions", raw_path=b"/v1/chat/completions", **updates):
    values = {
        "method": "POST",
        "path": path,
        "raw_path": raw_path,
        "query": b"trace=opaque",
        "headers": (
            (b"host", b"proxy.test"),
            (b"authorization", b"Bearer provider-key"),
            (b"content-type", b"application/json"),
            (b"content-length", b"999"),
            (b"accept-encoding", b"gzip"),
            (b"connection", b"x-remove"),
            (b"x-remove", b"connection-specific"),
            (b"x-provider-option", b"preserve"),
        ),
        "body": b'{"model":"provider/model"}',
    }
    values.update(updates)
    return BufferedHttpRequest(**values)


@pytest.mark.asyncio
async def test_buffered_dispatch_maps_mount_and_preserves_end_to_end_values():
    requests = []

    async def upstream(request):
        requests.append(request)
        return httpx.Response(
            201,
            headers=(
                (b"content-type", b"application/json"),
                (b"content-length", b"17"),
                (b"connection", b"x-remove"),
                (b"x-remove", b"connection-specific"),
                (b"x-request-id", b"provider-id"),
            ),
            stream=TrackedStream([b'{"answer":"safe"}']),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(
            client,
            base_url="https://provider.test/provider/v1",
            mount_path="/v1",
        )
        response = await dispatcher.dispatch(buffered_request())

        assert client.is_closed is False

    assert response == BufferedHttpResponse(
        201,
        (
            (b"content-type", b"application/json"),
            (b"content-length", b"17"),
            (b"x-request-id", b"provider-id"),
        ),
        b'{"answer":"safe"}',
    )
    request = requests[0]
    assert str(request.url) == "https://provider.test/provider/v1/chat/completions?trace=opaque"
    assert request.content == b'{"model":"provider/model"}'
    assert request.headers["authorization"] == "Bearer provider-key"
    assert request.headers["accept-encoding"] == "gzip"
    assert request.headers["x-provider-option"] == "preserve"
    assert request.headers["content-length"] == str(len(request.content))
    assert "x-remove" not in request.headers


@pytest.mark.asyncio
async def test_buffered_dispatch_bounds_and_closes_response():
    stream = TrackedStream([b"123", b"456"])

    async def upstream(_request):
        return httpx.Response(200, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test", max_response_body_bytes=5)

        with pytest.raises(ResponseBodyTooLarge):
            await dispatcher.dispatch(buffered_request())

    assert stream.closed is True


@pytest.mark.asyncio
async def test_stream_dispatch_returns_open_success_and_closes_after_consumption():
    stream = TrackedStream([b"data: one\n\n", b"data: [DONE]\n\n"])

    async def upstream(_request):
        return httpx.Response(
            200,
            headers=((b"content-type", b"text/event-stream"), (b"x-request-id", b"stream-id")),
            stream=stream,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test")
        response = await dispatcher.stream_dispatch(buffered_request())

        assert isinstance(response, StreamingHttpResponse)
        assert stream.closed is False
        assert b"".join([chunk async for chunk in response.body]) == b"data: one\n\ndata: [DONE]\n\n"

    assert response.headers == ((b"content-type", b"text/event-stream"), (b"x-request-id", b"stream-id"))
    assert stream.closed is True


@pytest.mark.asyncio
async def test_stream_dispatch_source_closes_before_iteration():
    stream = TrackedStream([b"never consumed"])

    async def upstream(_request):
        return httpx.Response(200, headers=((b"content-type", b"application/json"),), stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test")
        response = await dispatcher.stream_dispatch(buffered_request())
        assert isinstance(response, StreamingHttpResponse)

        await response.body.aclose()

    assert stream.closed is True


@pytest.mark.asyncio
async def test_stream_dispatch_buffers_and_closes_provider_error():
    stream = TrackedStream([b'{"error":"rate limited"}'])

    async def upstream(_request):
        return httpx.Response(
            429,
            headers=((b"content-type", b"application/json"), (b"retry-after", b"1")),
            stream=stream,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test")
        response = await dispatcher.stream_dispatch(buffered_request())

    assert response == BufferedHttpResponse(
        429,
        ((b"content-type", b"application/json"), (b"retry-after", b"1")),
        b'{"error":"rate limited"}',
    )
    assert stream.closed is True


@pytest.mark.asyncio
async def test_stream_source_failure_closes_response():
    stream = TrackedStream([], RuntimeError("upstream disconnected"))

    async def upstream(_request):
        return httpx.Response(200, headers=((b"content-type", b"text/event-stream"),), stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test")
        response = await dispatcher.stream_dispatch(buffered_request())
        assert isinstance(response, StreamingHttpResponse)

        with pytest.raises(RuntimeError, match="upstream disconnected"):
            await response.body.__anext__()

    assert stream.closed is True


@pytest.mark.asyncio
async def test_request_outside_mount_stops_before_upstream_dispatch():
    requests = []

    async def upstream(request):
        requests.append(request)
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        dispatcher = ApplicationHttpDispatcher(client, base_url="https://provider.test/v1", mount_path="/v1")

        with pytest.raises(ValueError, match="outside the configured mount"):
            await dispatcher.dispatch(buffered_request(path="/other", raw_path=b"/other"))

    assert requests == []


@pytest.mark.parametrize(
    ("base_url", "mount_path", "limit", "timeout", "error"),
    [
        ("provider.test", "", 1, 1, "absolute HTTP"),
        ("ftp://provider.test", "", 1, 1, "absolute HTTP"),
        ("https://user:secret@provider.test", "", 1, 1, "credentials"),
        ("https://provider.test?query=yes", "", 1, 1, "query or fragment"),
        ("https://provider.test", "relative", 1, 1, "absolute ASCII"),
        ("https://provider.test", "/møunt", 1, 1, "absolute ASCII"),
        ("https://provider.test", "", 0, 1, "positive"),
        ("https://provider.test", "", True, 1, "positive"),
        ("https://provider.test", "", 1, float("inf"), "positive"),
    ],
)
@pytest.mark.asyncio
async def test_dispatcher_rejects_invalid_application_settings(base_url, mount_path, limit, timeout, error):
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match=error):
            ApplicationHttpDispatcher(
                client,
                base_url=base_url,
                mount_path=mount_path,
                max_response_body_bytes=limit,
                timeout=timeout,
            )
