---
evidence_id: P00-TASK-006-POSTMERGE
status: PROVEN
recorded_at: 2026-08-14
implementation_pr: 22
merge_commit: 6c48ef758d0fbdeae3abb9d0e912ad23167c0e3a
merge_tree: e46ac42052584b97c532cb60e567d057cc8a8d8b
postmerge_workflow_run: 31765845548
postmerge_workflow_job: 94661445335
---
# P00-TASK-006 — Post-merge verification

## Signed merge

GitHub created signed merge commit:

```text
6c48ef758d0fbdeae3abb9d0e912ad23167c0e3a
```

Its parent is the Task 5 state/projection main commit `772d5a8c3ff9346263f90424e78d6e6017e13f2d`; its tree is `e46ac42052584b97c532cb60e567d057cc8a8d8b`; GitHub reports `verification.verified=true` and `reason=valid`.

## Fresh main replay

The final read-only Task 6 workflow triggered from the `push` event on the signed merge itself:

```text
workflow run 31765845548
job         94661445335
conclusion  success
```

The job checked out `main@6c48ef758d0fbdeae3abb9d0e912ad23167c0e3a` and reproduced from the committed lock graph:

- Cargo metadata;
- Task 3 canonical JSON tests;
- Task 6: 6 contract, 8 adversarial and 5 integrity tests;
- the complete workspace suite;
- Clippy with `-D warnings`;
- rustfmt;
- clean repository state.

## Bounded proven contract

Task 6 is `PROVEN` for the declared local Phase 00 contract:

- canonical full RunEvent bytes in immutable CAS;
- fixed-width append-only per-run index;
- contiguous monotonic offsets;
- domain-separated SHA-256 chain;
- offline schema and payload-digest validation;
- cooperative writer serialization;
- idempotent identical retry;
- fail-closed gap, conflict, truncation, chain, path and CAS corruption handling;
- deterministic canonical projection rebuild.

## Limits preserved

This verdict does not claim distributed consensus, replication, arbitrary-filesystem tamper resistance, universal power-loss durability, automatic repair, compaction, retention, garbage collection, snapshots, a database backend or a durable workflow runtime.

## Negative memory retained

- the first RED fixtures violated the RunEvent schema and were corrected before production code;
- broad lockfile regeneration was rejected and replaced by a local-package-only +11/−0 change;
- Clippy and rustfmt findings were closed;
- a corruption test that attempted in-place mutation of a read-only CAS object was replaced by deletion/replacement;
- final CI permissions are read-only.

## Decision

`P00-TASK-006 = PROVEN` within the bounded contract. `P00-TASK-007` may be packetized only after this state and its RAGLite projection are merged.