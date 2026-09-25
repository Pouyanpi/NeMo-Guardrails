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
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = PROJECT_ROOT / "nemoguardrails/server/experimental/contracts"
OPENAI = CONTRACTS / "openai"
EXTENSION = "x-nemo-guardrails"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _extensions(value: object) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        extension = value.get(EXTENSION)
        if extension is not None:
            assert isinstance(extension, dict)
            yield extension
        for key, child in value.items():
            if key != EXTENSION:
                yield from _extensions(child)
    elif isinstance(value, list):
        for child in value:
            yield from _extensions(child)


def _projection_schemas(overlay: dict[str, Any]) -> dict[str, Any]:
    action = next(action for action in overlay["actions"] if action["target"] == "$.components.schemas")
    return action["update"]


def test_openai_source_is_immutable_and_content_addressed():
    source = _load_yaml(OPENAI / "source.yaml")

    assert set(source) == {"document_url", "download_url", "revision", "document_version", "sha256"}
    assert re.fullmatch(r"[0-9a-f]{40}", source["revision"])
    assert re.fullmatch(r"[0-9a-f]{64}", source["sha256"])
    assert source["revision"] in source["document_url"]
    assert source["revision"] in source["download_url"]
    assert urlparse(source["document_url"]).scheme == "https"
    assert urlparse(source["download_url"]).scheme == "https"


def test_chat_contract_is_valid_overlay_with_closed_guardrails_semantics():
    overlay = _load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml")
    overlay_schema = _load_json(CONTRACTS / "schemas/overlay-1.1-2026-04-01.json")
    profile_schema = _load_json(CONTRACTS / "schemas/guardrails-overlay-profile-v1.schema.json")

    Draft202012Validator(overlay_schema, format_checker=FormatChecker()).validate(overlay)
    profile_validator = Draft202012Validator(profile_schema)
    extensions = tuple(_extensions(overlay))
    assert extensions
    for extension in extensions:
        profile_validator.validate(extension)

    classifications = {extension["classification"] for extension in extensions if "classification" in extension}
    assert classifications == {"guarded", "constrained", "opaque"}
    subjects = [extension["subject"] for extension in extensions if "subject" in extension]
    assert {subject["role"] for subject in subjects} == {"user", "assistant"}
    assert all(subject["replaceable"] is False for subject in subjects)


def test_chat_contract_binds_buffered_and_streamed_projections():
    overlay = _load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml")
    schemas = _projection_schemas(overlay)
    operation = next(action for action in overlay["actions"] if action["target"] == "$.paths['/chat/completions'].post")
    declaration = operation["update"][EXTENSION]

    assert set(schemas) == {
        "NemoGuardrailsChatCompletionsRequest",
        "NemoGuardrailsChatCompletionsResponse",
        "NemoGuardrailsChatCompletionsStream",
    }
    assert declaration["projections"] == {
        "request": "#/components/schemas/NemoGuardrailsChatCompletionsRequest",
        "response": "#/components/schemas/NemoGuardrailsChatCompletionsResponse",
        "stream": {
            "projection": "#/components/schemas/NemoGuardrailsChatCompletionsStream",
            "selector": {"field": "stream", "value": True},
        },
    }
    assert len(overlay["actions"]) == 5
    assert any("text/event-stream" in action["target"] for action in overlay["actions"])
    assert schemas["NemoGuardrailsChatCompletionsRequest"]["properties"]["stream"] == {
        "type": "boolean",
        "default": False,
        EXTENSION: {
            "classification": "constrained",
            "reason": "The operation selects buffered or streamed response handling from this field.",
        },
    }


def test_chat_request_contract_accounts_for_the_pinned_provider_fields():
    overlay = _load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml")
    request = _projection_schemas(overlay)["NemoGuardrailsChatCompletionsRequest"]
    expected = {
        "audio",
        "frequency_penalty",
        "function_call",
        "functions",
        "logit_bias",
        "logprobs",
        "max_completion_tokens",
        "max_tokens",
        "messages",
        "metadata",
        "modalities",
        "model",
        "moderation",
        "n",
        "parallel_tool_calls",
        "prediction",
        "presence_penalty",
        "prompt_cache_key",
        "prompt_cache_options",
        "prompt_cache_retention",
        "reasoning_effort",
        "response_format",
        "safety_identifier",
        "seed",
        "service_tier",
        "stop",
        "store",
        "stream",
        "stream_options",
        "temperature",
        "tool_choice",
        "tools",
        "top_logprobs",
        "top_p",
        "user",
        "verbosity",
        "web_search_options",
    }

    assert set(request["properties"]) == expected
    assert all(EXTENSION in field for field in request["properties"].values())
    message = request["properties"]["messages"]
    assert message["minItems"] == message["maxItems"] == 1
    assert message["items"]["properties"]["role"]["const"] == "user"
    assert message["items"][EXTENSION]["unknown_fields"] == "configurable"
    assert message["items"]["properties"]["content"][EXTENSION]["subject"]["role"] == "user"
    assert "unknown_fields" not in request[EXTENSION]


def test_chat_response_contract_is_one_guarded_assistant_message():
    overlay = _load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml")
    response = _projection_schemas(overlay)["NemoGuardrailsChatCompletionsResponse"]

    assert set(response["properties"]) == {
        "choices",
        "created",
        "id",
        "metadata",
        "model",
        "moderation",
        "object",
        "service_tier",
        "system_fingerprint",
        "usage",
    }
    assert all(EXTENSION in field for field in response["properties"].values())
    choices = response["properties"]["choices"]
    assert choices["minItems"] == choices["maxItems"] == 1
    assert choices["items"]["properties"]["logprobs"]["type"] == "null"
    message = choices["items"]["properties"]["message"]
    assert message["properties"]["annotations"]["type"] == "array"
    assert message["properties"]["role"]["const"] == "assistant"
    assert message["properties"]["content"][EXTENSION]["subject"] == {
        "kind": "text",
        "role": "assistant",
        "replaceable": False,
    }
    assert message[EXTENSION]["unknown_fields"] == "configurable"
    assert "unknown_fields" not in response[EXTENSION]


def test_projection_components_are_valid_json_schemas():
    overlay = _load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml")

    for schema in _projection_schemas(overlay).values():
        Draft202012Validator.check_schema(schema)


def test_chat_stream_contract_closes_content_shapes_and_declares_event_inventory():
    stream = _projection_schemas(_load_yaml(OPENAI / "chat-completions.guardrails.overlay.yaml"))[
        "NemoGuardrailsChatCompletionsStream"
    ]
    chunk, error = stream["oneOf"]
    delta = chunk["properties"]["choices"]["items"]["properties"]["delta"]

    assert delta["additionalProperties"] is False
    assert delta["properties"]["content"][EXTENSION]["subject"] == {
        "kind": "text",
        "role": "assistant",
        "replaceable": False,
    }
    assert chunk[EXTENSION]["event"] == {
        "classification": "guarded_delta",
        "shape": "chat.completion.chunk:content",
        "match": {"object": "chat.completion.chunk"},
        "required_fields": [],
        "missing_text": {
            "classification": "opaque_metadata",
            "shape": "chat.completion.chunk:metadata",
        },
    }
    assert error[EXTENSION]["event"]["classification"] == "provider_error"
    assert stream[EXTENSION]["transport"] == {
        "format": "sse",
        "non_data_shape": "[DONE]",
        "sentinels": {"[DONE]": "[DONE]"},
    }
