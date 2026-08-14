---
evidence_id: P00-TASK-005-VERDICT
status: PREMERGE_VERIFIED
verified_implementation_head: b4c3ac1169d989ba2ae4b750f194c61fddda14fe
base_commit: 2bf674b4bd4f95214c59e9196b9d9ab2f2c324a5
recorded_at: 2026-08-13
---
# P00-TASK-005 — Pre-merge verification verdict

## Result

`P00-TASK-005` is `PREMERGE_VERIFIED`, not yet `PROVEN`. The local filesystem CAS implementation satisfies its focused and workspace gates on the implementation head. Promotion still requires role-separated reviews, a signed merge, post-merge verification, canonical state synchronization and a separate RAGLite projection.

## Scope and produced seam

The diff is restricted to the Task 5 packet, root Cargo membership/lock, the dedicated workflow and `crates/gs-cas/**`. No Evaluation IR schema/type, canonical JSON implementation, prior task workflow, volatile state file, RAGLite file or `hermesclaw-ci` path is modified.

The produced public seam is:

```rust
pub trait Cas {
    fn put(&self, bytes: &[u8]) -> Result<Digest, CasError>;
    fn get(&self, digest: &Digest) -> Result<Vec<u8>, CasError>;
}

pub struct LocalCas;
```

GitSpace SHA-256 identity is reused from `gs-canonical-json`; Task 5 adds no third-party runtime dependency.

## RED evidence

- PR: `#14`, RED-only and forbidden to merge.
- Head: `3a09fe489f2bd58aabb07e1f1ac482a520ecdd67`.
- Workflow run: `31753178807`.
- Job: `94623203053`.
- Toolchain: Rust/Cargo `1.97.1`.
- Observed failure: unresolved production imports `Cas`, `CasError`, `Digest` and `LocalCas`.
- Interpretation: the contract failed for the intended missing product seam; no unrelated environment failure masked RED.

## Implementation and integrity properties

The implementation provides:

- deterministic `objects/sha256/<2>/<62>` layout derived only from digest bytes;
- unique `create_new` temporary files under the same store root;
- full write, flush and file `sync_all` before visibility;
- read-only committed inode where the qualified platform permits;
- atomic no-replace commit through same-filesystem hard linking;
- concurrent-writer resolution by verifying the winner;
- exact-byte deduplication after digest verification;
- regular-file and symlink checks with an opened-file identity check on Unix;
- re-hashing of every object before `get` returns bytes;
- preservation rather than overwrite of corrupted existing targets;
- structured errors for I/O, missing objects, corruption, digest collision, unsafe paths and atomic-commit failures;
- best-effort guarded cleanup of owned temporary files.

## Fresh verification on implementation head

Task 5 workflow:

- run `31755010885`, job `94628798302` — `SUCCESS`;
- `cargo metadata --locked --no-deps --format-version 1` — PASS;
- `cargo test --locked -p gs-cas --all-targets` — PASS;
- 7 adversarial tests — PASS;
- 4 contract tests — PASS;
- `cargo clippy --locked -p gs-cas --all-targets -- -D warnings` — PASS;
- `cargo fmt --all -- --check` — PASS;
- `cargo test --locked --workspace --all-targets` — PASS, 20 tests total;
- repository-clean assertion — PASS.

Historical compatibility workflows on the same head:

- Task 1 run `31755010837` — `SUCCESS`;
- Task 3 run `31755010815` — `SUCCESS`;
- Task 4 run `31755010850` — `SUCCESS`;
- Task 5 run `31755010885` — `SUCCESS`.

The GitHub combined status for the same head reports all five contexts successful, including SonarCloud Code Analysis and SonarCloud Quality Gate.

## Counterexamples exercised

The permanent suite actively checks:

1. normal put/get and deterministic layout;
2. the standard SHA-256 identity of empty bytes;
3. idempotent duplicate puts without inode replacement on Unix;
4. missing-object errors carrying the requested digest;
5. injected post-commit corruption;
6. refusal to heal or overwrite corrupted negative evidence;
7. 24 simultaneous identical writers producing one complete object;
8. an abandoned partial temporary file remaining non-addressable and non-blocking;
9. Unix temporary-directory permission failure without a partial committed object;
10. object symlink rejection even when target bytes match;
11. symlinked shard rejection without writing outside the namespace;
12. non-regular object-path rejection;
13. ordinary-success temporary cleanup.

## Lockfile provenance

The initial GREEN workflow proved behavior but generated an uncommitted lockfile, causing historical clean-tree gates to fail. The exact generated lock was therefore captured before promotion:

- generating run: `31754441542`, job `94627106211`;
- artifact id: `9202186857`;
- artifact name: `p00-task-005-cargo-lock`;
- artifact archive digest: `sha256:640fb187d0f8d1c3e0544692909318ba7ecee6869ea0f72b0e4951fbe9597612`;
- extracted `Cargo.lock`: 27,278 bytes;
- extracted lock SHA-256: `3d91478c803f558401d41be2860344ce02d06572e810f5a9b0475ac8a719751d`;
- validated branch commit: `c57e2627f9471741ede64471122378e4523f705d`.

The temporary write-enabled workflow used only to commit that already-validated lock was removed immediately. The final workflow is read-only and every Cargo command that resolves the graph uses `--locked`.

## Negative findings retained

- `NEG-P00-010`: direct connector writes for some workflow/tree transitions were blocked; no canonical or live state was altered by those failed calls.
- `NEG-P00-011`: Clippy rejected a Unix test helper using broad `set_readonly(false)`; it was replaced with explicit mode `0o600`, with no waiver.
- `NEG-P00-012`: rustfmt detected source/test drift after the first GREEN; exact formatter output was committed.
- `NEG-P00-013`: the first GREEN generated but did not commit `Cargo.lock`; this broke prior clean-tree gates and was corrected with a captured, validated lock artifact.
- `NEG-P00-014`: branch movement refusals were handled by preserving exact commits and promoting them through fresh GREEN branches rather than forcing refs.
- `NEG-P00-015`: a first documentation-only verdict transcribed the extracted lock hash incorrectly; the commit was abandoned and this corrected verdict was recreated from the last fully verified implementation head.

## Residual risks and limits

- The qualified backend assumes a trusted local root and same-filesystem hard-link support.
- Ubuntu 24.04 / Rust 1.97.1 is freshly verified; non-Unix behavior is implemented but not independently qualified in this task.
- Directory-sync or cleanup failures may be reported after the object link is already visible. Retrying the same `put` is safe because the target is verified and never replaced.
- File permissions provide accidental-write resistance, not protection against a privileged local actor able to chmod or replace files.
- Exact SHA-256 collision behavior is implemented as a structured error but cannot be practically generated by the test suite.
- The task does not claim universal power-loss durability across every filesystem.
- Garbage collection, stale-temp lifecycle policy, streaming, chunking, compression, encryption, remote storage and distributed coordination remain outside Task 5.

## Review and termination gate

The PR timeline must contain three explicit `COMMENT` reviews — contract/scope, filesystem integrity/concurrency, and evidence/provenance. They may be role-separated reviews by the same authenticated identity and must not be described as identity-independent QA.

Current verdict: `PREMERGE_VERIFIED`. `PROVEN` is forbidden until the signed merge and post-merge gates complete.
