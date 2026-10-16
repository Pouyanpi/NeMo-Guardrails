# Guardrails Proxy

Guardrails for the model APIs you already use.

Put the NVIDIA NeMo Guardrails library between your clients and your inference
services. Check requests before they reach a model and check responses before
they reach your users, including streaming output.

Your clients keep the provider's API format. Your model service keeps generating
the response. The proxy extracts the content your checks need and relays accepted
JSON bodies and server-sent events without rebuilding them.

```text
Client ── request ──→ Input checks ──→ Model service
       ←─ response ─ Output checks ←─┘
```

## What it gives you

- **Guardrails at the HTTP boundary.** Apply configured input and output checks
  across applications, without putting guardrail execution into each client.
- **Provider-aware streaming.** Check text as it arrives while preserving the
  provider's event format, metadata, and completion behavior on accepted paths.
- **A reviewable inspection boundary.** Typed provider bindings declare what is
  checked, constrained, or passed through. Export their guard contracts to
  review that coverage without reading the implementation.
- **Independent routing and policy.** Connect upstreams and gateways, mount
  multiple provider instances, and select Rails by instance or trusted request
  context. Add application-owned HTTP routing when you need it.
- **A server and a Python interface.** Start from a YAML manifest or compose the
  same application in Python with custom integrations and transports.

Built-in integrations include OpenAI Chat Completions and Responses, with explicit
LiteLLM dialects. [Provider bindings](docs/providers-and-streaming.mdx) make their
current content coverage explicit as integrations and capabilities evolve.

## Try it

With the package installed and its environment active, run these commands from
your deployment directory:

```bash
guardrails-proxy validate proxy.yaml
guardrails-proxy inspect proxy.yaml
guardrails-proxy serve proxy.yaml
```

The [quickstart](docs/quickstart.mdx) covers installation from this checkout and
copying the bundled example into your own directory. Keep `proxy.yaml` and its
sibling Rails directory together. Set `base_url` to your upstream's API base,
including its path prefix; select `dialect: litellm` if you need that reviewed
dialect. The example enables Chat Completions and Responses with local regex
rails that block email-address patterns in input and output.

Send a request from another terminal, using your upstream's model ID. Include an
`Authorization` header if the upstream requires it:

```bash
curl -sS http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $PROVIDER_API_KEY" \
  -d '{"model":"YOUR_DEPLOYED_MODEL","messages":[{"role":"user","content":"Hello!"}]}'
```

Change the user text to `Contact person@example.com` to see an input blocked
before inference. Add `"stream": true` and use `curl -N` for a streamed response.
Follow the [quickstart](docs/quickstart.mdx) for complete setup and examples.

## Explore

| You want to… | Read |
| --- | --- |
| Run the proxy and see a guardrail execute | [Quickstart](docs/quickstart.mdx) |
| Choose upstreams, operations, and Rails configurations | [Configuration](docs/configuration.mdx) |
| Check provider coverage and understand streaming | [Providers and streaming](docs/providers-and-streaming.mdx) |
| Understand what is inspected and review an export | [Guard contracts](docs/guard-contracts.mdx) |
| Use multiple upstreams, replicas, or gateways | [Deployment](docs/deployment.mdx) |
| Embed the application or extend its bindings and transport | [Python integration](docs/python-integration.mdx) |

Inspection applies to the content declared by a binding and the checks enabled
in its Rails configuration. Other operations may pass through without content
inspection. Streaming checks cannot retract text already sent. See the guides
for the current bindings' coverage and deployment behavior.

## Project status

Guardrails Proxy is experimental (`0.1.0a1`) and is not yet published to PyPI.
It depends on the NVIDIA NeMo Guardrails library. Its launcher listens on
loopback by default; provide inbound authentication before exposing a service.

See [Development](DEVELOPMENT.md) to build, test, or contribute.
Licensed under [Apache 2.0](LICENSE-Apache-2.0.txt).
