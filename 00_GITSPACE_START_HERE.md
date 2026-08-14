---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.9
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
- preuves Tasks 1–9 : `docs/phase-00/evidence/`;
- preuve Task 9 post-merge : `docs/phase-00/evidence/P00-TASK-009-POSTMERGE.md`;
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
- Foundry M0 : un verdict historique ne pré-déclare jamais replay, vérification indépendante ou non-régression; replay vérifie les artefacts sans modèle, runner ni mutation du store.
- Les identités de run restent liées au commit source complet; un identifiant routé n’est jamais une preuve de provenance suffisante.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-009` sont fusionnées et prouvées dans leurs contrats bornés.

Task 9 a fermé le premier vertical slice natif déterministe : validation Evaluation IR, runner tool-mediated, oracle protégé, CAS, journal, verdict historique non compensable, EvidenceBundle, EvalRunManifest et replay sans modèle. Le replay refuse les substitutions sémantiques, n’initialise ni ne répare un store, ne recrée pas le runner et recompose le verdict et le trace byte-à-byte. Le scénario PASS reste historiquement bloqué tant que régression, replay, evidence et vérification indépendante ne sont pas fermés; le scénario FAIL est le contrôle positif `false_done=true`.

Son merge GitHub signé est `b15a2b74f16e8fa6bf1d88832c9191eab44f2a25`; la reproduction post-merge fraîche est le run `31824037711`, job `94843810930`.

Task 9 est `PROVEN` dans ce contrat borné. Le milestone M0 et la Phase 00 restent `PARTIALLY_VERIFIED`, notamment parce qu’aucune reproduction par une identité de reviewer séparée n’est enregistrée.

La prochaine unité est `P00-TASK-010` : SDK Python d’adaptateur et frontière canonique provider-neutral.
