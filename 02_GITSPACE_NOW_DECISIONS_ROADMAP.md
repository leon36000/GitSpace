---
doc_id: GS-02
title: GitSpace — Maintenant, décisions et roadmap
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.1
updated: 2026-08-13
---
# GitSpace — Maintenant, décisions et roadmap

## État actif [GS-NOW-009]

- Architecture C : `ACCEPTED`.
- C0 Native Evaluation Foundry : `ACCEPTED`.
- Dépôt canonique : `leon36000/GitSpace`, `main`.
- Bootstrap documentaire : fusionné et accepté.
- P00-TASK-001 : **`PROVEN`**.
- Merge Task 1 : `61d37de161bedd6fa18232c240dff7df3a9db155`.
- Tree Task 1 : `5af857a73635efa1e85c594cff52355930c84c71`.
- Signature du merge : GitHub `verified=true`.
- `hermesclaw-ci` : préservée à `91f55525b231116fd431430f46c87667e5c1f140` lors de la vérification post-merge.
- Toolchains qualifiées pour le workspace Phase 00 : Rust 1.97.1, Python 3.12.13, uv 0.12.0.
- Plan Phase 00 : 22 unités, packetisation juste-à-temps.
- Seed Suite : 32 tâches spécifiées.
- Phase 00 globale : `PARTIALLY_VERIFIED`.
- Prochaine action exacte : **packetiser P00-TASK-002 depuis le SHA canonique après cette synchronisation d’état, puis implémenter les schémas Evaluation IR v1 par RED → GREEN → vérification externe.**

## Preuves Task 1

- RED initial : absence de `toolchains.lock.json` détectée.
- CI finales sur la tête `3bb1136cd0ae1322a2903f7339d26990074a8782` : Python, uv, rustc, cargo, test contractuel, `cargo metadata` et propreté du dépôt PASS.
- Deux défauts de vérification ont été trouvés et corrigés : oracle uv trop strict et test transitoire qui aurait interdit les futurs crates.
- Diff : neuf chemins, tous dans la portée du paquet.
- Merge squash signé et vérifié.

## Décisions techniques mises à jour

- `TDR-P00-001-AMENDED` devient `PILOT_ACCEPTED_WITH_EVIDENCE` pour le trio Rust/Python/uv de Task 1.
- Inspect et Harbor restent des adaptateurs futurs remplaçables, pas des dépendances canoniques.
- La preuve de version n’est pas encore une attestation complète de supply chain binaire; ce besoin reste à la couche provenance.

## Gates immédiats

1. Commit canonique de cet état puis projection RAGLite.
2. P00-TASK-002 : huit schémas Draft 2020-12.
3. Exemples valides et contrôles négatifs.
4. `additionalProperties: false` dans le noyau.
5. Extensions uniquement namespacées.
6. Digests `sha256:` stricts.
7. Revue de cohérence avec `GS-P00-SPEC-001`.
8. Task 3 non packetisée avant verdict frais Task 2.

## Décisions différées

Temporal, Neon Postgres, SonarQube, Fallow, AMD, sandbox, moteur de politique, Jujutsu et infrastructure distribuée restent différés jusqu’à un besoin mesuré ou une expérience dédiée.

## Handoff

```yaml
active_phase: PHASE-00
completed_tasks:
  - P00-TASK-001
next_task: P00-TASK-002
phase_status: PARTIALLY_VERIFIED
canonical_task1_merge: 61d37de161bedd6fa18232c240dff7df3a9db155
next_exact_action: >-
  Commit this state and its RAGLite projection, then derive P00-TASK-002
  from the resulting canonical main SHA and implement the Evaluation IR
  v1 schemas with test-first verification.
```
