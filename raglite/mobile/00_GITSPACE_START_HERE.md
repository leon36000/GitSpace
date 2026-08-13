---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.1
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
- preuve Task 1 : `docs/phase-00/evidence/P00-TASK-001-VERDICT.md`;
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

Le bootstrap documentaire est fusionné. `P00-TASK-001` est fusionnée et prouvée sur `main` par CI externe, revue adversariale et merge signé `61d37de161bedd6fa18232c240dff7df3a9db155`. La prochaine unité est `P00-TASK-002` : schémas Evaluation IR v1. La Phase 00 globale reste `PARTIALLY_VERIFIED`.

Le manifeste RAGLite porte l’identité exacte de la paire canon/projection active.
