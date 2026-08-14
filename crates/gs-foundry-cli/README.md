# gs-foundry-cli

Phase 00 M0 native Foundry vertical slice.

This crate composes the already-proven GitSpace authority seams:

```text
Evaluation IR
→ tool-mediated local runner
→ protected oracle result
→ immutable CAS artifacts
→ append-only event journal
→ non-compensable verdict
→ EvidenceBundle
→ EvalRunManifest
→ read-only replay/rescore
```

## Native scenarios

- `pass` — protected oracle passes and produces safe success;
- `fail` — protected oracle fails while success was declared, producing false-DONE;
- `timeout` — monotonic deadline blocks the result;
- `policy` — forbidden workspace action is blocked before an effect;
- `infra` — a controlled pre-existing runner directory produces an infrastructure classification.

No external model, provider, network, container, database or benchmark framework is involved.

## Replay boundary

The receipt is a JSON locator, not a new canonical object. It points to immutable CAS objects and the run journal. Replay:

- validates task, EvidenceBundle, RunManifest and verdict through the sovereign Evaluation IR;
- requires all receipt artifacts to remain readable through verified CAS;
- verifies receipt ↔ bundle ↔ manifest agreement;
- replays exactly three typed journal events;
- rebuilds and compares the persisted trace;
- reissues the verdict from persisted scoring input;
- performs no runner/model invocation and no CAS or journal write.

Repeated replay over the same receipt must yield byte-identical canonical `ReplayReport` JSON.

## CLI

```bash
gs-foundry-cli run --root /tmp/gs-foundry --scenario pass --source-commit <git-sha>
gs-foundry-cli replay --root /tmp/gs-foundry --receipt receipt.json
```

Both commands emit one JSON object on stdout.

## Non-goals

This is a deterministic M0 fixture, not an arbitrary-code benchmark harness. It does not provide external model execution, network, container/VM sandboxing, adapter integration, signatures or remote storage.
