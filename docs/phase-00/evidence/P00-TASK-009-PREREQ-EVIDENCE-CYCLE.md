---
evidence_id: P00-TASK-009-PREREQ-EVIDENCE-CYCLE
status: CORRECTION_UNDER_VERIFICATION
recorded_at: 2026-08-14
base_commit: 2da3d0e46edf5b3bf280bca2b5282de7700442bf
red_pr: 37
red_workflow_run: 31778117998
red_workflow_job: 94697773347
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

A complete immutable RunManifest therefore required the final EvidenceBundle digest, while the complete immutable EvidenceBundle simultaneously required the final RunManifest digest. GitSpace must not invent a fake SHA-256 fixed point or weaken the CAS identity model.

## RED proof

Closed unmerged PR #37 added only a contract requiring a one-way reference graph. Task 2 workflow run `31778117998`, job `94697773347`, failed exactly because `run_manifest_digest` was still listed in EvidenceBundle `required`. All earlier schema checks passed.

## Corrective design

The authoritative edge remains:

```text
EvalRunManifest → EvidenceBundle
```

The reverse `run_manifest_digest` field is removed from EvidenceBundle v1 before any real EvidenceBundle instance has been emitted by the Foundry. The manifest's CAS URI already commits to the complete EvidenceBundle bytes; the bundle retains run ID, task ID, environment digest, commit SHA and artifact map for cross-checking.

This is a Phase 00 schema defect correction, not a semantic relaxation. Because the object is closed (`additionalProperties=false`), legacy `run_manifest_digest` input is explicitly rejected after correction.

## Revalidation requirement

The correction is valid only if:

- Task 2 schema tests pass;
- Python shared corpus passes;
- Rust Evaluation IR parity passes against the same corpus;
- Clippy/rustfmt and locked metadata pass;
- the Task 4 workflow is permanently triggered by future `schemas/v1/**` changes;
- the complete workspace remains green.

Until those gates close, Task 9 remains `BLOCKED_WITH_EVIDENCE` and no vertical-slice implementation is allowed.
