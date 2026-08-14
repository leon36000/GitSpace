---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.9
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
- P00-TASK-008 : `PROVEN`, merge signé `69e39f77c902a2560bed39314bf8b8fffad8f3f7`.
- P00-TASK-009 : `PROVEN` dans son contrat borné, merge signé `b15a2b74f16e8fa6bf1d88832c9191eab44f2a25`.
- Preuve post-merge Task 9 : run `31824037711`, job `94843810930`, conclusion `success` sur le merge exact.
- Push du merge Task 9 : workflows Task 6 `31824037655`, Task 7 `31824037841`, Task 8 `31824037632` et Task 9 `31824037711`, tous `success`.
- Evaluation IR v1 : huit schémas Draft 2020-12 et huit variantes Rust.
- Canonical JSON + SHA-256 : seam Rust fusionné et réutilisé par CAS, journal, identités et artefacts Foundry.
- CAS local : immuable, shardé, atomique sans remplacement et relu avec vérification du digest.
- Journal local : pointeurs append-only vers événements CAS, offsets contigus, chaîne SHA-256, replay vérifié et projection reconstruisible.
- Verdict engine : couvertures dérivées, ensembles non vides obligatoires, gates critiques non compensables, `false_done` et `safe_success` recalculés, explication déterministe et frontière de schéma.
- Runner local M0 : tool-mediated, workspace/oracle séparés, chemins/capabilities stricts, effets CAS, timeout borné par budget restant, oracle protégé, snapshot déterministe et cleanup physiquement vérifié.
- Foundry M0 : cinq classifications déterministes; artefacts CAS et journal; verdict historique conservateur; EvidenceBundle/RunManifest acycliques; replay sémantique, byte-stable et non mutateur; identités liées au commit source.
- `hermesclaw-ci` : préservée à `91f55525b231116fd431430f46c87667e5c1f140` et hors scope.
- Milestone M0 : `PARTIALLY_VERIFIED`; une reproduction par une identité de reviewer séparée manque encore.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-010` — SDK Python d’adaptateur.

## Résultat Task 9

```text
validate
→ prepare
→ run
→ protected oracle
→ CAS
→ journal
→ historical verdict
→ EvidenceBundle
→ EvalRunManifest
→ replay without model or store mutation
```

Invariants fermés :

- PASS fonctionnel ne s’auto-promeut pas en succès prouvé;
- FAIL déclaré success après oracle négatif produit `false_done=true`;
- substitutions CAS seulement hash-valides échouent si leur sémantique diffère;
- receipt, EvidenceBundle et manifest concordent avec le commit source complet;
- deux commits ne partagent pas le même run ID;
- replay ne crée ou répare aucun layout et ne recrée pas le runner;
- symlinks Foundry/CAS/journal présents avant ouverture sont rejetés;
- verdict et trace sont reconstruits de façon déterministe.

Limites conservées :

- aucune identité de reviewer séparée;
- aucune exécution de code arbitraire ou de framework externe;
- aucune attestation autonome du `source_commit` fourni au CLI hors harness exact-head;
- aucune défense complète contre une course filesystem hostile concurrente;
- dénominateur canonique futur des obligations visibles/protégées/runtime encore `UNKNOWN`.

## Prochaine action exacte

Fusionner cette promotion d’état, projeter `00`, `02` et `04` byte-à-byte dans RAGLite depuis le merge signé, puis packetiser Task 10 depuis le nouveau SHA canonique de `main`. Task 11 reste bloquée jusqu’au verdict frais Task 10.

```yaml
completed_tasks:
  - P00-TASK-001
  - P00-TASK-002
  - P00-TASK-003
  - P00-TASK-004
  - P00-TASK-005
  - P00-TASK-006
  - P00-TASK-007
  - P00-TASK-008
  - P00-TASK-009
next_task: P00-TASK-010
m0_status: PARTIALLY_VERIFIED
m0_blocker: IDENTITY_INDEPENDENT_REPRODUCTION_MISSING
phase_status: PARTIALLY_VERIFIED
