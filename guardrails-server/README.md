# Guardrails Proxy

A separately packaged transparent HTTP proxy. The distribution is
`guardrails-proxy`; its Python package is `guardrails_proxy`. The server depends
on `nemoguardrails`, not the reverse. The library's existing server is unchanged.
Version `0.1.0a1` is a pre-release, not a stability promise.

## Development and installation

From the repository root:

```bash
uv sync --locked --all-packages --group dev
uv run --locked --package guardrails-proxy guardrails-proxy --help
uv build --all-packages
```

Both projects have independent package metadata and distributions, with a shared
uv workspace lockfile for development. The workspace source selects the local
library checkout; wheel metadata contains a normal versioned `nemoguardrails`
dependency, not a filesystem path. Installing the library alone does not install
or package this proxy. No `nemoguardrails proxy` subcommand is added.

This checkpoint requires the `0.25` library development line. Before that library
release is available, install the library wheel built from this checkout together
with the proxy wheel, rather than resolving an older published release. The
version bound reflects the tested integration surface, not a completed release
compatibility matrix. No package publication is performed by these commands.

## Run an example

The server owns its examples, schemas, contracts and documentation. See the
[application guide](src/guardrails_proxy/application.md) for a trusted manifest,
provider/dialect selection, credentials, supported modes and buffering limits.
The basic example uses local regex checks with no additional rail-model service;
generation still needs a compatible upstream. Native OpenAI and LiteLLM bindings
are explicit selections, not inferred from URLs.

```bash
uv run --locked --package guardrails-proxy guardrails-proxy validate guardrails-server/src/guardrails_proxy/examples/basic/proxy.yaml
uv run --locked --package guardrails-proxy guardrails-proxy serve guardrails-server/src/guardrails_proxy/examples/basic/proxy.yaml
```

The example's upstream is a placeholder at `http://127.0.0.1:9000/v1`. Copy the
manifest and its sibling Rails directory together before editing your deployment.
The default listener is loopback port 8000. The launcher does not supply inbound
authentication; do not expose it publicly without deployment-owned access controls.

After installing the wheels in your own environment, use `guardrails-proxy`
directly. `python -m guardrails_proxy` is an equivalent entry point. Neither
requires the repository checkout. Bundled examples are package resources; copy
the complete basic example into a new deployment-owned directory:

```bash
uv run --no-project python -c "from importlib.resources import files; from shutil import copytree; copytree(files('guardrails_proxy') / 'examples/basic', 'proxy-example')"
guardrails-proxy validate proxy-example/proxy.yaml
guardrails-proxy inspect proxy-example/proxy.yaml
guardrails-proxy serve proxy-example/proxy.yaml
```

Activate the environment containing the installed wheels before these commands.
Edit `proxy-example/proxy.yaml` to select your upstream and dialect. The launcher
uses the same factory, trusted manifest parser and lifespan as Python assembly;
the console entry point adds no separate configuration or ownership layer.

## Tests and dependency boundaries

```bash
make test WORKERS=0 TEST=guardrails-server/tests/proxy_tests
make test WORKERS=0 TEST=guardrails-server/tests/recorded ARGS="--block-network --record-mode=none"
make test WORKERS=0 TEST=guardrails-server/tests/packaging ARGS="--block-network --allowed-hosts=127.0.0.1"
```

Packaging tests build both distributions offline and install local wheels with
locked runtime dependencies in a fresh environment. Run `uv sync --locked
--all-packages --group dev` first to populate the dependency cache. Tests check
CLI/module parity and reuse the localhost buffered, streaming, blocking and
disconnect cases against the installed console script and packaged Rails example.
Repository cassette targets include both library and proxy recordings by default;
set `RECORDED_TESTS` to narrow them. Coverage includes both Python packages.
The existing library Dockerfile copies the member's metadata for workspace
resolution but still installs and starts only the legacy library server. This
change does not introduce a proxy image.

Recorded tests reuse repository-owned sanitization helpers; those are development
tools, not server runtime dependencies. Recordings are moved unchanged. Tests
must not call live providers. The full moved suite still exposes the pre-existing
core queue-cleanup retry failure; packaging does not resolve lifecycle prerequisites.

The runtime library boundary currently uses `Guardrails`, `RailsConfig`, and
`nemoguardrails.rails.llm.options` result/status types. It invokes the existing
startup/check/shutdown API and reads Rails configuration for adapter selection.
No private library import or shim is added by this move, but compatibility of
these result types and lifecycle semantics remains part of release validation.
The library's server extra is not used to supply this project's dependencies:
the proxy declares its own HTTP, CLI, YAML and schema dependencies directly.
