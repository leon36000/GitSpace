---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.4
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
- preuves Tasks 1–4 : `docs/phase-00/evidence/`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN`.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Validation Evaluation IR : schéma Draft 2020-12 local avant décodage Serde.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-004` sont fusionnées et prouvées. Task 4 a ajouté huit variantes Rust Evaluation IR, un registre URN offline, des erreurs structurées, un corpus de parité Python/Rust et un contrôle adversarial permanent sur le domaine entier de `execution.seed`.

Son merge GitHub signé est `e1d057908f0c9f01c22f9ff5d45000b52bed2e21` et son tree est identique à la tête qualifiée.

La prochaine unité est `P00-TASK-005` : Content-Addressed Store local. La Phase 00 globale reste `PARTIALLY_VERIFIED`.
