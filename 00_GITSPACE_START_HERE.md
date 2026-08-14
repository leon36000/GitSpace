---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.6
updated: 2026-08-14
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
- preuves Tasks 1–6 : `docs/phase-00/evidence/`;
- preuve Task 6 post-merge : `docs/phase-00/evidence/P00-TASK-006-POSTMERGE.md`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN` sans preuve fraîche.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Validation Evaluation IR : schéma Draft 2020-12 local avant décodage Serde.
- CAS local : objets immuables adressés par SHA-256, lecture re-hashée et aucun overwrite silencieux.
- Journal local : événements canoniques dans le CAS, pointeurs append-only, offsets contigus, chaîne SHA-256 et projections reconstruisibles.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-006` sont fusionnées et prouvées dans leurs contrats bornés.

Task 6 a ajouté le premier journal d’événements GitSpace : index local append-only à enregistrements fixes, événements canoniques dans le CAS, validation de schéma et de payload, retries idempotents, verrouillage coopératif, détection de corruption/troncature et reconstruction déterministe de `RunProjection`. Son merge GitHub signé est `6c48ef758d0fbdeae3abb9d0e912ad23167c0e3a`; la reproduction post-merge fraîche est le run `31765845548`, job `94661445335`.

La prochaine unité est `P00-TASK-007` : verdict engine non compensable. La Phase 00 globale reste `PARTIALLY_VERIFIED`.
