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

A changed or missing canonical snapshot stops execution before external invocation. Concrete framework mappings must add their own qualification evidence; this SDK does not certify Inspect, Harbor, SWE-bench, AgentDojo or any provider.

## JSON boundary

Accepted values are null, booleans, strings, interoperable safe integers, finite floats, lists and string-keyed objects. Custom classes, tuples, sets, bytes, non-finite numbers, cycles and excessive nesting are rejected.

Extensions use namespaced keys. Artifacts are strict `cas://sha256/...` references. Metrics are finite non-bool numbers. No external framework object can be returned as canonical data.

## Outcomes

```text
pass | fail | timeout | policy | infra
```

`AdapterTimeout` and `AdapterPolicyViolation` normalize to their dedicated statuses. Unexpected external exceptions normalize to bounded single-line `infra` results. Input/schema errors, semantic loss and contract violations remain explicit SDK failures and are not misclassified as agent failure.

## Verification

```bash
PYTHONPATH=python uv run --frozen python -m unittest discover -s tests/adapters -p 'test_*.py' -v
PYTHONPATH=python uv run --frozen python -m compileall -q python/gs_eval_adapters tests/adapters
```

The final CI also replays the existing Python schema/toolchain contracts and the complete locked Rust workspace.
