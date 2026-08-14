---
evidence_id: P00-TASK-006-RED
status: VALID_RED
recorded_at: 2026-08-14
base_commit: 772d5a8c3ff9346263f90424e78d6e6017e13f2d
red_branch: agent/p00-task-006-red-v1
red_pr: 21
corrected_red_head: 80cb9a40bcf9050aa41beddaffc384494dd05f42
workflow_run: 31764472772
workflow_job: 94657375485
---
# P00-TASK-006 RED evidence

## Intended behavior boundary

The contract tests were written before production code. The `gs-event-journal` crate exposed only an empty `lib.rs` and the workflow asserted that the focused contract suite failed because the Task 6 API did not exist.

## First RED and task defect

The initial RED run `31764127602` / job `94656390022` observed the expected `E0432` missing-API failure. Adversarial review then found that the first test data used short run IDs and dotted lowercase event types that violated the already-canonical RunEvent schema.

This was classified as a task defect, not as an implementation failure. No production code was written. Fixtures were corrected to 26-character Crockford ULID-shaped IDs and uppercase underscore event types.

## Corrected RED

The corrected head `80cb9a40bcf9050aa41beddaffc384494dd05f42` was checked out through PR merge ref `c4997e9f7f8604fe19708f0a8d71d69d0aec590c`.

The inner command:

```bash
cargo test -p gs-event-journal --test contract
```

failed with Rust `E0432` for the exact absent API:

```text
EventError
EventOffset
EventSink
EventSource
LocalEventJournal
projection_bytes
rebuild_run_projection
```

The proof workflow concluded success only after asserting this non-zero result and confirming that `crates/gs-event-journal/src/lib.rs` contained no production implementation.

## Verdict

`VALID_RED`.

PR #21 is RED evidence only and remains unmerged. The GREEN candidate is implemented on a separate branch from the same canonical base.
