---
evidence_id: GS-EVIDENCE-P00-TASK-003-VERDICT
status: VERIFIED_PENDING_FINAL_CI_AND_MERGE
verified_at: 2026-08-13
base_commit: c95cfcff9e79a6f5025dd8652d2b4a40ab587ca6
implementation_head: d7039b2446444364a9c3c2cb67d1810c2a56b3e3
verified_merge_candidate: a7443a169e094a4f63cf82f3c57f3001ec4aba72
---

# P00-TASK-003 — Canonical JSON and digest verification evidence

## Scope

Task 3 adds one Rust authority seam for RFC 8785/JCS canonical JSON and SHA-256 digests. No Evaluation IR Rust types, CAS, journal, runner, Verdict Engine, adapter, database, Temporal, Neon, SonarQube, Fallow or AMD integration is included.

## Research basis

- Canonicalization contract: RFC 8785 / JSON Canonicalization Scheme.
- JCS implementation candidate: `serde_json_canonicalizer = 0.3.2` behind a GitSpace-owned API.
- Hash implementation candidate: RustCrypto `sha2 = 0.11.0`.
- JSON value implementation: `serde_json = 1.0.149` without arbitrary-precision features.
- Dependencies are locked in `Cargo.lock` and final verification uses `--locked`.

## RED evidence

Workflow run `31743869373` on the test-first commit failed for the expected reason:

```text
unresolved import `gs_canonical_json`
```

The tests existed before the library implementation.

## Intermediate negative evidence

- `NEG-P00-006`: first GREEN implementation passed all seven functional tests but Clippy found a `collapsible_if` style finding. Behavior was preserved while formatting/lint quality was corrected.
- `NEG-P00-007`: the first run generated `Cargo.lock` instead of consuming a committed lock. The lockfile was captured from CI, committed with registry checksums, and all final Cargo commands use `--locked`.
- `NEG-P00-008`: an intermediate targeted Clippy allowance was used only to expose the lockfile and rustfmt diff. It is absent from the final crate manifest; final CI passes `-D warnings` without waivers.
- `NEG-P00-009`: rustfmt initially reported formatting differences. The exact formatter output was applied; final `cargo fmt --check` passes.

## Final deterministic verification

Workflow run `31744737116` against GitHub merge candidate `a7443a169e094a4f63cf82f3c57f3001ec4aba72` completed successfully on Ubuntu 24.04.

Verified runtime and gates:

```text
rustc 1.97.1                       PASS
cargo 1.97.1                       PASS
cargo metadata --locked            PASS
cargo test --locked                PASS — 7/7 integration tests
cargo clippy --locked -D warnings  PASS
cargo fmt --check                  PASS
repository clean                   PASS
```

The seven integration controls cover:

1. input object key-order equivalence;
2. recursive object sorting;
3. RFC/JCS number normalization;
4. UTF-16 code-unit ordering edge case;
5. known SHA-256 vector for canonical `{"a":1,"b":2}`;
6. canonical digest equals SHA-256 of canonical bytes;
7. negative-zero rejection at the GitSpace boundary.

Task 1 non-regression workflow run `31744737174` also passed on the same PR candidate, proving the first real crate does not invalidate the persistent toolchain contract.

## Supply-chain note

The final dependency graph is locked with crates.io checksums. A targeted RustSec check confirms that the known `sha2` AVX2 advisory affected version 0.9.7 and was patched from 0.9.8 onward; the locked `sha2 0.11.0` is outside that affected range. Absence of findings for the complete dependency graph is not claimed; comprehensive automated dependency auditing remains a later supply-chain gate.

## SonarQube note

SonarQube was considered as a secondary reviewer once Rust code existed, but the current environment has no reachable Sonar MCP/CLI/container runtime. This is `DEFERRED_BY_ENVIRONMENT`, not evidence of code quality and not a blocker because compiler tests, RFC vectors, Clippy and rustfmt are the authoritative Task 3 gates.

## Remaining gates

- CI rerun with this evidence file on the final head;
- fresh adversarial review of the resulting diff and merge candidate;
- signed squash merge;
- post-merge tree/signature verification;
- state and RAGLite synchronization before Task 4 packetization.

Until those gates close, the canonical current-state file must not mark Task 3 as `PROVEN`.
