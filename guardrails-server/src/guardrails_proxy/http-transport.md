# Outbound HTTP transport reference

Use the [Python transport guide](../../docs/python-integration.mdx#customize-outbound-http)
for a working application example. The `http_transport_factory` argument on
`guardrails_proxy.application.create_proxy_application` supplies application-owned
HTTPX dispatch behavior without changing provider field policy or Rails checks.

## Position in the request flow

| Component | Responsibility |
| --- | --- |
| `ProviderIntegration` | Declares endpoints, errors, upstream settings, and provider control headers. |
| `UpstreamSettings` | Defines the instance's local mount and initial base URL. |
| `ProviderTransport` | Builds outbound requests, applies guarded representation/buffer rules, and hands off responses. |
| Pass-through router | Adapts unrelated operations to ASGI forwarding and response ownership. |
| HTTPX transport | Performs or replaces the final outbound HTTP exchange. |

For checked operations, the custom transport is reached after input inspection;
its returned content goes through output inspection when enabled. Unrelated
operations use pass-through forwarding. The hook is outbound HTTP dispatch,
not inbound FastAPI middleware or a Rails resolver API.

The shared client strips hop-by-hop and declared control headers. Ordinary
upstream authorization and API-version headers follow provider forwarding rules.
Only output-inspected guarded operations ask for identity encoding. Other
responses retain the caller's representation preference.

## Relationship to `UpstreamSettings`

The instance's `base_url` supplies the initial HTTP URL. A custom transport may
forward that request unchanged, dispatch to trusted destinations, or return a
synthetic response. An external gateway can instead serve as the fixed base URL,
with no custom transport required. See [deployment topologies](../../docs/deployment.mdx).

The hook is application-wide. If several provider instances share it, route by
trusted logical host/path or explicitly supplied metadata. It does not choose
new provider bindings after input inspection. Changing destinations must retain
compatibility with the selected endpoint/dialect.

For body-aware routing, bound JSON reads used for selection and preserve non-JSON
upload streaming. Replace the logical base prefix deliberately and retain encoded
suffix/query bytes. Apply destination-owned credentials; do not forward one
origin's caller secrets to another. Synthetic responses must supply unread async
bodies compatible with raw HTTPX response iteration.

## Other uses

The extension supports application implementations of egress/TLS configuration,
model aliases, trusted routing, recording, metrics, replay, and fault injection.
It does not supply built-in balancing, failover, quotas, or safe inference retries.

Use a fixed upstream setting for one URL, inbound middleware for authentication,
and provider declarations for content semantics. Keep those decisions independent.
`httpx.MockTransport` is useful for deterministic HTTP fixtures;
`httpx.ASGITransport` is useful for in-process wiring but buffers responses and
does not establish incremental socket delivery.

## Constraints and ownership

The factory is invoked once per application lifespan and must return a new
`httpx.AsyncBaseTransport`. Without it, HTTPX uses its normal network transport.
The runtime owns the resulting shared client and transport. A transport owns
any network transport it creates and must implement streaming and cooperative,
repeatable close behavior.

The pool does not persist upstream cookies or inherit caller-independent client
headers/authentication. Explicit caller Cookie and upstream Set-Cookie headers
remain part of the exchange. Credential injection belongs to explicit application
transport policy rather than shared client defaults.

Dispatch owns acquired response resources until handoff. The returned response
owns cleanup afterward, including failure before iteration. Bare async-generator
bodies need an independent owner close callback; an appropriate self-owning
iterator can expose `aclose()` directly. Exhaustion alone does not prove the
underlying connection closed.

Cooperative response cleanup, application HTTP shutdown, and failed-startup
rollback use bounded, shielded attempts. Ordinary close errors are logged without
replacing the primary outcome. Retries must be tolerated; timeouts cannot prove
release of uncooperative owners. Read/idle timeouts are separate policy.

Guarded request and response limits do not impose universal bounds on unrelated
pass-through uploads or downloads. Preserve that distinction when adding an
application transport. Consult the [streaming guide](../../docs/providers-and-streaming.mdx)
for inspected-window limits and the
[development notes](../../DEVELOPMENT.md#compatibility-and-lifecycle-validation)
for outstanding lifecycle validation.
