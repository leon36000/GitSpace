---
evidence_id: P00-TASK-009-PREREQ-EVIDENCE-CYCLE
status: CLOSED_WITH_EVIDENCE
recorded_at: 2026-08-14
base_commit: 2da3d0e46edf5b3bf280bca2b5282de7700442bf
red_pr: 37
red_workflow_run: 31778117998
red_workflow_job: 94697773347
fix_pr: 38
fix_head: 0303c5f75eab054fe59e8889d36dac806af1f790
merge_commit: ce0c58d9012b723fbe276a4a33f3f7598dd976aa
merge_tree: 600a3955ac4d65dc0b3b081220b7837d6a93fcc5
---
# Task 9 prerequisite — EvidenceBundle hash-cycle correction

## Finding

During Task 9 packetization, the first real materialization of `EvalRunManifest` and `EvidenceBundle` exposed a content-addressing cycle:

```text
EvalRunManifest.artifacts.evidence_bundle
  → CAS digest of EvidenceBundle

EvidenceBundle.run_manifest_digest
  → digest of complete EvalRunManifest
```

A complete immutable RunManifest required the final EvidenceBundle digest while the complete immutable EvidenceBundle simultaneously required the final RunManifest digest. GitSpace therefore refused to invent a fake SHA-256 fixed point or weaken CAS identity semantics.

## RED proof

Closed unmerged PR #37:

```text
workflow 31778117998
job      94697773347
```

The new acyclicity contract failed exactly because `run_manifest_digest` remained required. All earlier schema tests passed.

## Corrective design

The authority graph is now one-way:

```text
EvalRunManifest → EvidenceBundle
```

The reverse `run_manifest_digest` field was removed from EvidenceBundle v1 before any Foundry-produced EvidenceBundle existed. The manifest CAS URI commits to the bundle's complete bytes; the bundle still carries run/task/environment/commit identity and artifact references. Because the schema remains closed, legacy input containing the removed field is rejected.

## GREEN proof

Fix PR #38 was verified on exact head `0303c5f75eab054fe59e8889d36dac806af1f790`:

```text
Task 2 schema workflow 31778488400 / job 94698909403 — SUCCESS
Task 4 parity workflow 31778488420 / job 94698909503 — SUCCESS
```

The Task 4 run reproduced:

- Python canonical schemas;
- Python shared corpus;
- Rust 1.97.1 identity;
- locked metadata;
- Rust Evaluation IR parity;
- complete Rust workspace against revised IR;
- Clippy `-D warnings`;
- rustfmt;
- clean repository state.

The Task 4 workflow now triggers on future `schemas/v1/**` changes and runs the complete downstream workspace, making schema/type/consumer drift a permanent CI concern rather than a one-time check.

## Signed merge

```text
ce0c58d9012b723fbe276a4a33f3f7598dd976aa
tree 600a3955ac4d65dc0b3b081220b7837d6a93fcc5
verification.verified = true
reason = valid
```

The signed merge has parent `2da3d0e46edf5b3bf280bca2b5282de7700442bf`.

## Decision

`GS-CONFLICT-P00-IR-001 = CLOSED_WITH_EVIDENCE`.

This correction changes no vertical-slice runtime behavior; it repairs the pre-first-use Evaluation IR contract. `P00-TASK-009` may now be redérived from the canonical main containing this signed correction.