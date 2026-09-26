# Guardrails Overlay Profile v1

Status: experimental

The Guardrails Overlay Profile defines how a provider OpenAPI description can carry a narrow, reviewable guard boundary without replacing the provider's API model. It combines three existing extension points deliberately:

| Layer | Responsibility |
| --- | --- |
| OpenAPI Overlay 1.1 | Applies ordered changes to a provider OpenAPI description. |
| OpenAPI 3.1 and JSON Schema | Describe the guarded request and response shapes. |
| `x-nemo-guardrails` | Records guard semantics that neither standard expresses. |

An Overlay is the interchange artifact. This profile does not decide whether contributors author that Overlay directly or use a compiler frontend that emits it. Both paths must produce the same profile-valid artifact.

## Standards boundary

Profile artifacts use [OpenAPI Overlay 1.1](https://spec.openapis.org/overlay/v1.1.0.html). Overlay actions add ordinary OpenAPI Schema Objects and bind them to one provider operation. Schema structure and constraints continue to use standard keywords such as `type`, `properties`, `required`, `const`, and `additionalProperties`.

`x-nemo-guardrails` must not restate schema structure. It carries only Guardrails-specific meaning:

- a vocabulary version;
- a closed capability profile;
- guarded, constrained, and opaque classifications;
- provider-neutral text subjects;
- replacement policy;
- projection direction and provider-source binding;
- unknown-field policy;
- operation-to-projection bindings.

The profile vocabulary is validated by [`guardrails-overlay-profile-v1.schema.json`](schemas/guardrails-overlay-profile-v1.schema.json). The Overlay document is independently validated against the OpenAPI Initiative's [Overlay 1.1 schema revision dated 2026-04-01](https://spec.openapis.org/overlay/1.1/schema/2026-04-01).

## Capability profile

Version 1 defines two capability profiles: `single_text.v1` for buffered payloads and `single_text_delta.v1` for event streams.

It supports one or more text subjects whose roles are `user` or `assistant`. It does not imply that provider payloads are flat or that only one provider field exists. Every provider-owned field represented at a guarded boundary must have one classification.

| Classification | Meaning |
| --- | --- |
| `guarded` | The field contains, or leads to, content inspected by Guardrails. A guarded text leaf carries a `subject`. |
| `constrained` | The projection intentionally narrows provider behavior so extraction and response handling remain unambiguous. |
| `opaque` | The field remains under provider authority and is preserved without Guardrails interpretation. |

Classification does not authorize payload rewriting. Every v1 text subject declares `replaceable: false`. A checker request to modify content remains an explicit runtime failure.

`single_text_delta.v1` carries one assistant text as ordered deltas. Every reviewed event shape is classified as a guarded delta, opaque metadata, or provider error. Provider-error events are preserved but never interpreted as generated assistant text. A guarded-delta declaration must define how missing text becomes an explicit opaque event shape. The profile does not allow output to be released before its configured inspection window passes.

## Projection declarations

A request or buffered-response projection is an ordinary OpenAPI Schema Object with a root `x-nemo-guardrails` value:

```yaml
x-nemo-guardrails:
  version: 1
  kind: payload
  profile: single_text.v1
  direction: request
  source: '#/components/schemas/ProviderRequest'
```

`source` identifies the provider schema reviewed by the projection. It is provenance and binding metadata, not a JSON Schema assertion. Tooling must not silently interpret it as `allOf`, copy provider constraints into the local projection, or treat provider validation and guard validation as equivalent.

Standard Schema Object keywords are authoritative for presence and closure:

- the object-level `required` array declares required properties;
- `additionalProperties: true`, or its omission, allows fields not interpreted
  by the projection;
- `additionalProperties: false` closes the object;
- `unknown_fields: configurable` is reserved for a guarded content boundary
  whose otherwise-open shape may be closed by trusted runtime configuration.

Legacy `unknown_fields: allow` and `unknown_fields: forbid` values may be read
only when they agree with `additionalProperties`; new profile artifacts omit
them. Extension metadata must not contradict or duplicate ordinary JSON Schema
structure.

Opaque and allowed unknown fields remain byte-for-byte provider payload concerns. The profile identifies what Guardrails may inspect; it does not authorize normalization or reserialization of the surrounding HTTP message.

## Text subjects

A guarded text leaf uses a field annotation:

```yaml
x-nemo-guardrails:
  classification: guarded
  subject:
    kind: text
    role: user
    replaceable: false
```

A guarded container may omit `subject` and lead to nested guarded leaves. A nested object boundary may identify the provider component it reviews with `source` and declare `unknown_fields: configurable` when runtime closure is intentional. It still carries an explicit classification; source binding is not a fourth classification. `subject` is valid only with the `guarded` classification. Constrained fields may record a non-empty `reason`. An opaque field cannot carry schema assertions that the generated projection would ignore; it must be reclassified as constrained if Guardrails validates its value or presence.

## Operation binding

One operation annotation indexes the projections used by the guarded endpoint:

```yaml
x-nemo-guardrails:
  version: 1
  operation: example_chat
  projections:
    request: '#/components/schemas/NemoGuardrailsExampleChatRequest'
    response: '#/components/schemas/NemoGuardrailsExampleChatResponse'
```

The binding is local to one OpenAPI operation. Overlay actions also redirect that operation's request and successful buffered-response schema references to the same components. A profile validator must reject missing, mismatched, or dangling bindings.

A streaming operation adds a `stream` binding containing an event projection and a boolean request selector. The referenced schema is an ordinary OpenAPI union whose branches carry closed stream-event declarations. Its root declares the reviewed provider event schema, explicit unknown-field policy, SSE framing, non-data event shape, and terminal sentinels. The shared request projection selects buffered or streaming response handling; stream event projection and classification remain separate. Generated-looking classifiers implement the declared event shapes, while permanent handwritten hooks own provider-native error framing.

Overlay action targets are RFC 9535 JSONPath expressions. Direct operation and
component-index bindings accept equivalent dot and bracket notation; their
meaning must not depend on one textual spelling. The later compiler remains
responsible for enforcing the complete semantic profile and rejecting ignored
schema assertions or contradictory metadata.

## Versioning

The three relevant versions remain independent:

- `overlay` selects the OpenAPI Overlay feature set;
- `openapi` selects the provider document format;
- `x-nemo-guardrails.version` selects this vocabulary.

The capability profile name is versioned separately because adding tools, images, audio, streaming events, or replacement changes guard semantics even when the extension vocabulary remains compatible.

## Reference fixture

The compact fixture under `tests/server/experimental/fixtures/guardrails_overlay_profile/` demonstrates:

- guarded request and response text;
- constrained non-streaming behavior;
- opaque provider fields;
- explicit preservation of unknown fields;
- replacement disabled in both directions;
- operation-to-projection binding.

Tests validate the Overlay against the official Overlay schema, apply its update actions to the provider fixture, validate the materialized document as OpenAPI 3.1, validate every `x-nemo-guardrails` value against the profile vocabulary, and exercise the resulting JSON Schemas.

## Non-goals

Version 1 does not define:

- an authoring frontend or compiler;
- a provider contract or source acquisition format;
- normalization overlays;
- tools, images, audio, or multimodal content;
- safe replacement;
- runtime provider integration;
- public provider-extension APIs;
- materialized provider OpenAPI publication.
