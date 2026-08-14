---
task_id: P00-TASK-004
packet_version: 0.2.0
base_commit: 70397ad36609044b5f4b1c162b945431c8163d90
status: RED_PENDING_EXTERNAL_REPRODUCTION
---

# P00-TASK-004 execution state

## Goal

Add eight validated Rust Evaluation IR document types, an offline Draft 2020-12 schema registry, structured validation issues, and Python/Rust parity over one shared corpus.

## Current gate

The RED commit is complete. The Python schema baseline must pass while the Rust parity test fails specifically because the authority API is absent.

## GREEN constraints

- validate schema before typed decoding;
- no network schema resolution;
- keep schemas authoritative;
- do not duplicate field constraints in a weaker validator;
- exact dependencies and committed `Cargo.lock`;
- stable `ValidationIssue { path, code, message }`;
- Clippy `-D warnings` and rustfmt;
- no changes outside the declared Task 4 surfaces.
