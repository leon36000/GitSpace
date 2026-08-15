---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.11
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
- P00-TASK-010 : `PROVEN`, merge signé `06e480d8869f4d2e5e5fce1a670f7074c5be854e`.
- P00-TASK-011 : `PROVEN` dans sa fixture Inspect 0.3.258, merge correctif signé `0eb361843cb67d798f8030763f1fffbcffd665ca`.
- Preuve post-merge Task 11 : run `31861648147`, job `94955991327`, conclusion `success` sur le merge exact.
- Régression Task 10 sur le même merge : run `31861648140`, job `94955991418`, conclusion `success`.
- Sonar pré-merge Task 11 : zéro annotation, zéro issue ouverte, quality gate non calculé; état `NOT_COMPUTED_EXTERNAL`, jamais `PASS`.
- Evaluation IR v1 : huit schémas Draft 2020-12 et huit variantes Rust.
- Canonical JSON + SHA-256 : seam Rust réutilisé par CAS, journal, identités et artefacts Foundry.
- CAS local : immuable, shardé, atomique sans remplacement et relu avec vérification du digest.
- Journal local : append-only, offsets contigus, chaîne SHA-256 et projection reconstruisible.
- Verdict engine : gates critiques non compensables, `false_done` et `safe_success` recalculés, explication déterministe et frontière de schéma.
- Runner local M0 : tool-mediated, workspace/oracle séparés, paths/capabilities stricts, effets CAS, timeout borné et cleanup vérifié.
- Foundry M0 : cinq classifications déterministes, artefacts CAS/journal, verdict historique conservateur et replay sémantique non mutateur.
- SDK adaptateur Python : validation Evaluation IR avant accès externe, JSON builtins exacts, snapshot sémantique, cinq statuts, URI CAS, identités et registre fail-closed.
- Adaptateur Inspect : release/commit/packages pinés, run contrôlé sans réseau, log complet et record CAS, replay/rescore sans import Inspect, shim AnyIO privé piné et sérialisé, 26/26 mutations tuées.
- `hermesclaw-ci` : préservée à `91f55525b231116fd431430f46c87667e5c1f140` et hors scope.
- Milestone M0 : `PARTIALLY_VERIFIED`; une reproduction par une identité de reviewer séparée manque encore.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-012` — adaptateur Harbor / Terminal-Bench.

## Résultat Task 11

```text
canonical Evaluation IR
→ mapping Inspect fermé
→ Task + Sample + mockllm/model
→ generate + exact match
→ EvalLog complet
→ log + record CAS
→ projection + rescoring sans Inspect
```

Invariants fermés :

- release `0.3.258`, commit source, wheel et sdist concordent avec le lock;
- validation Task 10 avant premier accès Inspect;
- aucun provider, secret, endpoint, socket, tool, agent ou sandbox externe;
- wrapper runtime exact `EvalLogs`, cardinalité un, élément exact `EvalLog`;
- score Inspect reproduit indépendamment;
- états `error`/`cancelled` classés INFRA, pas échec agent;
- ordre des événements participant au digest;
- receiver AnyIO fermé, refs actives nettoyées et shim toujours restauré;
- installation du shim sérialisée;
- substitutions, mutations post-construction et options scorer incorrectes échouent fermées;
- workflow exact-head, archive propre et workspace complet verts.

Limites conservées :

- une seule fixture Inspect 0.3.258;
- API privée strictement pinée et à requalifier à chaque release;
- aucun provider externe, réseau, sandbox ou scorer model-graded;
- concurrence Inspect extérieure au lock GitSpace hors contrat;
- qualité Sonar externe non calculée;
- aucune identité de reviewer séparée.

## Prochaine action exacte

Fusionner cette promotion d’état, projeter `00`, `02` et `04` byte-à-byte dans RAGLite depuis le merge signé, puis packetiser Task 12 depuis le nouveau SHA canonique de `main`. Task 13 reste bloquée jusqu’au verdict frais Task 12.

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
  - P00-TASK-011
next_task: P00-TASK-012
m0_status: PARTIALLY_VERIFIED
m0_blocker: IDENTITY_INDEPENDENT_REPRODUCTION_MISSING
phase_status: PARTIALLY_VERIFIED
