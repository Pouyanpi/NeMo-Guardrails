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
import subprocess
import sys

import pytest

from nemoguardrails.server.experimental.provider.sse import ServerSentEvent
from nemoguardrails.server.experimental.provider.stream import StreamEventRole, UnsupportedProviderStream
from nemoguardrails.server.experimental.providers.openai.chat_completions.request_binding import (
    PAYLOAD_CONTRACT,
    REQUEST_CONSTRAINED_FIELDS,
    REQUEST_GUARDED_FIELDS,
    REQUEST_OPAQUE_FIELDS,
    STREAM_SELECTOR_FIELD,
)
from nemoguardrails.server.experimental.providers.openai.chat_completions.stream_classifier import (
    CAPABILITY_PROFILE,
    GUARDED_SHAPES,
    OPAQUE_SHAPES,
    PROVIDER_DOCUMENT_SHA256,
    PROVIDER_ERROR_SHAPES,
    PROVIDER_REVISION,
    STREAM_CLASSIFIER,
    STREAM_CONTRACT,
    STREAM_FIELDS,
    STREAM_SOURCE_SCHEMA,
)
from nemoguardrails.server.experimental.providers.openai.chat_completions.stream_hooks import (
    ChatCompletionsStreamHooks,
)


def event(payload):
    data = payload if isinstance(payload, bytes) else json.dumps(payload, separators=(",", ":")).encode()
    return ServerSentEvent.from_bytes(b"data: " + data + b"\n\n")


def chunk(delta, **fields):
    return {
        "id": "chatcmpl-stream",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": delta, **fields}],
        "opaque": {"preserved": True},
    }


@pytest.mark.parametrize(
    ("native", "shape", "role", "text"),
    [
        (chunk({"role": "assistant"}), "chat.completion.chunk:metadata", StreamEventRole.OPAQUE_METADATA, None),
        (chunk({"content": "answer"}), "chat.completion.chunk:content", StreamEventRole.GUARDED_TEXT, "answer"),
        (
            {"object": "chat.completion.chunk", "choices": [], "usage": {"output_tokens": 1}},
            "chat.completion.chunk:metadata",
            StreamEventRole.OPAQUE_METADATA,
            None,
        ),
        (
            {"error": {"message": "upstream failed", "type": "server_error"}},
            "error",
            StreamEventRole.PROVIDER_ERROR,
            None,
        ),
        (b"[DONE]", "[DONE]", StreamEventRole.OPAQUE_METADATA, None),
    ],
)
def test_stream_classifier_covers_the_declared_event_inventory(native, shape, role, text):
    classified = STREAM_CLASSIFIER.classify_event(event(native))

    assert (classified.shape, classified.role, classified.text) == (shape, role, text)
    assert shape in GUARDED_SHAPES | OPAQUE_SHAPES | PROVIDER_ERROR_SHAPES


def test_stream_classifier_treats_non_data_events_as_declared_opaque_shape():
    classified = STREAM_CLASSIFIER.classify_event(ServerSentEvent.from_bytes(b": keepalive\n\n"))

    assert classified.shape == "[DONE]"
    assert classified.role is StreamEventRole.OPAQUE_METADATA


@pytest.mark.parametrize(
    "native",
    [
        chunk({"reasoning_content": "unguarded"}),
        chunk({"content": "answer", "tool_calls": []}),
        chunk({"content": "answer", "future_content": "unguarded"}),
        {
            "object": "chat.completion.chunk",
            "choices": [
                {"index": 0, "delta": {"content": "first"}},
                {"index": 1, "delta": {"content": "second"}},
            ],
        },
        {"error": {"message": "failed"}, "choices": [{"index": 0, "delta": {"content": "hidden"}}]},
    ],
)
def test_stream_classifier_rejects_content_outside_the_closed_profile(native):
    with pytest.raises(UnsupportedProviderStream):
        STREAM_CLASSIFIER.classify_event(event(native))


def test_stream_classifier_accepts_reviewed_error_extensions_without_guarding_them():
    classified = STREAM_CLASSIFIER.classify_event(
        event({"error": {"message": "failed", "misalignment": {"provider": "opaque"}}})
    )

    assert classified.role is StreamEventRole.PROVIDER_ERROR


def test_stream_contract_preserves_generated_identity_and_field_inventory():
    assert CAPABILITY_PROFILE == "single_text_delta.v1"
    assert STREAM_SOURCE_SCHEMA == "CreateChatCompletionStreamResponse"
    assert STREAM_CONTRACT.projection_id == "openai.chat_completions.stream.text.v1"
    assert STREAM_CONTRACT.fields is not None
    assert STREAM_FIELDS == (
        STREAM_CONTRACT.fields.guarded_fields,
        STREAM_CONTRACT.fields.constrained_fields,
        STREAM_CONTRACT.fields.opaque_fields,
    )
    assert len(PROVIDER_REVISION) == 40
    assert len(PROVIDER_DOCUMENT_SHA256) == 64


def test_shared_request_binding_owns_the_stream_selector_and_field_inventory():
    assert STREAM_SELECTOR_FIELD == "stream"
    assert REQUEST_GUARDED_FIELDS == PAYLOAD_CONTRACT.root.guarded_fields
    assert REQUEST_CONSTRAINED_FIELDS == PAYLOAD_CONTRACT.root.constrained_fields
    assert REQUEST_OPAQUE_FIELDS == PAYLOAD_CONTRACT.root.opaque_fields


def test_stream_hooks_frame_provider_native_error_and_terminal_events():
    body = b'{"error":{"code":"failed"}}'

    assert ChatCompletionsStreamHooks().encode_error(body) == (
        b'data: {"error":{"code":"failed"}}\n\n',
        b"data: [DONE]\n\n",
    )


@pytest.mark.parametrize(
    "module",
    [
        "nemoguardrails.server.experimental.providers.openai.chat_completions.request_binding",
        "nemoguardrails.server.experimental.providers.openai.chat_completions.stream_projection",
        "nemoguardrails.server.experimental.providers.openai.chat_completions.stream_classifier",
        "nemoguardrails.server.experimental.providers.openai.chat_completions.stream_hooks",
    ],
)
def test_stream_modules_import_in_a_fresh_interpreter(module):
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
