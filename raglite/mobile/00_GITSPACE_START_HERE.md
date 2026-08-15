---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.11
updated: 2026-08-14
---
# GitSpace — START HERE

GitSpace est un **Native Software World Engine pour contributeurs IA**. Architecture C et C0 sont acceptées. L’humain reste souverain sur intention, valeurs, budget et risque irréversible; ChatGPT maintient recherche, canon et plans; les exécuteurs et frameworks restent remplaçables.

## Amorçage

1. Lire `00_GITSPACE_START_HERE.md`.
2. Lire `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`.
3. Construire le `WORKING_SET` : objectif, non-scope, décisions, invariants, risques, preuves, blocages et prochaine action.
4. Charger uniquement les autres sources nécessaires.
5. Ne jamais substituer une conversation, une projection ou une sortie d’outil à une source canonique.

## Routage

- architecture/mission : `01_GITSPACE_MASTER_CANON.md` + ADR Register;
- état courant : `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`;
- recherche : `03_GITSPACE_RESEARCH_ATLAS.md`;
- planification/handoff : `04_GITSPACE_AGENT_PROTOCOL.md` + plan Phase 00;
- preuves Tasks 1–11 : `docs/phase-00/evidence/`;
- preuve Task 11 finale : `docs/phase-00/evidence/P00-TASK-011-POSTMERGE.md`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN` sans preuve fraîche.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Validation Evaluation IR : schéma Draft 2020-12 local avant accès à un adaptateur externe.
- CAS local : objets immuables adressés par SHA-256, lecture re-hashée et aucun overwrite silencieux.
- Journal local : événements canoniques dans le CAS, pointeurs append-only, offsets contigus, chaîne SHA-256 et projections reconstruisibles.
- Verdict : `safe_success` et `false_done` sont recalculés par gates non compensables; aucun score ou consensus ne peut les fournir.
- Runner M0 : opérations typées seulement; workspace et oracle séparés; capabilities strictes; timeout et cleanup vérifiés. Ce runner n’est pas un sandbox de code natif arbitraire.
- Foundry M0 : un verdict historique ne pré-déclare jamais replay, vérification indépendante ou non-régression; replay vérifie les artefacts sans modèle, runner ni mutation du store.
- SDK adaptateur : frontière Python provider-neutral JSON-only; validation canonique avant accès externe; perte sémantique bloquante; artefacts CAS seulement; aucune classe externe ne traverse comme vérité.
- Adaptateur concret : version, commit, package et mapping pinés; log brut conservé; replay indépendant du framework; toute divergence échoue fermée.
- Un shim privé n’est acceptable que sous pin exact, tests négatifs et obligation de requalification à chaque release.
- Un outil qualité externe ne vaut `PASS` que si son état positif est explicitement calculé. Une absence de calcul reste `NOT_COMPUTED_EXTERNAL`, jamais un succès implicite.
- Les identités de run et d’adaptateur servent au routage; le commit source complet et les preuves restent l’autorité de provenance.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-011` sont fusionnées et prouvées dans leurs contrats bornés.

Task 11 qualifie une seule fixture Inspect AI 0.3.258 : `EvalTaskSpec` et `AgentConfiguration` validés, `Task` et `Sample` en mémoire, `mockllm/model`, `generate`, scorer `match` exact, log et record liés au CAS, projection du log complet et rescoring dans un module qui n’importe pas Inspect. Le receiver AnyIO abandonné par la release pinée est fermé par un shim temporaire, sérialisé et toujours restauré.

Son merge correctif GitHub signé est `0eb361843cb67d798f8030763f1fffbcffd665ca`; sa reproduction post-merge fraîche est le run `31861648147`, job `94955991327`. La régression Task 10 est également verte sur `31861648140` / `94955991418`.

La preuve Sonar pré-merge finale contient zéro annotation et zéro issue ouverte, mais aucun objet de quality gate n’a été calculé. Son état canonique est `NOT_COMPUTED_EXTERNAL`, pas `PASS`.

Task 11 est `PROVEN` dans cette frontière bornée. Le milestone M0 et la Phase 00 restent `PARTIALLY_VERIFIED`, notamment parce qu’aucune reproduction par une identité de reviewer séparée, aucun modèle/provider externe et aucun sandbox Harbor ne sont encore qualifiés.

La prochaine unité est `P00-TASK-012` : adaptateur Harbor / Terminal-Bench, mapping Evaluation IR, artefacts CAS, classification d’infrastructure et replay indépendant du framework.
