# Development

Guardrails Proxy is the `guardrails-proxy` distribution and `guardrails_proxy`
Python package. It depends on the NVIDIA NeMo Guardrails library. Installing the
library alone does not install the proxy, and the library's existing API server
remains separate. The proxy has its own `guardrails-proxy` command and equivalent
`python -m guardrails_proxy` entry point.

Start with the [architecture overview](docs/architecture.mdx), then follow
[framework internals](docs/architecture-internals.mdx) for dependency boundaries,
request-local state, and implementation/test locations. The
[request lifecycle](docs/architecture-requests.mdx) explains execution and cleanup.

## Set up the workspace

From the repository root:

```bash
uv sync --locked --all-packages --group dev
cd guardrails-server
uv run --locked guardrails-proxy --help
uv run --locked guardrails-proxy validate src/guardrails_proxy/examples/basic/proxy.yaml
```

Running inside `guardrails-server` selects the proxy workspace package without
`--package`. For your own deployment, use
`uv run --locked guardrails-proxy serve /path/to/proxy.yaml` from that directory.
Installed users can activate their environment and use `guardrails-proxy`
directly; see the [quickstart](docs/quickstart.mdx).

Both projects have independent package metadata and distributions, with a shared
uv workspace lockfile for development. The workspace selects the local library
checkout. Wheel metadata contains a versioned `nemoguardrails` dependency, not a
filesystem path.

The current proxy requires `nemoguardrails>=0.25.0.dev0,<0.26`. Until a compatible
library release is available, use the workspace or install the library and proxy
wheels built from the same checkout. This bound identifies the integration
surface under test; it is not a completed release compatibility matrix.

## Build and install local distributions

From the repository root:

```bash
uv build --all-packages
```

Install both built wheels into your chosen environment. For example, from the
repository root with that environment active:

```bash
uv pip install dist/nemoguardrails-*.whl dist/guardrails_proxy-*.whl
```

After installation, invoke `guardrails-proxy` directly. A repository checkout is
not required to run the installed package. To copy its complete bundled example
into a deployment-owned directory, run this Python snippet in that environment:

```python
from importlib.resources import files
from shutil import copytree

copytree(files("guardrails_proxy") / "examples/basic", "proxy-example")
```

Keep the manifest and its sibling Rails directory together. Edit the copied
manifest to select your upstream and dialect, then run:

```bash
guardrails-proxy validate proxy-example/proxy.yaml
guardrails-proxy inspect proxy-example/proxy.yaml
guardrails-proxy serve proxy-example/proxy.yaml
```

The console entry point uses the same manifest parser, application factory, and
lifespan as Python assembly. It adds no second ownership or configuration layer.

## Run checks

From the repository root, after installing development dependencies:

```bash
make test WORKERS=0 TEST=guardrails-server/tests/proxy_tests
make test WORKERS=0 TEST=guardrails-server/tests/recorded ARGS="--block-network --record-mode=none"
make test-proxy-package
```

Packaging checks build both distributions offline and install local wheels with
locked runtime dependencies in a fresh environment. The dependency cache must
first be populated by the workspace sync. Installed-console tests exercise
CLI/module parity, bundled resources, and localhost buffered, streaming,
blocking, and disconnect behavior.

Repository cassette targets include library and proxy recordings by default;
set `RECORDED_TESTS` to narrow them. Coverage includes both Python packages.
Recorded tests reuse repository-owned sanitization helpers as development tools,
not proxy runtime dependencies. Unit and replay tests must not call live providers.

Ruff, pre-commit, license insertion, and type checking use the repository's shared
configuration. Run the standard repository pre-commit checks on changed files.
The proxy does not maintain a parallel lint configuration.

## Package and release ownership

The proxy owns its examples, schemas, contracts, and technical reference assets.
Its wheel excludes the library source, tests, and recordings. The library wheel
does not embed or depend on the proxy. The library's `server` extra is not used
to supply proxy dependencies; the proxy declares its HTTP, CLI, YAML, and schema
dependencies directly.

CI installs both workspace packages explicitly. Ordinary test matrices exclude
the packaging directory; separate serial acceptance jobs run offline build,
installation, and localhost checks in GitHub Actions and GitLab. Local
`make test` still includes packaging tests in its full-suite selection.

The proxy is not published to PyPI. Library release builds select `nemoguardrails`
and use `dist/nemoguardrails/`; publication checks reject unexpected files or
versions. Proxy acceptance builds use temporary directories and do not feed
the publishing workflows. Building locally does not publish either package.

The existing library Dockerfile copies the workspace member's metadata for
dependency resolution but installs and starts only the library's existing
server. There is no dedicated proxy image in this packaging change.

## Compatibility and lifecycle validation

The library boundary uses `Guardrails`, `RailsConfig`, and
`nemoguardrails.rails.llm.options` result/status types. The adapter invokes
startup, check, and shutdown APIs and reads Rails configuration to select
supported checks. Compatibility of these types and lifecycle semantics remains
part of release validation.

The moved suite includes a real-core queue-cleanup retry regression. Packaging
does not fix the underlying interrupted-cleanup prerequisites. Successful
installation, healthy shutdown, or socket tests do not establish that every
interrupted cleanup path is complete. Keep those regressions visible and report
their outcomes when validating a release.
