---
evidence_id: P00-TASK-006-VERDICT
status: PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE
recorded_at: 2026-08-14
base_commit: 772d5a8c3ff9346263f90424e78d6e6017e13f2d
implementation_pr: 22
red_pr: 21
---
# P00-TASK-006 — Verification verdict

## Result under review

Task 6 adds a bounded local append-only event journal backed by the Task 5 immutable CAS.

```text
canonical RunEvent JSON → immutable CAS object
                              ↓
per-run fixed-width journal pointer + chain
                              ↓
verified replay → disposable RunProjection
```

The journal stores no second copy of the event. Its record contains only the zero-based contiguous offset, the CAS digest and a domain-separated SHA-256 chain digest.

## TDD evidence

### Corrected RED

- branch: `agent/p00-task-006-red-v1`
- closed unmerged PR: #21
- corrected head: `80cb9a40bcf9050aa41beddaffc384494dd05f42`
- workflow run: `31764472772`
- job: `94657375485`
- observed failure: Rust `E0432` for the seven absent Task 6 API symbols
- production implementation: absent

The first RED also produced a task-quality finding: its initial run IDs and event types violated the canonical RunEvent schema. The fixtures were corrected before production code and RED was re-observed.

## GREEN evidence history

### First implementation pass

- initial implementation head: `ccc44ded742d877d5e97b5f6df6b757cfdac20a0`
- run: `31764829439`
- job: `94658392038`
- functional tests: passed
- finding: unused import rejected by Clippy

### Lock graph counterexample

The first bootstrap used `cargo generate-lockfile` and changed 29 existing transitive lock lines while Task 6 added no external dependency. That result was rejected.

The previous Task 5 lockfile was restored and Cargo resolved only the new local workspace package. Commit `22e4329d1b5abdeb6c1657b98842d4b40624f20c` adds exactly the local `gs-event-journal` lock entry: 11 additions, zero deletions, zero transitive version change.

### Formatting gate

- run: `31764993553`
- job: `94658882880`
- contract/adversarial/workspace tests: passed
- Clippy: passed after the unused import fix
- finding: rustfmt differences

Mechanical formatting was applied by the temporary same-repository bootstrap workflow. The workflow's write permission is removed in the final candidate.

### Initial full GREEN

- run: `31765083729`
- job: `94659160171`
- conclusion: success
- Task 6 tests at that point: 14
- workspace, Clippy, rustfmt and clean-tree gates: passed

### Integrity expansion and test defect

Five additional tests were added for header magic, offset corruption, CAS corruption, suffix replay and independent journal handles. Run `31765389288`, job `94660110136`, found that the corruption test attempted an in-place write to an intentionally read-only CAS object. The attack fixture was corrected to delete and replace the object, modeling an actor with arbitrary store write access.

### Hardened GREEN

- head under test: `072be3a99816a64bf36244ca449f1624ac858643`
- run: `31765551622`
- job: `94660598729`
- conclusion: success
- Task 6 contract tests: 6/6
- Task 6 adversarial tests: 8/8
- Task 6 integrity tests: 5/5
- complete workspace suite: pass
- Clippy with `-D warnings`: pass
- rustfmt: pass
- clean repository gate: pass

The final read-only head run is recorded in the PR review because committing its identifier would create a new head and an evidence self-reference loop.

## Verified properties

- event schema and payload digest checked before visibility;
- canonical event bytes stored in CAS before journal pointer;
- zero-based contiguous offsets;
- identical retry idempotence;
- conflicting retry and sequence gaps rejected;
- run ID mismatch rejected;
- fixed header and record lengths;
- changed magic, offset, chain and truncated tails rejected;
- missing or corrupted CAS objects rejected;
- symlink journal replacement rejected on Unix;
- cooperative concurrent writers serialized, including independent handles;
- `read_from` verifies the complete journal before returning a suffix;
- offsets not representable as `usize` produce an empty suffix instead of truncation;
- projection bytes are canonical and deterministic after deletion/rebuild;
- an orphan CAS object without a journal pointer remains invisible;
- successful append calls `sync_all()` before returning.

## Explicit limitations

- locks are cooperative/advisory on some platforms;
- a non-cooperating process with arbitrary filesystem write access is outside the guarantee;
- Task 6 does not claim universal power-loss durability across every filesystem/controller;
- parent-directory persistence is not claimed;
- no replication, consensus, compaction, retention, garbage collection or repair;
- rejected gaps/conflicts may leave unreferenced CAS objects until a future GC design;
- no Temporal, Restate, Neon or PostgreSQL integration;
- no verdict engine or runner behavior.

## Scope verification

Allowed code paths only: workspace membership/lockfile, minimal Digest constructor seam, new `gs-event-journal` crate, Task 6 workflows, packet and evidence. No state, RAGLite, schema, Task 5 CAS implementation or `hermesclaw-ci` change is included.

## Decision

Current status: `PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE`.

Promotion to the bounded Task 6 status `PROVEN` requires:

1. final read-only workflow success on the exact PR head;
2. role-separated review with no material finding open;
3. signed merge;
4. fresh post-merge workflow success on `main`;
5. state promotion and byte-identical RAGLite projection;
6. Task 7 remains unpacketized until those gates close.
