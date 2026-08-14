# gs-foundry-cli

Phase 00 M0 native Foundry vertical slice.

This crate composes the already-proven GitSpace authority seams:

```text
Evaluation IR
→ tool-mediated local runner
→ protected oracle result
→ immutable CAS artifacts
→ append-only event journal
→ non-compensable pre-verification verdict
→ EvidenceBundle
→ EvalRunManifest
→ read-only replay/rescore
```

## Native scenarios

- `pass` — functional behavior and protected oracle pass;
- `fail` — protected oracle fails while success was declared, exercising false-DONE detection;
- `timeout` — monotonic deadline blocks the result;
- `policy` — forbidden workspace action is blocked before an effect;
- `infra` — a controlled pre-existing runner directory produces an infrastructure classification.

No external model, provider, network, container or database is involved.

## Deterministic identity

`RunReceipt`, `EvalVerdict` and `EvidenceBundle` share one 26-character Crockford Base32 suffix. The suffix is the first 128 bits of SHA-256 over the domain-separated tuple:

```text
gitspace:p00-task-009:identity:v1
NUL
source_commit
NUL
scenario_slug
```

The same `(source_commit, scenario)` pair therefore reproduces the same identifiers and remains idempotent. A different source commit or scenario produces a different qualified identity, so two commits cannot alias one run while still allowing both runs to coexist in the same Foundry store.

The suffix is ULID-shaped only to satisfy the Evaluation IR identifier schema; it is not a chronological timestamp. The complete source commit remains present in the receipt and EvidenceBundle and is rechecked during replay. The 128-bit suffix is a routing identity, not a replacement for full provenance evidence.

## Proof chronology

A functional PASS is **not** allowed to self-promote to `safe_success` when the initial verdict is issued. At that moment the EvidenceBundle, replay and identity-independent verification have not yet been closed. The persisted PASS verdict is therefore deliberately `declared_outcome=blocked`, `safe_success=false`, `false_done=false`, with evidence/replay/independent-verification gates open.

The FAIL scenario deliberately declares success despite a failed protected oracle and must therefore produce `false_done=true`.

Replay happens later, from immutable persisted artifacts, and reports `replay_verified=true` and `evidence_verified=true` without rewriting the historical verdict. An eventual independently verified final-success decision belongs to a later/superseding verification step, not to self-assertion inside the original run.

## Replay boundary

The receipt is a JSON locator, not a new canonical object. It points to immutable CAS objects and the run journal. Replay:

- validates task, EvidenceBundle, RunManifest and verdict through the sovereign Evaluation IR;
- binds the receipt, run identity and EvidenceBundle to the source commit actually executed;
- verifies the qualified Task 9 environment in both evidence and manifest;
- requires all receipt artifacts to remain readable through verified CAS;
- verifies the exact qualified bytes of task, plan, state-before, state-after, patch and scoring artifacts;
- verifies receipt ↔ bundle ↔ manifest agreement;
- replays exactly three complete typed journal events;
- rebuilds and compares the persisted trace;
- reissues the historical verdict from persisted scoring input and the qualified identity;
- performs no runner/model invocation and no CAS or journal write.

Repeated replay over the same receipt must yield byte-identical canonical `ReplayReport` JSON.

## Provenance in tests

When Git metadata is available, the test harness binds `source_commit` to the exact checked-out commit using `git rev-parse HEAD`. Clean archive replays have no Git metadata and use an explicit all-zero synthetic digest solely to exercise the contract; that synthetic value is never claimed as repository provenance.

## CLI

```bash
gs-foundry-cli run --root /tmp/gs-foundry --scenario pass --source-commit <git-sha>
gs-foundry-cli replay --root /tmp/gs-foundry --receipt receipt.json
```

Both commands emit one JSON object on stdout.

## Non-goals

This is a deterministic M0 fixture, not an arbitrary-code benchmark harness. It does not provide external model execution, network, container/VM sandboxing, adapter integration, signatures or remote storage.
