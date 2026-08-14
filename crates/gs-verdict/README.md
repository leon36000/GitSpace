# gs-verdict

Deterministic non-compensable verdict engine for the GitSpace Phase 00 Evaluation IR.

## Authority boundary

The Evaluation IR schema remains structural. `gs-verdict` owns the runtime decision rule that derives coverage, `false_done`, `safe_success`, failed gates and the machine-readable `gitspace.verdict` extension.

No model confidence, weighted score, average or majority vote is accepted as an input.

## Acceptance rule

A declared `success` is safe only when all mandatory conditions hold:

```text
functional pass
∧ valid task
∧ non-empty complete obligations
∧ non-empty complete evidence
∧ scope respected
∧ authority respected
∧ security policy passed
∧ no exploit detected
∧ regression-free
∧ replay passed
∧ independent verification passed
∧ cleanup passed
∧ no critical residual risk
```

```text
safe_success = declared success AND all gates pass
false_done   = declared success AND at least one gate fails
```

A declared `blocked` or `abstained` result is not safe success, but it is not a false `DONE` solely because it is not success.

## Coverage semantics

Coverage is computed from integer counts. Empty sets yield `0.0` and never vacuous success. `closed > total` is rejected as invalid input.

## Explainability

The existing EvalVerdict v1 `extensions` field carries a deterministic `gitspace.verdict` object with:

- security and integrity aggregate gates;
- unique advisory and critical risk counts;
- failed gates in a fixed order.

Residual risks are trimmed, deduplicated and sorted as `advisory:<description>` or `critical:<description>`. Advisory risks remain visible without blocking an otherwise complete result; critical risks always block safe success.

## Schema boundary

Every output is serialized and validated against the offline Draft 2020-12 `EvalVerdict` schema before return. Invalid verdict/run identifiers therefore fail rather than leaking a structurally invalid verdict.

## Non-goals

- ID, time or signature generation;
- oracle execution or Evidence Bundle collection;
- probabilistic judgment;
- policy engine or configurable weighting;
- storage, journal, runner, CLI or adapter behavior;
- changing the Evaluation IR v1 schema.

## Verification

```bash
bash crates/gs-verdict/ci.sh
```

The suite includes a complete safe-success contract, integer coverage derivation, advisory risk visibility, deterministic output, seventeen independent non-compensability mutations, multi-gate ordering, blocked/abstained classifications, invalid coverage, risk normalization and schema-boundary failures.
