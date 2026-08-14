# gs_eval_adapters

Provider-neutral Python adapter boundary for GitSpace Evaluation IR v1.

## Trust boundary

The SDK validates canonical `EvalTaskSpec` and `AgentConfiguration` documents with the eight offline Draft 2020-12 schemas before an adapter method can run. Data crosses adapter methods only as deep-copied JSON-compatible values.

An adapter must preserve the exact canonical request inside its prepared payload:

```text
canonical GitSpace request
→ prepare { canonical_request, framework_request, extensions }
→ semantic equality gate
→ invoke
→ collect
→ normalized AdapterResult
```

A changed or missing canonical snapshot stops execution before external invocation. Concrete framework mappings require their own qualification evidence.

## JSON boundary

Accepted values are null, booleans, Unicode scalar strings, interoperable safe integers, finite non-negative-zero floats, lists and string-keyed objects. Custom classes, builtin subclasses, tuples, sets, bytes, non-finite numbers, cycles and excessive nesting are rejected.

Extensions use namespaced keys. Artifacts are strict `cas://sha256/...` references. Metrics are finite non-bool numbers. No external framework object can be returned as canonical data.

## Outcomes

```text
pass | fail | timeout | policy | infra
```

`AdapterTimeout` and `AdapterPolicyViolation` normalize to their dedicated statuses. Unexpected external exceptions normalize to bounded single-line `infra` results. Input/schema errors, semantic loss and contract violations remain explicit SDK failures and are not misclassified as agent failure.

## Qualified Inspect adapter

Task 11 qualifies one deliberately narrow Inspect AI path:

```yaml
inspect_ai: 0.3.258
source_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
model: mockllm/model
tasks: 1
samples: 1
epochs: 1
solver: generate
scorer: match
scorer_options:
  location: exact
  ignore_case: true
  numeric: false
network: forbidden
```

`InspectAdapter` constructs the pinned in-memory Task, runs the local mock model, serializes the complete `EvalLog` to canonical JSON bytes, publishes content-matching CAS URIs, derives a bounded `InspectReplayRecord`, and returns only Task 10 JSON primitives.

`inspect_replay.py` imports no Inspect code. It can project the complete JSON log, validate the bounded record and reproduce the exact-match score with all `inspect_ai` imports blocked.

The Inspect score remains an observation. Collection fails closed if independent replay disagrees.

### Inspect 0.3.258 lifecycle shim

The pinned release drains its sample-event receiver but drops the reference without closing the AnyIO receive stream. The adapter applies a serialized temporary compatibility shim only during `inspect_eval`:

```text
close sender
→ wait for emitter
→ drain remaining events
→ close receiver
→ clear active references
→ restore original Inspect function
```

The distribution is not modified. The shim is tied to the exact release, source commit and wheel hash and must be removed or requalified for every future release. Direct concurrent Inspect runs outside the adapter lock are outside this qualification.

## Verification

```bash
uv lock --check --python 3.12.13
uv sync --frozen
PYTHONPATH=python:tests/adapters/inspect uv run --frozen \
  python -m unittest discover -s tests/adapters/inspect -p 'test_*.py' -v
PYTHONPATH=python:tests/adapters/inspect uv run --frozen \
  python tests/adapters/inspect/run_mutations.py
PYTHONPATH=python:tests/adapters uv run --frozen \
  python -m unittest discover -s tests/adapters -p 'test_*.py' -v
```

The final CI also replays the tests from `git archive HEAD`, revalidates the Python toolchain and sovereign schemas, then executes the complete locked Rust workspace, Clippy and rustfmt.

## Non-goals

The current qualification does not cover external model providers, network access, tools, agents, approval policies, sandboxes, multi-sample runs, model-graded scoring, other Inspect releases or arbitrary direct Inspect concurrency.
