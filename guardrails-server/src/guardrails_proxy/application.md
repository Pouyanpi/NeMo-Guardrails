# Proxy application reference

For a runnable first deployment, use the
[quickstart](../../docs/quickstart.mdx). The
[configuration guide](../../docs/configuration.mdx) and
[Python integration guide](../../docs/python-integration.mdx) are the primary
usage guides. This page records application assembly semantics.

## Run from YAML

The installed `guardrails-proxy` command and `python -m guardrails_proxy` enter
the same CLI. The commands are `validate`, `inspect`, `schema`, and `serve`.
They use the existing manifest parser and application factory.

`validate` checks data, configuration-directory availability, URL rules, and
routing without loading Rails code or contacting providers. `inspect` describes
bound operations, profiles, fixed Rails IDs, and limits, not enabled checks or
checker compatibility. `schema` derives the manifest's editor schema. `serve`
enters application lifespan and loads Rails before accepting requests.

YAML requires `version: 1` and fixed `rails_config_id` selections. Relative paths
resolve against the manifest target's directory. It does not expand environment
variables or import callbacks. See [manifest rules](../../docs/configuration.mdx#manifest-validation-rules).

### Requests and blocking

Input checks run before upstream dispatch. Buffered output checks run before
returning the selected response text. Streaming output checks run over windows
before approved event bytes are released. Earlier windows cannot be retracted.

The [bundled example](examples/basic/proxy.yaml) uses local regex checks for
email-address patterns and needs a separately running upstream. Its
[streaming settings](../../docs/providers-and-streaming.mdx#streaming-windows)
count nonempty provider text deltas, not tokens. See the
[quickstart requests](../../docs/quickstart.mdx#send-a-buffered-request) and
[blocking example](../../docs/quickstart.mdx#see-input-blocking).

## Declare a built-in provider

Import `ConfigEntry`, `ProviderConfig`, `ProxyConfig`, and
`create_proxy_application` from `guardrails_proxy.application`.

`create_proxy_application(config)` accepts a `ProxyConfig` with providers and a
Rails catalog. Construction validates paths and routes. Startup owns the HTTP
client and initializes the catalog; requests use ready checkers.

Python relative paths resolve against the application's construction working
directory. Use absolute paths when its launch directory is not fixed.

### Operations and dialects

The built-in provider is `openai`. Select `chat_completions`, `responses`, or
both in a nonempty ordered list/tuple; duplicate and unknown names are rejected.
Omit the dialect for native bindings, or explicitly select `litellm`.

A URL or model name does not select a dialect. Current content coverage belongs
to the selected binding and its capability profiles, which can evolve; consult
[providers and streaming](../../docs/providers-and-streaming.mdx) for the shipped
bindings. An operation selection does not install a route allowlist or enable
checks disabled in Rails. Unselected operations may pass through.

## Fixed and dynamic Rails configuration

`rails_config_id` selects a registered ID per provider and bypasses user resolver
code. A provider without a fixed ID in `ProxyConfig` requires a trusted resolver,
even when the catalog contains only one entry. All-fixed declarations need no
callback.

`config_resolver` accepts the original request, provider type, instance ID, and
canonical operation name through `ConfigContext`. It may return a string directly
or through an awaitable. Unknown/invalid results and callback failures stop the
request before upstream dispatch. Selection returns one configuration, not a
sequence. Authorization belongs to the trusted callback.

Every catalog entry initializes before readiness. No request-time parsing,
hot-reload mechanism, or dynamic catalog is added by resolution. See the
[resolution reference](configuration-resolution.md) for lifecycle and trust rules.

## Custom Python composition

The same factory accepts explicit `ProviderIntegration` objects through
`providers=...`, Rails entries, a resolver, and an HTTP transport factory.
This supports custom endpoints and mixed reviewed declarations without a global
provider registry.

In direct mode, one Rails entry and no resolver infers a static selection;
multiple entries require a resolver. An explicit resolver is invoked even with
one entry. These direct-mode rules differ from `ProxyConfig`'s explicit per-provider
fixed/dynamic selection.

Do not combine `ProxyConfig` with direct provider/catalog/limit/prefix arguments.
The Python callbacks `config_resolver` and `http_transport_factory` remain separate
keyword arguments in either mode. See
[Python composition](../../docs/python-integration.mdx) and
[transport ownership](http-transport.md).

## Validation, defaults, and limitations

Configuration models reject unknown fields, snapshot input collections, and are
frozen. Instance IDs and mounts must be unique. Bound routes and operation IDs
are validated for conflicts. Upstream URLs are explicit HTTP(S), without
userinfo, query, or fragment; declarative configuration does not use provider
URL environment defaults.

The default application prefix is empty, guarded request limit is 1 MiB,
inspected response limit is 10 MiB, and outbound timeout is 30 seconds.
These bounds do not become global limits for unrelated pass-through traffic.

The proxy declares its own HTTP, CLI, YAML, and schema dependencies. The
library's `server` extra and provider client SDKs are not required for HTTP
forwarding. Individual Rails integrations may have additional dependencies.

Startup and cleanup reuse the runtime's owners and cooperative budgets. The
independent interrupted-cleanup regressions still require real-resource release
validation; healthy launch or disconnect tests alone do not establish readiness
for every cancellation path. See [development validation](../../DEVELOPMENT.md#compatibility-and-lifecycle-validation).
