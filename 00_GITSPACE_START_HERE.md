---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.10
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
- preuves Tasks 1–10 : `docs/phase-00/evidence/`;
- preuve Task 10 post-merge : `docs/phase-00/evidence/P00-TASK-010-POSTMERGE.md`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN` sans preuve fraîche.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Validation Evaluation IR : schéma Draft 2020-12 local avant décodage Serde ou accès à un adaptateur externe.
- CAS local : objets immuables adressés par SHA-256, lecture re-hashée et aucun overwrite silencieux.
- Journal local : événements canoniques dans le CAS, pointeurs append-only, offsets contigus, chaîne SHA-256 et projections reconstruisibles.
- Verdict : `safe_success` et `false_done` sont recalculés par gates non compensables; aucun score ou consensus ne peut les fournir.
- Runner M0 : opérations typées seulement; workspace et oracle séparés; capabilities strictes; effets et snapshot CAS; timeout coopératif; cleanup vérifié. Ce runner n’est pas un sandbox de code natif arbitraire.
- Foundry M0 : un verdict historique ne pré-déclare jamais replay, vérification indépendante ou non-régression; replay vérifie les artefacts sans modèle, runner ni mutation du store.
- SDK adaptateur : frontière Python provider-neutral JSON-only; validation canonique avant accès externe; perte sémantique bloquante; artefacts CAS seulement; aucune classe externe ne traverse comme vérité.
- Les identités de run et d’adaptateur servent au routage; le commit source complet et les preuves restent l’autorité de provenance.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-010` sont fusionnées et prouvées dans leurs contrats bornés.

Task 10 a fermé la première frontière provider-neutral : validation offline de `EvalTaskSpec` et `AgentConfiguration`, builtins JSON exacts, copie profonde, snapshot sémantique obligatoire, cinq statuts normalisés, extensions namespacées, URI CAS strictes, identités bornées, registre fail-closed et constructeur public cohérent avec le SDK. Les sous-classes Python, valeurs non interopérables, exceptions et métadonnées hostiles, clés à effets, perte sémantique et identités forgées échouent fermées.

Son merge GitHub signé est `06e480d8869f4d2e5e5fce1a670f7074c5be854e`; la reproduction post-merge fraîche est le run `31830147076`, job `94863626878`.

Task 10 est `PROVEN` dans cette frontière bornée. Le milestone M0 et la Phase 00 restent `PARTIALLY_VERIFIED`, notamment parce qu’aucune reproduction par une identité de reviewer séparée n’est enregistrée et qu’aucun framework externe concret n’est encore qualifié.

La prochaine unité est `P00-TASK-011` : adaptateur Inspect contrôlé, artefacts CAS et rescoring indépendant d’Inspect.
