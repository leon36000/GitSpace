---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.10
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
- P00-TASK-009 : `PROVEN`, merge signé `b15a2b74f16e8fa6bf1d88832c9191eab44f2a25`.
- P00-TASK-010 : `PROVEN` dans son contrat borné, merge signé `06e480d8869f4d2e5e5fce1a670f7074c5be854e`.
- Preuve post-merge Task 10 : run `31830147076`, job `94863626878`, conclusion `success` sur le merge exact.
- Evaluation IR v1 : huit schémas Draft 2020-12 et huit variantes Rust.
- Canonical JSON + SHA-256 : seam Rust fusionné et réutilisé par CAS, journal, identités et artefacts Foundry.
- CAS local : immuable, shardé, atomique sans remplacement et relu avec vérification du digest.
- Journal local : pointeurs append-only vers événements CAS, offsets contigus, chaîne SHA-256, replay vérifié et projection reconstruisible.
- Verdict engine : couvertures dérivées, ensembles non vides obligatoires, gates critiques non compensables, `false_done` et `safe_success` recalculés, explication déterministe et frontière de schéma.
- Runner local M0 : tool-mediated, workspace/oracle séparés, chemins/capabilities stricts, effets CAS, timeout borné par budget restant, oracle protégé, snapshot déterministe et cleanup physiquement vérifié.
- Foundry M0 : cinq classifications déterministes; artefacts CAS et journal; verdict historique conservateur; EvidenceBundle/RunManifest acycliques; replay sémantique, byte-stable et non mutateur; identités liées au commit source.
- SDK adaptateur Python : validation Evaluation IR avant accès externe; JSON builtins exacts; snapshot sémantique; cinq statuts; extensions namespacées; URI CAS; identités/registre/result fail-closed; 43 tests et 19/19 mutations.
- `hermesclaw-ci` : préservée à `91f55525b231116fd431430f46c87667e5c1f140` et hors scope.
- Milestone M0 : `PARTIALLY_VERIFIED`; une reproduction par une identité de reviewer séparée manque encore.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-011` — adaptateur Inspect.

## Résultat Task 10

```text
canonical Evaluation IR
→ offline schema validation
→ strict copied JSON request
→ prepare with exact semantic snapshot
→ invoke
→ collect
→ normalized JSON-only AdapterResult
```

Invariants fermés :

- tâche et configuration validées avant tout accès à l’adaptateur;
- aucune résolution réseau de schéma;
- seuls les builtins JSON exacts traversent;
- sous-classes, objets externes, cycles, profondeur excessive, unsafe integers, NaN/Infinity, zéro négatif et surrogates isolés sont refusés;
- perte sémantique bloque l’invocation;
- exceptions et métadonnées hostiles sont bornées;
- artefacts = URI CAS canoniques;
- métriques = nombres exacts finis interopérables;
- descriptor, identité, registre et résultat public sont déterministes et fail-closed;
- workflow final en lecture seule, archive propre et 19/19 mutations tuées.

Limites conservées :

- frontière Python in-process, pas isolation de processus;
- aucun framework concret qualifié;
- références CAS validées sans authentification autonome du contenu externe;
- redaction complète des secrets non fournie;
- aucune identité de reviewer séparée.

## Prochaine action exacte

Fusionner cette promotion d’état, projeter `00`, `02` et `04` byte-à-byte dans RAGLite depuis le merge signé, puis packetiser Task 11 depuis le nouveau SHA canonique de `main`. Task 12 reste bloquée jusqu’au verdict frais Task 11.

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
  - P00-TASK-010
next_task: P00-TASK-011
m0_status: PARTIALLY_VERIFIED
m0_blocker: IDENTITY_INDEPENDENT_REPRODUCTION_MISSING
phase_status: PARTIALLY_VERIFIED
