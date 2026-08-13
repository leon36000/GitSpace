---
doc_id: GS-02
title: GitSpace — Maintenant, décisions et roadmap
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.3.2
updated: 2026-08-13
read_when: EVERY_NEW_CHAT_OR_MAJOR_RESUME
---

# GitSpace — Maintenant, décisions et roadmap

## État actif [GS-NOW-005]

- Architecture C — Native Software World Engine : **APPROUVÉE**.
- C0 — Native Evaluation Foundry hybride : **APPROUVÉE**.
- Nom : GitSpace.
- Propriétaire souverain : humain.
- Architecte-chercheur et auteur des plans : ChatGPT dans le Projet GitSpace.
- Exécuteurs techniques : agents remplaçables, choisis au moment du handoff.
- Dépôt cible : `leon36000/GitSpace`, public, branche par défaut `main`.
- État observé le 2026-08-13 :
  - `main` pointe vers `f69b22d2bd09aa5eae96693acf501b2464c3be25`;
  - le seul fichier observé sur `main` est un README décrivant un dépôt de staging CI privé pour HermesClaw;
  - la branche `hermesclaw-ci` pointe vers `91f55525b231116fd431430f46c87667e5c1f140` lors de la dernière vérification;
  - son dernier commit observé est `ci: remove abandoned HermesClaw proof manifest`;
  - cette branche a avancé plusieurs fois pendant la consolidation, confirmant qu’elle est active et mouvante;
  - cet état contredit l’hypothèse documentaire précédente `EMPTY_NO_COMMITS`.
- Classification du dépôt actuel : `QUARANTINED_EXTERNAL_STATE`.
- Conflit de dépôt : `GS-CONFLICT-REPO-001`.
- Corpus canonique commit-ready v0.3.1 : **PRODUIT LOCALEMENT, NON PUBLIÉ**.
- Spécification Phase 00 : `GS-P00-SPEC-001` v0.2.1, executor-neutral.
- Plan Phase 00 : `GS-P00-PLAN-001` v0.3.0, executor-neutral et non exécutable sans paquet frais.
- Plan de bootstrap : `P00-BOOTSTRAP-PLAN-001` v0.3.0, révisé avec un gate de transport.
- RAGLite : projection preview v0.3.1 générée byte-for-byte depuis le corpus local; le manifeste porte un digest d’arbre, pas un faux SHA de commit.
- Transport distant : **`BLOCKED_WITH_EVIDENCE`**.
  - `gh` n’est pas installé dans l’environnement de planification;
  - le conteneur ne dispose pas d’un transport Git réseau utilisable;
  - un probe du connecteur a créé huit blobs Git non référencés;
  - six blobs correspondaient exactement aux fichiers locaux;
  - deux blobs ont divergé, démontrant que la transcription manuelle d’un gros payload encodé n’est pas une voie sûre;
  - aucun tree, commit, ref, branche ou pull request n’a été créé;
  - `reachable_repository_changes: 0`.
- Conflits actifs : `GS-CONFLICT-TRANSPORT-001` et `GS-CONFLICT-PATCH-001`.
- Le second patch du replay local est une **preuve de reproductibilité**, pas un patch de publication : il référence le SHA synthétique de son commit A local et doit être régénéré après le vrai commit A distant.
- Code produit GitSpace : **non commencé**.
- Code de gouvernance dans le dépôt cible : **non publié**.
- Phase active : **Phase 00 — Research Atlas + Benchmark Foundry**.
- Statut global : `PARTIALLY_VERIFIED`.
- Prochaine action exacte : **`P00-BOOTSTRAP-TRANSPORT-001` — provisionner un transport Git authentifié et byte-preserving depuis un checkout local, vérifier le SHA de `main`, préparer localement les commits A et B avec le vrai SHA A, comparer les blobs, puis pousser la branche et ouvrir une pull request brouillon sans modifier ni supprimer `hermesclaw-ci`.**

Aucune nouvelle tentative de transfert manuel de base64 ou de contenu volumineux via un argument de modèle n’est autorisée.

## Décisions acceptées

- **ADR-0001** : Native World Engine; Git périphérique au produit.
- **ADR-0002** : Rust principal pour le noyau, sans mono-langage dogmatique.
- **ADR-0003** : humain souverain sur intention, valeurs, budget et risque.
- **ADR-0004** : `AgentProcess` comme contributeur technique natif.
- **ADR-0005** : aucun agent ne peut se déclarer terminé; faux `DONE = 0`.
- **ADR-0006** : mémoire hiérarchique, quarantinée, traçable et révoquable.
- **ADR-0007** : transformations sémantiques avant patches textuels, direction à qualifier.
- **ADR-0008** : RAGLite Markdown pour la mémoire du Projet ChatGPT.
- **ADR-0009** : C0 — IR d’évaluation GitSpace souverain, adaptateurs externes remplaçables et Seed Suite initiale de 32 tâches.
- **ADR-0010** : ChatGPT produit et maintient recherche, architecture et plans; les agents d’exécution consomment des paquets acceptés.

## Décisions techniques actives

- **TDR-P00-001-AMENDED** : Rust pour les composants d’autorité et Python pour les adaptateurs; les versions exactes sont sélectionnées et verrouillées par un dossier de qualification frais.
- **TDR-P00-002** : sécurité, autorité, intégrité, portée et nettoyage sont non compensables.
- **TDR-P00-003** : QA indépendante obligatoire pour toute tâche native active.
- **TDR-P00-004** : journal append-only local + CAS pour le premier vertical slice, à qualifier.
- **TDR-P00-005-AMENDED** : aucun harness d’agent n’est canonique; Claude Code reste un exécuteur aval possible.
- **TDR-P00-006** : `leon36000/GitSpace` est le dépôt cible du corpus complet.
- **TDR-P00-007-AMENDED** : le RAGLite est une projection du dépôt et doit porter provenance et digests.
- **TDR-P00-008** : publication RAGLite en deux commits pour éviter l’auto-référence du SHA.
- **TDR-P00-009** : une tâche du plan maître n’est exécutable qu’après packetisation depuis un commit de base frais.
- **TDR-P00-010-PROPOSED** : préserver le staging existant, publier le canon sur une branche dédiée et intégrer par pull request.
- **TDR-P00-011** : toute publication canonique exige un transport byte-preserving avec comparaison des hashes Git source/distant; la transcription manuelle de contenu encodé est interdite.

Les TDR sont réversibles. Elles ne redéfinissent pas le canon produit.

## Éléments STALE ou superseded

- `EMPTY_NO_COMMITS` comme état du dépôt.
- `GS-CC-EXEC-001` comme contrat de planification actif.
- `EXEC-E0` comme prochaine action.
- `P00-TASK-001 READY_NOT_EXECUTED` comme unité immédiatement exécutable.
- `GS-P00-PLAN-001` v0.1 et v0.2 comme plans actifs.
- Rust `1.97.1` et Python `3.12.13` comme pins déjà acceptés.
- tout manifeste RAGLite tentant de contenir le SHA du commit qui le contient.
- `P00-BOOTSTRAP-PUBLISH-001` comme action directement exécutable dans l’environnement de planification actuel.
- le second patch local comme patch publiable sans régénération.
- la transmission manuelle de gros payloads base64 comme transport fiable.

Ces éléments sont conservés dans l’historique et les registres de conflits; ils ne sont pas supprimés de la mémoire négative.

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

1. Un transport authentifié byte-preserving est disponible et qualifié.
2. Le bootstrap canonique est préparé en deux commits locaux depuis le SHA distant attendu.
3. Les blobs locaux et distants du commit A sont identiques.
4. Le manifeste du commit B référence le vrai SHA du commit A.
5. Le conflit de dépôt est conservé et résolu sans perte d’historique.
6. Le plan Phase 00 ne dépend d’aucun fournisseur d’agent.
7. Chaque claim de recherche possède provenance, niveau de preuve, limites et expérience.
8. Le premier paquet produit est dérivé après le merge du bootstrap, pas avant.
9. Aucun état documentaire n’est présenté comme preuve runtime.

## Roadmap condensée

`00 Research/Evals → 01 Constitution → 02 World Engine → 03 GitBridge/Repo Intelligence → 04 AgentKernel → 05 Security/Sandbox → 06 Context/Memory → 07 Intent/Outcome → 08 Change/Shadow Worlds → 09 Proof Mesh → 10 Causal Lab → 11 Model Fabric → 12 Skills/Components → 13 Observatory → 14 Federation`.

## Décisions différées

- harness d’exécution initial;
- Restate versus Temporal;
- Cedar versus Policy IR;
- gVisor versus Firecracker versus Kata;
- worktree Git versus Jujutsu;
- Dagger/Nix;
- framework UI;
- licence;
- stratégie de branchement définitive;
- architecture d’hébergement.

Elles seront tranchées par recherche, prototype ou benchmark.

## Handoff

```yaml
active_phase: PHASE-00
active_deliverable: P00-CANONICAL-REPOSITORY-BOOTSTRAP
phase_status: PARTIALLY_VERIFIED
transport_status: BLOCKED_WITH_EVIDENCE
planner: CHATGPT_PROJECT_GITSPACE
execution_harness: DEFERRED_REPLACEABLE
product_code_started: false
repository:
  full_name: leon36000/GitSpace
  visibility: public
  default_branch: main
  observed_main_sha: f69b22d2bd09aa5eae96693acf501b2464c3be25
  observed_state: NONEMPTY_UNRELATED_STAGING_PLACEHOLDER
  preserved_branch:
    name: hermesclaw-ci
    last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
    moving_branch_recheck_required: true
  conflict_id: GS-CONFLICT-REPO-001
transport_probe:
  unreferenced_blobs_created: 8
  exact_blobs: 6
  mismatched_blobs: 2
  trees_created: 0
  commits_created: 0
  refs_created: 0
  branches_created: 0
  pull_requests_created: 0
  reachable_repository_changes: 0
local_candidate:
  version: 0.3.1
  status: COMMIT_READY_TRANSPORT_BLOCKED
next_exact_action: >-
  P00-BOOTSTRAP-TRANSPORT-001 — provision an authenticated,
  byte-preserving local Git transport; verify main at
  f69b22d2bd09aa5eae96693acf501b2464c3be25; prepare commit A,
  regenerate commit B from the real A SHA, verify blob equality,
  then push the bootstrap branch and open a draft pull request.
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
  - current_repository_state_is_quarantined
  - raglite_uses_two_commit_provenance
  - canonical_transport_is_byte_preserving
  - manual_base64_transport_is_forbidden
```

Ce fichier est volatil. Après publication ou décision structurante, produire une version complète et invalider explicitement la précédente.
