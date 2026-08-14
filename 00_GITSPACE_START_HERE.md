---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.5
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
- preuves Tasks 1–5 : `docs/phase-00/evidence/`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN` sans preuve indépendante fraîche.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Validation Evaluation IR : schéma Draft 2020-12 local avant décodage Serde.
- CAS local : objets immuables adressés par SHA-256, lecture re-hashée et aucun overwrite silencieux.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-005` sont fusionnées et prouvées.

Task 5 a ajouté le premier Content-Addressed Store GitSpace : backend filesystem local, identité SHA-256 souveraine, layout shardé déterministe, écritures temporaires synchronisées, commit atomique sans remplacement, déduplication idempotente, lecture revalidée et rejets permanents de corruption, symlink et objet non régulier. Son merge GitHub signé est `c8b1a1a50040ce757e44eb2867257c14b270dc8a`; la vérification post-merge fraîche est le run `31757546436`, job `94636551986`.

La prochaine unité est `P00-TASK-006` : journal d’événements append-only et reconstruction de projections avec `EventSink` et `EventSource`. La Phase 00 globale reste `PARTIALLY_VERIFIED`.
