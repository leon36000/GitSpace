---
task_id: P00-TASK-004
evidence_type: RED
status: OBSERVED_LOCALLY_PENDING_CI
base_commit: 70397ad36609044b5f4b1c162b945431c8163d90
updated: 2026-08-13
---

# P00-TASK-004 — RED evidence

The shared Python corpus validates against all eight offline Draft 2020-12 schemas.

The Rust contract test fails before implementation because the following authority API is intentionally absent:

- `validate_json`;
- `validate_task_json`;
- `EvalDocument`;
- `ValidationReport`.

This is the expected RED reason. No Rust Evaluation IR implementation exists in this commit. The external GitHub Actions run must reproduce this failure before GREEN code is added.
