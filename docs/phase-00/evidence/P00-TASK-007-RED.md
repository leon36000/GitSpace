---
evidence_id: P00-TASK-007-RED
status: VALID_RED
recorded_at: 2026-08-14
base_commit: f04aaacd18914c221bdbe63d9c71a371c9a4cfda
red_branch: agent/p00-task-007-red-v1
red_pr: 25
red_head: 0191a45f6e014ab51e715d30954ad2b307bfa1bf
workflow_run: 31766543692
workflow_job: 94663531377
---
# P00-TASK-007 RED evidence

The contract and non-compensability matrix were written before production code. The `gs-verdict` crate exposed only an empty `lib.rs`.

The GitHub Actions proof checked PR merge ref `f6faf08e0fcb3047ea7d2238804500abbfd521d2` and executed:

```bash
cargo test -p gs-verdict --test contract
```

Rust failed with `E0432` for the absent Task 7 API, including:

```text
CoverageCount
ResidualRisk
VerdictInput
issue_verdict
```

The workflow concluded success only after asserting the non-zero compile result and confirming that `crates/gs-verdict/src/lib.rs` contained no production implementation.

PR #25 was closed unmerged. GREEN is implemented on a separate branch from the same canonical base.

Verdict: `VALID_RED`.
