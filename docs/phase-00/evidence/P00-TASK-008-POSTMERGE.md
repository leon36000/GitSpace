---
evidence_id: P00-TASK-008-POSTMERGE
status: PROVEN
recorded_at: 2026-08-14
implementation_pr: 34
merge_commit: 69e39f77c902a2560bed39314bf8b8fffad8f3f7
merge_tree: 7d23af6c42c52ea14c1920e1a12fefb3396e25c4
postmerge_workflow_run: 31777434678
postmerge_workflow_job: 94695722915
---
# P00-TASK-008 — Post-merge verification

## Signed merge

GitHub created signed merge commit:

```text
69e39f77c902a2560bed39314bf8b8fffad8f3f7
```

Its parent is the Task 7 state/projection main commit `8c0c3c60e4e906c4c88d9e65f7f48a0e22df5ad5`; its tree is `7d23af6c42c52ea14c1920e1a12fefb3396e25c4`; GitHub reports `verification.verified=true` and `reason=valid`.

## Fresh main replay

The final read-only Task 8 workflow triggered from the `push` event on the signed merge itself:

```text
workflow run 31777434678
job         94695722915
conclusion  success
```

The job checked out `main@69e39f77c902a2560bed39314bf8b8fffad8f3f7` and reproduced from the committed lock graph:

- Cargo metadata;
- all focused `gs-local-runner` tests;
- the complete workspace suite;
- Clippy with `-D warnings`;
- rustfmt;
- clean repository state.

## Bounded proven contract

Task 8 is `PROVEN` for the declared tool-mediated local-runner boundary:

- fresh digest-derived run directory;
- separate workspace and protected oracle siblings;
- strict relative path parsing and component-aware capabilities;
- agent operations resolve only below workspace;
- read/write effects are ordered and committed to the verified CAS;
- policy block and timeout stop all later effects;
- protected oracle checks execute only after completed operations;
- final workspace snapshot is canonical, sorted and CAS-backed;
- mutable run state is physically removed before returned success;
- duplicate fixture/oracle paths and unsafe run IDs fail before effects;
- existing traversed symlinks and an authority-root symlink fail closed;
- typed delay is bounded by the remaining monotonic timeout budget.

## Counterexamples retained

- first GREEN allowed `Delay { millis: 500 }` under a 10 ms timeout to run for `501.896168ms`; a failing regression test was observed before correction;
- cleanup truth is now verified against the filesystem rather than trusted from `cleaned_up=true` alone;
- the temporary bootstrap workflow wrote only the local lock entry/mechanical formatting; final workflow permissions are `contents: read`.

## Limits preserved

This verdict does not claim arbitrary native-code, shell or untrusted-WASM sandboxing. The runner is tool-mediated. A concurrent hostile native process with arbitrary filesystem access, network/secret isolation, process preemption, containers and VM isolation remain outside Task 8 and belong to later phases.

## Repository integrity

`hermesclaw-ci` remains unchanged at `91f55525b231116fd431430f46c87667e5c1f140`.

## Decision

`P00-TASK-008 = PROVEN` within the bounded tool-mediated contract. `P00-TASK-009` may be packetized only after this state and its byte-identical RAGLite projection are merged.