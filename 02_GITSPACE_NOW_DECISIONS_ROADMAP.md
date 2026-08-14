---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.7
updated: 2026-08-14
---
# GitSpace — Maintenant

Architecture C et C0 restent `ACCEPTED`.

- P00-TASK-001 : `PROVEN`.
- P00-TASK-002 : `PROVEN`.
- P00-TASK-003 : `PROVEN`.
- P00-TASK-004 : `PROVEN`, merge signé `e1d057908f0c9f01c22f9ff5d45000b52bed2e21`.
- P00-TASK-005 : `PROVEN`, merge signé `c8b1a1a50040ce757e44eb2867257c14b270dc8a`.
- P00-TASK-006 : `PROVEN`, merge signé `6c48ef758d0fbdeae3abb9d0e912ad23167c0e3a`.
- P00-TASK-007 : `PROVEN`, merge signé `453b7a1e33daac5d485ad176608225403b2ba5dc`.
- Preuve post-merge Task 7 : run `31767376709`, job `94665911378`, tous les gates PASS.
- Evaluation IR v1 : huit schémas Draft 2020-12 et huit variantes Rust.
- Canonical JSON + SHA-256 : seam Rust fusionné et réutilisé par CAS et journal.
- CAS local : immutable, shardé, atomique sans remplacement et relu avec vérification du digest.
- Journal local : pointeurs append-only vers événements CAS, offsets contigus, chaîne SHA-256, replay vérifié et projection reconstruisible.
- Verdict engine : couvertures dérivées, ensembles non vides obligatoires, gates critiques non compensables, `false_done` et `safe_success` recalculés, explication déterministe et frontière de schéma.
- `hermesclaw-ci` : préservée à `91f55525b231116fd431430f46c87667e5c1f140` et hors scope.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-008` — runner local et isolation d’oracle.

## Prochaine action exacte

Fusionner cette synchronisation, projeter `00`, `02` et `04` byte-à-byte dans RAGLite depuis le merge signé, puis packetiser Task 8 depuis le nouveau SHA de `main`. Task 9 reste bloquée jusqu’au verdict frais Task 8.

```yaml
completed_tasks:
  - P00-TASK-001
  - P00-TASK-002
  - P00-TASK-003
  - P00-TASK-004
  - P00-TASK-005
  - P00-TASK-006
  - P00-TASK-007
next_task: P00-TASK-008
phase_status: PARTIALLY_VERIFIED
```
