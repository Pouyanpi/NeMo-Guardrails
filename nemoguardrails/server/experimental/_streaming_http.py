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

"""Bind guarded provider streams to an injected HTTP exchange."""

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from starlette.responses import Response, StreamingResponse

from nemoguardrails.server.experimental._buffered_kernel import InspectionStage, OperationProjectionFailed
from nemoguardrails.server.experimental._content_checker import ContentChecker, StreamBufferingPolicy
from nemoguardrails.server.experimental._guarded_operation import UnsupportedGuardedPayload
from nemoguardrails.server.experimental._guarded_stream import (
    StreamOutcomeRenderer,
    StreamProcessingFailed,
    StreamUpstreamFailed,
    guard_provider_stream,
    validate_streaming_policy,
)
from nemoguardrails.server.experimental._http_kernel import (
    BufferedHttpRequest,
    BufferedHttpResponse,
    HttpHeaders,
    ResponseBodyTooLarge,
)
from nemoguardrails.server.experimental.provider.stream import ProviderStreamAdapter
from nemoguardrails.server.experimental.provider.types import GuardedMessage


@dataclass(frozen=True, slots=True)
class StreamingHttpResponse:
    """Carry one successful response without choosing an HTTP client."""

    status_code: int
    headers: HttpHeaders
    body: AsyncIterator[bytes]

    def __post_init__(self) -> None:
        if not isinstance(self.status_code, int) or not 200 <= self.status_code <= 299:
            raise ValueError("A streaming HTTP response must have a successful status code.")
        if not hasattr(self.body, "__aiter__"):
            raise TypeError("A streaming HTTP response body must be an async iterator.")
        if any(not isinstance(name, bytes) or not isinstance(value, bytes) for name, value in self.headers):
            raise TypeError("Streaming HTTP response headers must contain byte pairs.")


StreamingHttpDispatch = Callable[[BufferedHttpRequest], Awaitable[StreamingHttpResponse | BufferedHttpResponse]]


def _response(value: BufferedHttpResponse) -> Response:
    response = Response(content=value.body, status_code=value.status_code)
    response.raw_headers = list(value.headers)
    return response


def _streaming_response(
    value: StreamingHttpResponse,
    body: AsyncIterator[bytes],
    *,
    may_modify: bool,
) -> StreamingResponse:
    response = StreamingResponse(body, status_code=value.status_code)
    response.raw_headers = [
        (name, header_value)
        for name, header_value in value.headers
        if not may_modify or name.lower() != b"content-length"
    ]
    return response


def _header_values(headers: HttpHeaders, name: bytes) -> tuple[bytes, ...]:
    return tuple(value for header_name, value in headers if header_name.lower() == name)


def _is_event_stream(headers: HttpHeaders) -> bool:
    values = _header_values(headers, b"content-type")
    return len(values) == 1 and values[0].partition(b";")[0].strip().lower() == b"text/event-stream"


def _has_identity_encoding(headers: HttpHeaders) -> bool:
    values = _header_values(headers, b"content-encoding")
    return not values or all(token.strip().lower() == b"identity" for value in values for token in value.split(b","))


async def _close_source(source: AsyncIterator[bytes]) -> None:
    close = getattr(source, "aclose", None)
    if callable(close):
        result = close()
        if inspect.isawaitable(result):
            await result


async def _relay(source: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    try:
        async for chunk in source:
            yield chunk
    finally:
        await _close_source(source)


async def execute_streaming_http(
    request: BufferedHttpRequest,
    *,
    dispatch: StreamingHttpDispatch,
    checker: ContentChecker,
    streaming_policy: StreamBufferingPolicy | None,
    input_message: GuardedMessage,
    adapter: ProviderStreamAdapter,
    render_outcome: StreamOutcomeRenderer,
    max_event_bytes: int,
    max_pending_bytes: int,
) -> Response:
    """Dispatch one prepared stream and preserve its HTTP lifecycle."""

    if max_event_bytes <= 0 or max_pending_bytes <= 0:
        raise ValueError("Streaming HTTP byte limits must be positive.")
    if streaming_policy is not None:
        validate_streaming_policy(streaming_policy)

    try:
        upstream = await dispatch(request)
    except Exception as failure:
        return _response(render_outcome(StreamUpstreamFailed(failure)))

    if isinstance(upstream, BufferedHttpResponse):
        if 200 <= upstream.status_code <= 299:
            return _response(
                render_outcome(
                    OperationProjectionFailed(
                        InspectionStage.OUTPUT,
                        UnsupportedGuardedPayload("A successful streaming response must have an open body."),
                    )
                )
            )
        if len(upstream.body) > max_pending_bytes:
            return _response(render_outcome(StreamUpstreamFailed(ResponseBodyTooLarge())))
        return _response(upstream)
    if not isinstance(upstream, StreamingHttpResponse):
        return _response(render_outcome(StreamProcessingFailed(TypeError("Unsupported streaming dispatch result."))))
    if not _is_event_stream(upstream.headers):
        await _close_source(upstream.body)
        return _response(
            render_outcome(
                OperationProjectionFailed(
                    InspectionStage.OUTPUT,
                    UnsupportedGuardedPayload("A successful provider stream must use text/event-stream."),
                )
            )
        )
    if streaming_policy is not None and not _has_identity_encoding(upstream.headers):
        await _close_source(upstream.body)
        return _response(
            render_outcome(
                OperationProjectionFailed(
                    InspectionStage.OUTPUT,
                    UnsupportedGuardedPayload("An inspected provider stream must use identity content encoding."),
                )
            )
        )
    if streaming_policy is None:
        return _streaming_response(upstream, _relay(upstream.body), may_modify=False)

    body = guard_provider_stream(
        upstream.body,
        checker=checker,
        streaming_policy=streaming_policy,
        input_message=input_message,
        adapter=adapter,
        render_outcome=render_outcome,
        max_event_bytes=max_event_bytes,
        max_pending_bytes=max_pending_bytes,
    )
    return _streaming_response(upstream, body, may_modify=True)
