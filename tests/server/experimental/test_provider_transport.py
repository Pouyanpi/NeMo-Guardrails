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

import asyncio

import httpx
import pytest
from starlette.requests import Request

from nemoguardrails.server.experimental._http_kernel import (
    BufferedHttpRequest,
    BufferedHttpResponse,
    HttpDispatchFailed,
    ResponseBodyTooLarge,
)
from nemoguardrails.server.experimental._provider_transport import ProviderTransport
from nemoguardrails.server.experimental._streaming_http import StreamingHttpResponse
from nemoguardrails.server.experimental.provider.integration import UpstreamSettings


@pytest.mark.asyncio
@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("failure_type", [httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError])
async def test_network_failure_is_translated_without_exposing_details(httpx_mock, streaming, failure_type):
    failure = failure_type("private upstream detail")
    httpx_mock.add_exception(failure)
    async with httpx.AsyncClient() as client:
        dispatcher = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        dispatch = dispatcher.stream_dispatch if streaming else dispatcher.dispatch
        with pytest.raises(HttpDispatchFailed) as caught:
            await dispatch(buffered_request())
    assert caught.value.__cause__ is failure
    assert "private upstream detail" not in str(caught.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("streaming", [False, True])
async def test_buffered_read_failure_is_translated_and_closed(httpx_mock, streaming):
    failure = httpx.ReadError("private upstream detail")
    stream = TrackedStream([b"partial"], failure)
    httpx_mock.add_response(status_code=503 if streaming else 200, stream=stream)
    async with httpx.AsyncClient() as client:
        dispatcher = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        dispatch = dispatcher.stream_dispatch if streaming else dispatcher.dispatch
        with pytest.raises(HttpDispatchFailed) as caught:
            await dispatch(buffered_request())
    assert caught.value.__cause__ is failure
    assert stream.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [asyncio.CancelledError(), ValueError("bad transport")])
async def test_dispatch_preserves_cancellation_and_programming_errors(httpx_mock, failure):
    async def fail(_request):
        raise failure

    httpx_mock.add_callback(fail)
    async with httpx.AsyncClient() as client:
        dispatcher = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        with pytest.raises(type(failure)) as caught:
            await dispatcher.dispatch(buffered_request())
    assert caught.value is failure


@pytest.mark.asyncio
async def test_requests_do_not_inherit_another_callers_cookies_or_client_credentials(httpx_mock):
    for _ in range(3):
        httpx_mock.add_response(
            headers={"set-cookie": "session=previous-caller; Path=/"}, stream=TrackedStream([b"ok"])
        )
    async with httpx.AsyncClient(auth=("default-user", "default-password"), headers={"x-default": "private"}) as client:
        client.cookies.set("session", "preexisting", domain="provider.test", path="/")
        dispatcher = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        for headers in [(), ((b"cookie", b"session=explicit-caller"),), ()]:
            await dispatcher.dispatch(buffered_request(headers=headers))
    requests = httpx_mock.get_requests()
    assert [request.headers.get("cookie") for request in requests] == [None, "session=explicit-caller", None]
    assert all("authorization" not in request.headers and "x-default" not in request.headers for request in requests)
    assert requests[0].extensions["timeout"]["read"] == 30.0


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
        transport = ProviderTransport(
            UpstreamSettings("https://provider.test/provider/v1", "/v1"),
            client,
        )
        response = await transport.dispatch(buffered_request())

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
    assert request.headers["accept-encoding"] == "identity"
    assert request.headers["x-provider-option"] == "preserve"
    assert request.headers["content-length"] == str(len(request.content))
    assert "x-remove" not in request.headers


@pytest.mark.asyncio
async def test_buffered_dispatch_bounds_and_closes_response():
    stream = TrackedStream([b"123", b"456"])

    async def upstream(_request):
        return httpx.Response(200, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        transport = ProviderTransport(
            UpstreamSettings("https://provider.test"),
            client,
            max_response_body_bytes=5,
        )

        with pytest.raises(ResponseBodyTooLarge):
            await transport.dispatch(buffered_request())

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
        transport = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        response = await transport.stream_dispatch(buffered_request())

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
        transport = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        response = await transport.stream_dispatch(buffered_request())
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
        transport = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        response = await transport.stream_dispatch(buffered_request())

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
        transport = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        response = await transport.stream_dispatch(buffered_request())
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
        transport = ProviderTransport(UpstreamSettings("https://provider.test/v1", "/v1"), client)

        with pytest.raises(ValueError, match="outside the configured mount"):
            await transport.dispatch(buffered_request(path="/other", raw_path=b"/other"))

    assert requests == []


@pytest.mark.asyncio
async def test_dispatch_does_not_repeat_base_path_already_present_after_mount():
    requests = []

    async def upstream(request):
        requests.append(request)
        return httpx.Response(200, stream=TrackedStream([]))

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        transport = ProviderTransport(
            UpstreamSettings("https://provider.test/v1", "/providers/openai"),
            client,
        )
        await transport.dispatch(
            buffered_request(
                path="/providers/openai/v1/models",
                raw_path=b"/providers/openai/v1/models",
            )
        )

    assert str(requests[0].url) == "https://provider.test/v1/models?trace=opaque"


@pytest.mark.asyncio
async def test_dispatch_strips_only_declared_control_headers():
    requests = []

    async def upstream(request):
        requests.append(request)
        return httpx.Response(200, stream=TrackedStream([]))

    headers = buffered_request().headers + ((b"x-proxy-control", b"local"),)
    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        transport = ProviderTransport(
            UpstreamSettings("https://provider.test"),
            client,
            control_headers={"x-proxy-control"},
        )
        await transport.dispatch(buffered_request(headers=headers))

    assert requests[0].headers["authorization"] == "Bearer provider-key"
    assert requests[0].headers["x-provider-option"] == "preserve"
    assert "x-proxy-control" not in requests[0].headers


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
async def test_provider_transport_rejects_invalid_application_settings(base_url, mount_path, limit, timeout, error):
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match=error):
            ProviderTransport(
                UpstreamSettings(base_url, mount_path),
                client,
                max_response_body_bytes=limit,
                timeout=timeout,
            )


@pytest.mark.parametrize("control_header", ["", " X-Control", "X-Control", "x-møunt"])
@pytest.mark.asyncio
async def test_provider_transport_rejects_invalid_control_headers(control_header):
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="lowercase ASCII"):
            ProviderTransport(
                UpstreamSettings("https://provider.test"),
                client,
                control_headers={control_header},
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,status,length", [("HEAD", 200, "13"), ("GET", 204, None), ("GET", 205, "0"), ("GET", 304, "13")]
)
async def test_bodyless_passthrough_closes_upstream_before_returning(method, status, length):
    stream = TrackedStream([b"hidden content"])

    async def respond(_request):
        return httpx.Response(status, headers={"content-length": "13"}, stream=stream)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": method,
            "scheme": "https",
            "path": "/v1/models",
            "raw_path": b"/v1/models",
            "query_string": b"",
            "headers": [],
            "server": ("proxy.test", 443),
        },
        receive,
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        transport = ProviderTransport(UpstreamSettings("https://provider.test"), client)
        response = await transport.passthrough(request)

    assert response.body == b""
    assert response.status_code == status
    assert response.headers.get("content-length") == length
    assert stream.closed
