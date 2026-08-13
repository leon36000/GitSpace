---
evidence_id: GS-EVIDENCE-P00-TASK-004-VERDICT
status: VERIFIED_PENDING_SIGNED_MERGE
verified_at: 2026-08-13
base_commit: 70397ad36609044b5f4b1c162b945431c8163d90
implementation_head: 008863a500908f99ddbc49402db8037a4974dfdb
pull_request: 11
---

# P00-TASK-004 — Rust Evaluation IR types and schema parity

## Scope

Task 4 adds GitSpace-owned Rust representations for all eight Evaluation IR v1 contracts, an offline Draft 2020-12 registry, stable structured validation issues and schema-first typed parsing. Canonical JSON, CAS, journal, verdict runtime logic, adapters and databases remain unchanged and out of scope.

## Required seam

```rust
pub fn validate_task_json(value: &serde_json::Value) -> Result<(), ValidationReport>;
pub fn parse_task_json(value: &serde_json::Value) -> Result<EvalTaskSpec, ValidationReport>;
```

The generic seam additionally supports the eight contracts through `SchemaName`, `validate_named_json` and `parse_named_json`.

## Dependency and retrieval boundary

The locked candidate uses exact versions:

```text
jsonschema = 0.49.9, default features disabled
serde = 1.0.229, derive enabled
serde_json = 1.0.149
```

All eight schemas are embedded with `include_str!` and registered under their canonical `urn:gitspace:schema:v1:*` identifiers before validator construction. The implementation does not configure HTTP or filesystem schema retrieval. This proves the Task 4 path uses the local registry; it is not a comprehensive supply-chain or network-capability audit of every transitive crate.

## RED evidence

PR #10 was opened solely to observe RED and was closed without merge. Workflow run `31747950641`, job `94606872702`, exited 101 for the intended reason:

```text
error[E0432]: unresolved import `gs_eval_ir`
```

The public and parity tests therefore existed before `src/lib.rs`.

## Shared parity evidence

The authoritative corpus contains 15 positive and negative cases and covers every v1 schema:

1. `EvalTaskSpec`;
2. `WorldFixture`;
3. `OracleBundle`;
4. `AgentConfiguration`;
5. `EvalRunManifest`;
6. `RunEvent`;
7. `EvidenceBundle`;
8. `EvalVerdict`.

Negative cases retain rejection of malformed IDs and digests, non-namespaced extensions, unknown core fields, malformed CAS URIs and contradictory verdict states. Python Draft 2020-12 and Rust evaluate the same materialized JSON values.

## Negative and adversarial evidence

- `NEG-P00-010`: an initial file-transport path removed two Rust attribute markers. The compiler rejected the source; declarations were restored and split into focused modules.
- `NEG-P00-011`: the first shared corpus covered only seven of eight schemas. `EvalRunManifest` positive and unknown-core negative controls were added before qualification.
- `NEG-P00-012`: the first otherwise-green typed model narrowed schema-valid `execution.seed` values to `i64`. Adversarial run `31750559131`, job `94615095218`, proved the divergence with `u64::MAX`: schema validation passed and typed decode failed with `expected i64`. The type is now `i128`, covering every integer representable by `serde_json::Value`; the counterexample remains a permanent regression test.
- `NEG-P00-013`: Cargo initially reported the lockfile stale after adding Task 4 dependencies. The exact `Cargo.lock` and Rust 1.97.1 `rustfmt` output were generated in GitHub Actions, committed to the PR branch, and all final Cargo gates use `--locked`.

## Final deterministic verification

Workflow run `31750652767`, job `94615394813`, completed successfully on Ubuntu 24.04 against implementation head `008863a500908f99ddbc49402db8037a4974dfdb`.

```text
Python 3.12.13 identity                         PASS
jsonschema 4.26.0 identity                      PASS
canonical Python schema controls                PASS — 11/11
shared Python parity corpus                     PASS
rustc 1.97.1 / cargo 1.97.1                     PASS
cargo metadata --locked                         PASS
cargo test --locked -p gs-eval-ir --all-targets PASS — 3/3
cargo clippy --locked -D warnings                PASS
cargo fmt --all -- --check                      PASS
repository clean                                PASS
```

Regression workflows passed on the same head:

```text
P00 Task 001 — run 31750652787 PASS
P00 Task 003 — run 31750652772 PASS
```

## Review verdict

Specification axis: `PASS_PENDING_SIGNED_MERGE`. The required seam, validation order, local URN registry, eight typed variants, stable issue fields, parity corpus and locked gates are covered by fresh executable evidence.

Engineering-quality axis: `PASS_WITH_RESIDUAL_LIMITS`. No material unresolved defect remains within Task 4 scope. The registry is rebuilt per call, which is correct but may later warrant measured caching. Date-time `format` remains the schema's annotation behavior in both validators; stricter semantic format enforcement is not claimed. Comprehensive dependency vulnerability analysis is deferred to the dedicated supply-chain layer.

SonarQube remains `DEFERRED_BY_ENVIRONMENT`: no reachable Sonar MCP/CLI/container runtime exists in this session. This is not a quality PASS and is not substituted for compiler, parity, Clippy or rustfmt evidence.

## Remaining gates

- rerun all affected CI with this evidence file on the final PR head;
- final diff/review-thread inspection;
- signed squash merge;
- post-merge verification of tree, signature and workflows;
- state synchronization, followed by a separate byte-identical RAGLite projection.

Until these gates close, the canonical current-state file must not mark Task 4 as `PROVEN`, and Task 5 remains blocked.
