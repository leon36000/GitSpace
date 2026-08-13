---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.3
updated: 2026-08-13
---
# GitSpace — START HERE

GitSpace est un **Native Software World Engine pour contributeurs IA**. Architecture C et C0 sont acceptées. L’humain reste souverain sur intention, valeurs, budget et risque irréversible; ChatGPT maintient recherche, canon et plans; les exécuteurs restent remplaçables.

## Amorçage

1. Lire `00_GITSPACE_START_HERE.md`.
2. Lire `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`.
3. Construire le `WORKING_SET` : objectif, non-scope, décisions, invariants, risques, preuves, blocages et prochaine action.
4. Charger uniquement les autres sources nécessaires.
5. Ne jamais substituer une conversation à une source canonique.

## Routage

- architecture/mission : `01_GITSPACE_MASTER_CANON.md` + ADR Register;
- état courant : `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`;
- recherche : `03_GITSPACE_RESEARCH_ATLAS.md`;
- planification/handoff : `04_GITSPACE_AGENT_PROTOCOL.md` + plan Phase 00;
- preuves Task 1–3 : `docs/phase-00/evidence/`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN`.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Faux `DONE = 0`.

## État

`P00-TASK-001`, `P00-TASK-002` et `P00-TASK-003` sont fusionnées et prouvées. Task 3 a ajouté le seam Rust RFC 8785/JCS + SHA-256 avec dépendances verrouillées, 7/7 vecteurs, Clippy, rustfmt et merge GitHub signé `a9217b95c74b7b0e0a4c97c30e4394db3cb04387`.

La prochaine unité est `P00-TASK-004` : types Rust Evaluation IR et validation/parité avec les schémas. La Phase 00 globale reste `PARTIALLY_VERIFIED`.
