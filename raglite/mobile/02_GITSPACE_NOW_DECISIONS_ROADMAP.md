---
doc_id: GS-02
title: GitSpace — Maintenant, décisions et roadmap
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.3.4
updated: 2026-08-13
read_when: EVERY_NEW_CHAT_OR_MAJOR_RESUME
---

# GitSpace — Maintenant, décisions et roadmap

## État actif [GS-NOW-007]

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
- A `488fd399314ad834881c7c59d78915ed236c9239` — canon initial, tree `da903750e480beb2806882e0603ab3822dae00bb`.
- B `08a38c4360a8e5e83332aa5f8f39917576c20030` — projection RAGLite de A.
- C `4802c26f6ffc8c17d005cb41685bd2244cbd7593` — clôture de l’état après publication.
- D `0c6ed111dea42efb9b4a27e4c305b5ae5f2d1c25` — projection RAGLite de C, tree `97b302180bd85579c25b28da8fa8b3d339d85465`.
- La paire active après corrections de revue est identifiée exclusivement dans `raglite/RAGLITE-MANIFEST.yaml`, afin d’éviter toute auto-référence infinie.
- Corpus proposé : **20 documents canoniques + 6 fichiers de projection**.
- Plan Phase 00 : `GS-P00-PLAN-001` v0.4.0, 22 unités, executor-neutral, paquet obligatoire.
- Spécification Phase 00 : `GS-P00-SPEC-001` v0.3.0, 12 lanes et 32 Seed Tasks.
- Transport : **QUALIFIED_FOR_THIS_BOOTSTRAP_WITH_EVIDENCE**.
- Revue autorité/cohérence : **PASS après correction**.
- Revue recherche/méthode : **PASS après remplacement du type non enregistré `EVIDENCE_SYNTHESIS` par `EVIDENCE`**.
- Revue provenance/transport : **PASS avec finding faible sur les commits Git non signés**.
- Ces revues sont rôle-séparées et fondées sur des relectures fraîches, mais pas indépendantes par identité; cette limite reste visible.
- `main` et `hermesclaw-ci` n’ont pas été modifiées.
- Code produit GitSpace : **non commencé**.
- Phase active : **Phase 00 — Research Atlas + Benchmark Foundry**.
- Statut global : `PARTIALLY_VERIFIED`.
- Prochaine action exacte : **le propriétaire examine la PR #1 et accepte ou refuse le merge. En cas d’acceptation, fusionner sans modifier `hermesclaw-ci`, remplacer atomiquement les cinq sources du Projet ChatGPT depuis la projection fusionnée, puis packetiser Task 1 depuis le SHA canonique fusionné.**

## Pourquoi le statut n’est pas PROVEN

- la PR est brouillon et non fusionnée;
- le propriétaire n’a pas encore accepté que `main` devienne le canon GitSpace;
- les revues ne sont pas indépendantes par identité;
- les commits de bootstrap ne sont pas signés;
- aucun code produit, benchmark ou replay runtime de Foundry n’a été exécuté;
- les sources du Projet ChatGPT ne seront remplacées qu’après merge accepté.

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
- **TDR-P00-013** : les sources canoniques ne contiennent pas le SHA de leur propre paire active; le manifeste projection est l’autorité exacte pour cette identité.

## Éléments STALE, superseded ou fermés

- `EMPTY_NO_COMMITS` — `STALE`.
- Claude Code comme planificateur ou harness imposé — `STALE_ARCHIVED`.
- `EXEC-E0` comme prochaine action — `STALE`.
- ancien `P00-TASK-001 READY_NOT_EXECUTED` — `INVALIDATED`.
- plans Phase 00 v0.1/v0.2 — `SUPERSEDED`.
- Rust 1.97.1/Python 3.12.13 comme pins acceptés — `STALE`, candidats seulement.
- manifeste auto-référentiel — `REFUTED`.
- patch B synthétique publiable — `REFUTED`.
- transcription manuelle base64 — `REFUTED`.
- `GS-CONFLICT-TRANSPORT-001` — fermé pour le bootstrap, règle générale conservée.
- `GS-CONFLICT-PATCH-001` — fermé par le vrai couple A/B.
- `GS-CONFLICT-CURRENT-STATE-001` — fermé par C/D puis corrections de revue.
- `GS-CONFLICT-REPO-001` — ouvert jusqu’au merge ou refus propriétaire.

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

1. Décision propriétaire sur la PR #1.
2. En cas d’acceptation : merge sans effet sur `hermesclaw-ci`.
3. Vérification post-merge de `main`, de la branche préservée et du manifeste.
4. Remplacement atomique des cinq sources du Projet ChatGPT.
5. Examen mémoire rapide.
6. Packetisation exacte de Task 1 depuis le SHA fusionné.
7. Aucun code produit avant ces gates.

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
  initial_canonical_commit_a: 488fd399314ad834881c7c59d78915ed236c9239
  initial_projection_commit_b: 08a38c4360a8e5e83332aa5f8f39917576c20030
  state_closure_commit_c: 4802c26f6ffc8c17d005cb41685bd2244cbd7593
  state_projection_commit_d: 0c6ed111dea42efb9b4a27e4c305b5ae5f2d1c25
  active_pair_source: raglite/RAGLITE-MANIFEST.yaml
  preserved_branch:
    name: hermesclaw-ci
    last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
review:
  authority_coherence: PASS_AFTER_FIX
  research_method: PASS_AFTER_FIX
  provenance_transport: PASS_WITH_LOW_FINDING
  identity_independent: false
transport:
  status: QUALIFIED_FOR_BOOTSTRAP_WITH_EVIDENCE
  canonical_method: UTF8_CONTENT_PLUS_GIT_BLOB_REUSE
  forbidden_method: MANUAL_BASE64_TRANSCRIPTION
next_exact_action: >-
  Owner reviews PR #1 and explicitly accepts or rejects the merge.
  On acceptance, merge, verify branches and manifest, atomically
  replace the five ChatGPT project sources, then packetize Task 1
  from the merged canonical SHA.
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
  - raglite_active_pair_is_manifest_authoritative
  - manual_base64_transport_is_forbidden
```

Ce fichier est volatil. Après merge, refus ou démarrage de Task 1, produire une version complète et invalider explicitement la précédente.
