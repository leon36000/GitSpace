---
evidence_id: P00-TASK-009-RED
status: VALID_RED
recorded_at: 2026-08-14
base_commit: 7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd
red_branch: agent/p00-task-009-red-v1
red_pr: 40
red_head: 2d380c83ddfb0816e3e7e7d5be9a38356eb79c00
workflow_run: 31779294301
workflow_job: 94701336666
merge_ref: 9501c886a90d88c8bc03de621266bed6b2ab6f3e
---
# P00-TASK-009 RED evidence

Task 9 contract tests were written before production code. `crates/gs-foundry-cli/src/lib.rs` was intentionally empty.

GitHub Actions on Ubuntu 24.04 / Rust 1.97.1 executed:

```bash
cargo test -p gs-foundry-cli --test contract
```

and observed Rust `E0432` exactly for the absent authority API:

```text
NativeFoundry
NativeScenario
ObservedClassification
ReplayReport
RunReceipt
receipt_bytes
replay_bytes
```

The proof workflow succeeded only after asserting that compile failure and confirming no production implementation existed. All inherited Task 1–8 workflows were green on the same RED head.

The RunManifest/EvidenceBundle prerequisite conflict had already been closed by signed schema correction `ce0c58d9012b723fbe276a4a33f3f7598dd976aa` and evidence closure `7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd` before this RED branch was created.

PR #40 was closed unmerged. GREEN is implemented on a fresh branch from the same canonical base.

Verdict: `VALID_RED`.
