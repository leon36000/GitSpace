---
evidence_id: P00-TASK-008-VERDICT
status: PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE
recorded_at: 2026-08-14
base_commit: 8c0c3c60e4e906c4c88d9e65f7f48a0e22df5ad5
implementation_pr: 34
red_pr: 33
---
# P00-TASK-008 — Verification verdict

## Result under review

Task 8 adds a bounded tool-mediated local runner. Evaluated behavior is restricted to typed read/write/delay operations. The runner creates fresh sibling workspace/oracle directories, enforces component-aware capabilities, attributes effects through CAS, evaluates protected oracle checks after operations, snapshots only the workspace and removes mutable run state before success is returned.

This component is **not** an arbitrary native-code sandbox.

## TDD evidence

### RED

- closed unmerged PR: #33;
- head: `c3726b2807b3a4d18bece91d5787dc5c7c42a8c0`;
- workflow run: `31776279968`;
- job: `94692255095`;
- merge ref: `a1cfc252223b40c9b62bea604456613562a716c9`;
- observed failure: Rust `E0432` for the absent Task 8 authority API;
- production implementation: absent.

## GREEN history

### First GREEN

Workflow run `31776738495`, job `94693643357`, passed the first runner implementation and full workspace gates after adding only the local package lock entry and mechanical rustfmt changes.

### Deadline counterexample

Adversarial review found that `Delay { millis }` slept the full requested duration before checking the deadline. A 500 ms delay under a 10 ms budget produced a measured elapsed time of `501.896168ms` in workflow `31776865227`, job `94694019770`.

A regression test was committed before the fix. The runner now sleeps `min(requested_delay, remaining_budget)`, then returns `TimedOut` and executes no later effect when the deadline is reached.

### Lifecycle and cleanup hardening

Additional tests verify:

- an allowed effect before a policy violation remains attributed;
- the violating operation and all later operations produce no effect;
- mutable run directories are physically absent after returned Completed, TimedOut and OracleFailed results;
- `cleaned_up=true` is therefore checked against filesystem state rather than trusted as a self-reported bit;
- snapshot artifacts never contain oracle paths;
- an exact authority-root symlink is rejected;
- an existing symlink component under the workspace path resolver is rejected directly in the path module.

The hardened bootstrap run `31777048131`, job `94694573153`, passed Task 8 and the complete workspace suite.

## Verified properties

- strict non-empty relative paths; absolute, `.`, `..`, prefixes and NUL rejected;
- component-aware capability prefixes (`src` does not authorize `src2`);
- explicit empty prefix authorizes the complete workspace;
- agent operations resolve only below `workspace/`;
- traversal attempts toward `oracle/` are policy blocked before I/O;
- fixture/oracle duplicates fail before effects;
- unsafe empty/NUL run IDs fail before run-directory creation;
- run-directory name is SHA-256-derived from run ID;
- read/write effects have contiguous deterministic indices and CAS digests;
- policy block and timeout stop all later effects;
- protected oracle checks run only after completed operations;
- oracle failure is explicit and cleanup still occurs;
- final workspace files are re-read, committed to CAS, lexicographically sorted and represented in canonical JSON;
- snapshot digest references the canonical manifest in CAS;
- mutable run state is removed before a successful `RunResult` is returned;
- existing symlinks on traversed paths fail closed;
- timeout uses monotonic `Instant` and bounds the typed delay test operation by remaining budget.

## Lock and scope

`Cargo.lock` changes by +10/−0 for the local `gs-local-runner` package; no transitive dependency version changes.

Changed runtime surface is limited to:

- workspace membership/lock entry;
- `crates/gs-local-runner/**`;
- Task 8 workflow, packet and evidence.

No Task 7 verdict, CAS, journal, Evaluation IR schema/type, canonical state, RAGLite or `hermesclaw-ci` runtime source is modified.

## Explicit limits

- only typed operations are executed; no arbitrary shell/native/WASM execution;
- capability enforcement is an API/filesystem boundary, not a process sandbox;
- a concurrent hostile native process with arbitrary filesystem access is outside the guarantee;
- parent ancestors of the authority-owned runner root are trusted;
- timeout does not preempt arbitrary native code because arbitrary native code is not accepted by this runner;
- network, secrets, egress, containers and VMs remain later-phase work;
- no identity-independent external security audit is claimed.

## Decision

Current status: `PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE`.

Promotion to bounded Task 8 `PROVEN` requires:

1. final read-only workflow success on the exact PR head;
2. role-separated final review with no material finding open;
3. signed merge;
4. fresh post-merge workflow success on `main`;
5. state promotion and byte-identical RAGLite projection;
6. Task 9 remains unpacketized until those gates close.
