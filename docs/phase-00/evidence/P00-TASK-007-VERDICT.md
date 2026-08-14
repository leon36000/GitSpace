---
evidence_id: P00-TASK-007-VERDICT
status: PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE
recorded_at: 2026-08-14
base_commit: f04aaacd18914c221bdbe63d9c71a371c9a4cfda
implementation_pr: 26
red_pr: 25
---
# P00-TASK-007 — Verification verdict

## Result under review

Task 7 adds a deterministic non-compensable verdict engine over the existing EvalVerdict v1 contract. It derives coverage from integer counts, calculates `safe_success` and `false_done`, exposes fixed-order failed gates, normalizes residual risks and validates every emitted verdict against the offline Draft 2020-12 schema.

## TDD evidence

### RED

- branch: `agent/p00-task-007-red-v1`;
- closed unmerged PR: #25;
- head: `0191a45f6e014ab51e715d30954ad2b307bfa1bf`;
- workflow run: `31766543692`;
- job: `94663531377`;
- observed result: Rust `E0432` for the absent verdict-engine API;
- production implementation: absent.

### Initial GREEN

- initial implementation head: `15c79270a2018a55a899d2a88fa2f34276a17efb`;
- workflow run: `31766773174`;
- job: `94664193651`;
- contract tests: 4/4;
- non-compensability matrix tests: 8/8, including seventeen independent single-gate mutations;
- complete workspace suite, Clippy and rustfmt: pass.

Cargo added only the new local `gs-verdict` package to `Cargo.lock`: eight additions, zero deletions and no transitive version change.

## Adversarial findings and corrections

### Numeric reporting edge

The first engine used a direct `u64` to `f64` ratio. Review found that `(u64::MAX - 1) / u64::MAX` can round to `1.0` even though the coverage is incomplete. The gate itself remained safe, but the reported metric would be misleading.

The engine now returns exact `1.0` only when the integer counts are exactly complete. An incomplete positive ratio that rounds upward is clamped to the greatest representable `f64` below `1.0`.

Three regression tests cover:

- incomplete near-maximum counts remain strictly below `1.0`;
- exact maximum counts remain exactly `1.0`;
- empty sets are `0.0` and never vacuously complete.

### Gate interaction search

A complete table of all 256 combinations of the eight boolean critical gates verifies:

- only the all-green combination yields `safe_success=true`;
- all other declared successes yield `false_done=true`;
- failed-gate count equals the number of false gates;
- security and integrity aggregate explanations remain correct.

## Comprehensive GREEN

- head: `ae5cb8f6616e83df850e2fc6917f4fd348439a45`;
- workflow run: `31767112339`;
- job: `94665152614`;
- conclusion: success.

Focused Task 7 suite:

- contract: 4/4;
- matrix: 8/8;
- numeric: 3/3;
- exhaustive truth table: 1/1 containing 256 combinations.

The same run also reproduced the complete workspace suite, including canonical JSON, CAS, Evaluation IR parity and the event journal. Clippy with `-D warnings`, rustfmt and the clean-tree gate passed.

The final read-only exact-head run is recorded in the PR review rather than committed into this file, because committing its identifier would create a new head and an evidence self-reference loop.

## Verified semantics

- coverage is derived only from integer counts;
- `closed > total` is rejected;
- empty obligation/evidence sets never produce vacuous success;
- functional pass, valid task, complete obligations, complete evidence, scope, authority, security policy, exploit absence, regression, replay, independent verification, cleanup and absence of critical risk are non-compensable;
- an advisory risk remains visible without blocking an otherwise complete success;
- a critical risk always blocks safe success;
- `blocked` and `abstained` are not false `DONE` merely for being non-success;
- risk descriptions are trimmed, deduplicated and sorted deterministically;
- failed gates use a fixed order;
- security and integrity aggregate explanations are deterministic;
- invalid verdict/run identifiers fail at the schema boundary;
- identical input produces identical typed and serialized output;
- no LLM judgment, confidence, average, probability or weighted score is used.

## Scope verification

The diff is limited to workspace membership, the local lock entry, the new `gs-verdict` crate, Task 7 packet/evidence and the Task 7 workflow. No schema v1, Evaluation IR type, canonical state, RAGLite, CAS, journal, runner, adapter or `hermesclaw-ci` change is included.

## Explicit limits

- the engine consumes already-classified measurements; it does not execute or validate the underlying tests, replay or reviewer independence itself;
- the engine does not generate IDs, timestamps, signatures or Evidence Bundles;
- advisory/critical risk severity is supplied by an upstream authority and is not inferred;
- policy composition, persistence, runner integration and oracle execution remain out of scope;
- identity-independent external review is not claimed.

## Decision

Current status: `PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE`.

Promotion to the bounded Task 7 status `PROVEN` requires:

1. final read-only workflow success on the exact PR head;
2. role-separated review with no material finding open;
3. signed merge;
4. fresh post-merge workflow success on `main`;
5. state promotion and byte-identical RAGLite projection;
6. Task 8 remains unpacketized until those gates close.
