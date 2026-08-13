---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.4
updated: 2026-08-13
---
# GitSpace — Maintenant

Architecture C et C0 restent `ACCEPTED`.

- P00-TASK-001 : `PROVEN`.
- P00-TASK-002 : `PROVEN`.
- P00-TASK-003 : `PROVEN`.
- P00-TASK-004 : `PROVEN`, merge signé `e1d057908f0c9f01c22f9ff5d45000b52bed2e21`.
- Evaluation IR v1 : huit schémas Draft 2020-12 et huit variantes Rust.
- Validation : registre URN offline, schéma avant Serde, erreurs structurées.
- Parité : corpus Python/Rust 15 cas + régression adversariale `u64::MAX`.
- Canonical JSON + SHA-256 : seam Rust fusionné.
- `hermesclaw-ci` : préservée et hors scope.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-005` — Content-Addressed Store local.

## Prochaine action exacte

Fusionner cet état, projeter RAGLite depuis le nouveau commit, puis packetiser Task 5 depuis le `main` résultant. Task 6 reste bloquée jusqu’au verdict frais Task 5.

```yaml
completed_tasks: [P00-TASK-001, P00-TASK-002, P00-TASK-003, P00-TASK-004]
next_task: P00-TASK-005
phase_status: PARTIALLY_VERIFIED
```
