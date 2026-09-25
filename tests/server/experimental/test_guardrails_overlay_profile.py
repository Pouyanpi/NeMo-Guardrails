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

import copy
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonpath_rfc9535 import find
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from openapi_spec_validator import validate

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = PROJECT_ROOT / "nemoguardrails/server/experimental/contracts"
FIXTURES = Path(__file__).parent / "fixtures/guardrails_overlay_profile"
EXTENSION = "x-nemo-guardrails"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _merge_update(current: object, update: object) -> object:
    if isinstance(current, dict) and isinstance(update, Mapping):
        merged = copy.deepcopy(current)
        for key, value in update.items():
            merged[key] = _merge_update(merged[key], value) if key in merged else copy.deepcopy(value)
        return merged
    return copy.deepcopy(update)


def _apply_fixture_overlay(document: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(document)
    for action in overlay["actions"]:
        nodes = find(action["target"], result)
        assert nodes
        for node in nodes:
            node.value = _merge_update(node.value, action["update"])
    return result


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


def _component_name(reference: str) -> str:
    prefix = "#/components/schemas/"
    assert reference.startswith(prefix)
    return reference.removeprefix(prefix)


def _materialized_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    provider = _load_yaml(FIXTURES / "provider.openapi.yaml")
    overlay = _load_yaml(FIXTURES / "single-text.guardrails.overlay.yaml")
    return overlay, _apply_fixture_overlay(provider, overlay)


def _profile_validator() -> Draft202012Validator:
    schema = _load_json(CONTRACTS / "schemas/guardrails-overlay-profile-v1.schema.json")
    return Draft202012Validator(schema)


def test_reference_overlay_uses_the_standard_overlay_vocabulary():
    overlay, _ = _materialized_fixture()
    schema = _load_json(CONTRACTS / "schemas/overlay-1.1-2026-04-01.json")

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(overlay)
    assert {frozenset(action) & {"update", "remove", "copy"} for action in overlay["actions"]} == {
        frozenset({"update"})
    }


def test_equivalent_rfc_9535_targets_materialize_the_same_contract():
    provider = _load_yaml(FIXTURES / "provider.openapi.yaml")
    overlay = _load_yaml(FIXTURES / "single-text.guardrails.overlay.yaml")
    equivalent = copy.deepcopy(overlay)
    replacements = {
        "$.components.schemas": '$["components"]["schemas"]',
        "$.paths['/chat'].post": '$["paths"]["/chat"]["post"]',
        "$.paths['/chat'].post.requestBody.content['application/json'].schema['$ref']": (
            '$["paths"]["/chat"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]'
        ),
        "$.paths['/chat'].post.responses['200'].content['application/json'].schema['$ref']": (
            '$["paths"]["/chat"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]'
        ),
    }
    for action in equivalent["actions"]:
        action["target"] = replacements[action["target"]]

    assert _apply_fixture_overlay(provider, equivalent) == _apply_fixture_overlay(provider, overlay)


def test_reference_overlay_materializes_valid_openapi():
    _, materialized = _materialized_fixture()

    validate(materialized)
    operation = materialized["paths"]["/chat"]["post"]
    bindings = operation[EXTENSION]["projections"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == bindings["request"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == bindings["response"]
    for reference in bindings.values():
        assert _component_name(reference) in materialized["components"]["schemas"]


def test_every_guardrails_extension_uses_the_closed_profile_vocabulary():
    overlay, _ = _materialized_fixture()
    validator = _profile_validator()
    extensions = tuple(_extensions(overlay))

    assert len(extensions) == 9
    for extension in extensions:
        validator.validate(extension)

    validator.validate(
        {
            "classification": "guarded",
            "source": "#/components/schemas/NestedProviderObject",
            "unknown_fields": "configurable",
        }
    )


@pytest.mark.parametrize(
    "extension",
    [
        {"classification": "automatic"},
        {"classification": "opaque", "unreviewed": True},
        {"classification": "guarded", "source": "ProviderRequest"},
        {"classification": "guarded", "unknown_fields": "infer"},
        {
            "classification": "guarded",
            "subject": {"kind": "text", "role": "user", "replaceable": True},
        },
        {
            "version": 1,
            "operation": "example_chat",
            "projections": {"request": "#/components/schemas/Request"},
        },
    ],
)
def test_profile_rejects_unknown_semantics_replacement_and_incomplete_bindings(extension):
    with pytest.raises(ValidationError):
        _profile_validator().validate(extension)


def test_every_projection_field_is_explicitly_classified():
    _, materialized = _materialized_fixture()
    schemas = materialized["components"]["schemas"]

    for name in ("NemoGuardrailsExampleChatRequest", "NemoGuardrailsExampleChatResponse"):
        properties = schemas[name]["properties"]
        assert properties
        assert all(EXTENSION in property_schema for property_schema in properties.values())


def test_standard_schema_keywords_own_presence_closure_and_opaque_values():
    _, materialized = _materialized_fixture()
    schemas = materialized["components"]["schemas"]

    for name in ("NemoGuardrailsExampleChatRequest", "NemoGuardrailsExampleChatResponse"):
        projection = schemas[name]
        assert projection["additionalProperties"] is True
        assert "unknown_fields" not in projection[EXTENSION]
        assert set(projection["required"]) <= set(projection["properties"])
        for field in projection["properties"].values():
            if field[EXTENSION]["classification"] == "opaque":
                assert set(field) == {EXTENSION}


def test_projection_schemas_enforce_guard_constraints_and_preserve_unknown_fields():
    _, materialized = _materialized_fixture()
    schemas = materialized["components"]["schemas"]
    request = schemas["NemoGuardrailsExampleChatRequest"]
    response = schemas["NemoGuardrailsExampleChatResponse"]
    request_validator = Draft202012Validator(request)
    response_validator = Draft202012Validator(response)

    request_validator.validate({"prompt": "hello", "model": "example", "future": {"provider": True}})
    response_validator.validate({"id": "response-1", "text": "hello", "usage": {"tokens": 1}, "future": True})
    assert not request_validator.is_valid({"prompt": "", "model": "example"})
    assert not request_validator.is_valid({"prompt": "hello", "model": "example", "stream": True})
    assert not response_validator.is_valid({"id": "response-1", "text": ""})


def test_text_subjects_disable_replacement_in_both_directions():
    overlay, _ = _materialized_fixture()
    subjects = [extension["subject"] for extension in _extensions(overlay) if "subject" in extension]

    assert {subject["role"] for subject in subjects} == {"user", "assistant"}
    assert all(subject == {"kind": "text", "role": subject["role"], "replaceable": False} for subject in subjects)
