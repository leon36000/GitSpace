---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.8
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
- preuves Tasks 1–8 : `docs/phase-00/evidence/`;
- preuve Task 8 post-merge : `docs/phase-00/evidence/P00-TASK-008-POSTMERGE.md`;
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
- Verdict : `safe_success` et `false_done` sont recalculés par gates non compensables; aucun score ou consensus ne peut les fournir.
- Runner M0 : opérations typées seulement; workspace et oracle séparés; capabilities strictes; effets et snapshot CAS; timeout coopératif; cleanup vérifié. Ce runner n’est pas un sandbox de code natif arbitraire.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-008` sont fusionnées et prouvées dans leurs contrats bornés.

Task 8 a ajouté le premier runner local tool-mediated : chemins relatifs stricts, capabilities composant-par-composant, workspace/oracle séparés, effets ordonnés et CAS-backed, timeout monotone, oracle protégé, snapshot workspace canonique et cleanup vérifié contre le filesystem. Un contre-exemple a révélé qu’un `Delay` de 500 ms sous budget 10 ms pouvait initialement durer `501.896168ms`; le test a échoué avant correction et le sommeil est désormais borné par le budget restant. Son merge GitHub signé est `69e39f77c902a2560bed39314bf8b8fffad8f3f7`; la reproduction post-merge fraîche est le run `31777434678`, job `94695722915`.

La prochaine unité est `P00-TASK-009` : vertical slice CLI et replay. La Phase 00 globale reste `PARTIALLY_VERIFIED`.
