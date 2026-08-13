---
doc_id: GS-02
title: GitSpace — Maintenant, décisions et roadmap
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.3.3
updated: 2026-08-13
read_when: EVERY_NEW_CHAT_OR_MAJOR_RESUME
---

# GitSpace — Maintenant, décisions et roadmap

## État actif [GS-NOW-006]

- Architecture C — Native Software World Engine : **APPROUVÉE**.
- C0 — Native Evaluation Foundry hybride : **APPROUVÉE**.
- Propriétaire souverain : humain.
- Architecte-chercheur et auteur des plans : ChatGPT dans le Projet GitSpace.
- Exécuteurs techniques : agents remplaçables choisis au handoff.
- Dépôt : `leon36000/GitSpace`, public, branche par défaut `main`.
- Base préservée : `main@f69b22d2bd09aa5eae96693acf501b2464c3be25`.
- Branche préservée : `hermesclaw-ci@91f55525b231116fd431430f46c87667e5c1f140` lors de la dernière vérification.
- Branche de bootstrap : `bootstrap/canonical-corpus-v0.3`.
- Pull request : **#1**, brouillon, ouverte et mergeable.
- Commit A — canon initial : `488fd399314ad834881c7c59d78915ed236c9239`.
- Tree A : `da903750e480beb2806882e0603ab3822dae00bb`.
- Commit B — projection RAGLite : `08a38c4360a8e5e83332aa5f8f39917576c20030`.
- Tree B : `7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879`.
- A est parent direct de la base `main` observée.
- B est l’unique descendant de A avant la clôture d’état.
- Diff A→B : exactement six fichiers, soit le manifeste et les cinq projections.
- Chaque projection mobile réutilise le même blob Git que sa source canonique.
- Corpus : 19 documents canoniques + 6 fichiers de projection.
- Plan Phase 00 : `GS-P00-PLAN-001` v0.4.0, 22 unités, executor-neutral, paquet obligatoire.
- Spécification Phase 00 : `GS-P00-SPEC-001` v0.3.0, 12 lanes et 32 Seed Tasks.
- Transport : **QUALIFIED_FOR_THIS_BOOTSTRAP_WITH_EVIDENCE**.
  - contenu UTF-8 direct vérifié;
  - tree Git construit depuis blobs identifiés;
  - parents, trees et diff vérifiés;
  - voie base64 manuelle rejetée après divergences;
  - les blobs orphelins de probe ne sont référencés par aucun commit.
- `main` et `hermesclaw-ci` n’ont pas été modifiées par la publication de branche.
- Code produit GitSpace : **non commencé**.
- Phase active : **Phase 00 — Research Atlas + Benchmark Foundry**.
- Statut global : `PARTIALLY_VERIFIED`.
- Prochaine action exacte : **effectuer les trois revues indépendantes de la PR #1, corriger toute contradiction matérielle, puis demander au propriétaire d’accepter ou refuser le merge; ne pas démarrer Task 1 avant un commit canonique fusionné.**

## Pourquoi le statut n’est pas PROVEN

- la PR est brouillon et non fusionnée;
- le propriétaire n’a pas encore accepté que `main` devienne le canon GitSpace;
- aucune revue humaine ou agentique indépendante distincte n’a encore soumis son verdict GitHub;
- aucun code produit, benchmark ou replay runtime de Foundry n’a été exécuté;
- les sources du Projet ChatGPT ne doivent être remplacées par le RAGLite du dépôt qu’après merge accepté.

## Décisions acceptées

- **ADR-0001** : Native World Engine; Git périphérique au produit.
- **ADR-0002** : Rust principal pour le noyau, sans mono-langage dogmatique.
- **ADR-0003** : humain souverain sur intention, valeurs, budget et risque.
- **ADR-0004** : `AgentProcess` comme contributeur technique natif.
- **ADR-0005** : aucun agent ne peut se déclarer terminé; faux `DONE = 0`.
- **ADR-0006** : mémoire hiérarchique, quarantinée, traçable et révoquable.
- **ADR-0007** : transformations sémantiques avant patches textuels, direction à qualifier.
- **ADR-0008** : RAGLite Markdown pour la mémoire du Projet ChatGPT.
- **ADR-0009** : C0 — IR d’évaluation GitSpace souverain, adaptateurs remplaçables et Seed Suite initiale de 32 tâches.
- **ADR-0010** : ChatGPT produit et maintient recherche, architecture et plans; les agents consomment des paquets acceptés.

## Décisions techniques actives

- **TDR-P00-001-AMENDED** : Rust pour l’autorité et Python pour les adaptateurs; versions exactes après qualification fraîche.
- **TDR-P00-002** : sécurité, autorité, intégrité, portée et nettoyage non compensables.
- **TDR-P00-003** : QA indépendante obligatoire.
- **TDR-P00-004** : journal local + CAS pour M0, à qualifier.
- **TDR-P00-005-AMENDED** : aucun harness d’agent n’est canonique.
- **TDR-P00-006** : `leon36000/GitSpace` est le dépôt cible.
- **TDR-P00-007-AMENDED** : le RAGLite est une projection avec provenance et digests.
- **TDR-P00-008** : publication RAGLite par paire canon/projection.
- **TDR-P00-009** : une tâche n’est exécutable qu’après packetisation depuis un commit frais.
- **TDR-P00-010** : préserver le staging existant et intégrer le canon par branche + PR.
- **TDR-P00-011** : transport canonique byte-preserving; base64 manuel interdit.
- **TDR-P00-012** : toute mise à jour d’état canonique affectant `00/02/04` reçoit une projection RAGLite dérivée de son commit parent.

## Éléments STALE, superseded ou fermés

- `EMPTY_NO_COMMITS` comme état du dépôt — `STALE`.
- `GS-CC-EXEC-001` comme contrat de planification actif — `STALE_ARCHIVED`.
- `EXEC-E0` comme prochaine action — `STALE`.
- `P00-TASK-001 READY_NOT_EXECUTED` dérivé avant dépôt canonique — `INVALIDATED`.
- plans Phase 00 v0.1/v0.2 comme plans actifs — `SUPERSEDED`.
- Rust 1.97.1/Python 3.12.13 comme pins déjà acceptés — `STALE`, candidats seulement.
- manifeste auto-référentiel — `REFUTED`.
- patch B synthétique comme artefact publiable — `REFUTED`; le vrai B a été généré depuis A.
- transcription manuelle base64 comme transport — `REFUTED`.
- `GS-CONFLICT-TRANSPORT-001` — fermé pour le bootstrap par blobs/tree/commits vérifiés; la règle générale reste active.
- `GS-CONFLICT-PATCH-001` — fermé par le vrai couple A/B.
- `GS-CONFLICT-REPO-001` — ouvert jusqu’au merge ou au refus propriétaire.

## Phase 00 — lots

```text
WP1 Research Atlas
WP2 Evaluation IR
WP3 Foundry Kernel
WP4 External Adapters
WP5 Native Seed Suite
WP6 Baseline Matrix
WP7 Scientific Report
```

## Gates immédiats

1. Revue de cohérence/autorité de la PR #1.
2. Revue recherche/méthode de la PR #1.
3. Revue provenance/transport de la PR #1.
4. Correction des défauts matériels trouvés.
5. Acceptation ou refus propriétaire du merge.
6. Après merge seulement : remplacement atomique des cinq sources du Projet ChatGPT.
7. Après synchronisation mémoire : packetisation exacte de Task 1 depuis le SHA fusionné.
8. Aucun code produit avant ces gates.

## Roadmap condensée

`00 Research/Evals → 01 Constitution → 02 World Engine → 03 GitBridge/Repo Intelligence → 04 AgentKernel → 05 Security/Sandbox → 06 Context/Memory → 07 Intent/Outcome → 08 Change/Shadow Worlds → 09 Proof Mesh → 10 Causal Lab → 11 Model Fabric → 12 Skills/Components → 13 Observatory → 14 Federation`.

## Décisions différées

- harness d’exécution initial;
- Restate versus Temporal;
- Cedar versus Policy IR;
- Postgres local versus Neon pour un environnement partagé;
- gVisor versus Firecracker versus Kata;
- worktree Git versus Jujutsu;
- Dagger/Nix;
- SonarQube et Fallow comme couches de contrôle du code produit;
- optimisation AMD pour workloads mesurés;
- framework UI;
- licence;
- architecture d’hébergement.

Ces choix seront activés uniquement lorsqu’un besoin ou une expérience les rend pertinents.

## Handoff

```yaml
active_phase: PHASE-00
active_deliverable: P00-CANONICAL-REPOSITORY-BOOTSTRAP
phase_status: PARTIALLY_VERIFIED
planner: CHATGPT_PROJECT_GITSPACE
execution_harness: DEFERRED_REPLACEABLE
product_code_started: false
repository:
  full_name: leon36000/GitSpace
  visibility: public
  default_branch: main
  base_sha: f69b22d2bd09aa5eae96693acf501b2464c3be25
  bootstrap_branch: bootstrap/canonical-corpus-v0.3
  pull_request: 1
  pull_request_state: DRAFT_OPEN_MERGEABLE
  canonical_commit_a: 488fd399314ad834881c7c59d78915ed236c9239
  projection_commit_b: 08a38c4360a8e5e83332aa5f8f39917576c20030
  preserved_branch:
    name: hermesclaw-ci
    last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
transport:
  status: QUALIFIED_FOR_BOOTSTRAP_WITH_EVIDENCE
  canonical_method: UTF8_CONTENT_PLUS_GIT_BLOB_REUSE
  forbidden_method: MANUAL_BASE64_TRANSCRIPTION
next_exact_action: >-
  Independently review PR #1 for authority/coherence,
  research/method, and provenance/transport; correct material findings;
  then obtain the owner's merge decision. Do not packetize or execute
  Phase-00 Task 1 before an accepted canonical merge.
critical_constraints:
  - architecture_c_is_canonical
  - c0_foundry_is_accepted
  - chatgpt_is_plan_author
  - executors_are_replaceable
  - evaluation_ir_is_sovereign
  - git_is_peripheral_to_product
  - human_is_intent_sovereign
  - false_done_target_zero
  - product_code_not_started
  - hermesclaw_branch_preserved
  - raglite_uses_canonical_parent_provenance
  - manual_base64_transport_is_forbidden
```

Ce fichier est volatil. Après merge, refus, correction structurante ou démarrage de Task 1, produire une version complète et invalider explicitement la précédente.
