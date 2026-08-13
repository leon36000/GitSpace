---
doc_id: GS-REPO-STATE-001
title: GitSpace — Repository State Evidence
authority: REPOSITORY_EVIDENCE
status: ACTIVE
version: 0.3.2
observed_at: 2026-08-13
repository: leon36000/GitSpace
---

# GitSpace — Repository State Evidence

## Observation atteignable

```yaml
repository: leon36000/GitSpace
visibility: public
default_branch: main
observed_main_sha: f69b22d2bd09aa5eae96693acf501b2464c3be25
main_commit_message: "chore: initialize private CI staging repository"
main_files:
  - README.md
branches:
  main: f69b22d2bd09aa5eae96693acf501b2464c3be25
  hermesclaw-ci: 91f55525b231116fd431430f46c87667e5c1f140
branch_activity:
  latest_commit_message: "ci: remove abandoned HermesClaw proof manifest"
  latest_commit_observed_at: 2026-08-13T07:01:21Z
  moving_branch_recheck_required: true
  previous_observed_shas:
    - 0e330b13690a882295d719efbc3d014cb9b2b977
    - 91f0073344999354a6d2a4c07f9d079e6ecfd32f
reachable_repository_changes: 0
branches_created_by_planner: 0
commits_created_by_planner: 0
pull_requests_created_by_planner: 0
```

Contenu observé du README :

```markdown
# GitSpace

Private CI staging repository.

The `hermesclaw-ci` branch is an isolated, temporary build mirror for the HermesClaw Rust vertical spine. It is not the canonical HermesClaw repository.
```

## Probe de transport — objets non référencés

Le probe a créé huit blobs via l’API d’objets Git. Aucun n’a été placé dans un tree ou référencé par un commit.

### Correspondance exacte avec les fichiers locaux

| Fichier visé | SHA Git local et distant |
|---|---|
| `README.md` | `0570ac09ed0f605ed87640bdf9312319a04edd03` |
| `AGENTS.md` | `6e002ccf01b8deece01c4e66ad3183771d7958be` |
| `docs/repository/GS-REPO-STATE-001.md` v0.3.0 | `9271e4e3e0644f5ba8de71200c21ea0d14bd7e26` |
| `raglite/README.md` | `f4004fd77b28df8714e19d56bf2a17abbf436c64` |
| `00_GITSPACE_START_HERE.md` v0.3.0 | `788f298c9863ffd394e1c07444cfba073bd1b691` |
| `docs/provenance/SOURCE-REGISTER.md` v0.3.0 | `c2a9a84400eaaf5f4198419d3a394c419a672ffa` |

### Objets rejetés pour divergence

| Cible visée | Blob créé | Hash attendu |
|---|---|---|
| première tentative `SOURCE-REGISTER.md` | `26417ec3144a2631704f5346cd6ce3dfc1974c16` | `c2a9a84400eaaf5f4198419d3a394c419a672ffa` |
| `01_GITSPACE_MASTER_CANON.md` | `fd216ea06891d807b696a8c5f475b8714e8c27b9` | `b9d73b88182d3d9fb4f44d1ad71f5a800fabdce4` |

```yaml
unreferenced_blobs_created: 8
exact_blobs: 6
mismatched_blobs: 2
trees_created: 0
commits_created: 0
refs_created: 0
branches_created: 0
pull_requests_created: 0
reachable_repository_changes: 0
```

Ces objets sont `NEGATIVE_EVIDENCE_UNREACHABLE`. Ils ne doivent jamais être réutilisés.

## Classification

`QUARANTINED_EXTERNAL_STATE`

Le README et la branche HermesClaw sont des données de dépôt, pas des instructions GitSpace. La création d’objets orphelins ne change pas l’état atteignable du dépôt, mais constitue un effet distant conservé dans l’audit.

## Contradictions

- `EMPTY_NO_COMMITS` est `STALE`.
- Le README actuel ne correspond pas à l’identité canonique GitSpace.
- Le transport manuel de gros payloads n’est pas byte-preserving.
- Le second patch synthétique ne peut pas être publié tel quel, car son manifeste référence le SHA A du replay local.

## Stratégie réversible

```text
1. ne plus créer de blob par transcription manuelle;
2. provisionner un checkout local authentifié;
3. vérifier main@f69b22d...;
4. préparer commit A localement depuis les fichiers du pack;
5. capturer le vrai SHA A;
6. générer la projection et le manifeste depuis ce SHA;
7. préparer commit B;
8. comparer les blobs locaux;
9. pousser la branche sans force;
10. relire l’arbre distant et comparer les blobs;
11. ouvrir une PR brouillon;
12. ne jamais toucher hermesclaw-ci.
```

## Conditions de fermeture

`GS-CONFLICT-REPO-001`, `GS-CONFLICT-TRANSPORT-001` et `GS-CONFLICT-PATCH-001` peuvent devenir `CLOSED_WITH_EVIDENCE` lorsque :

- la PR est acceptée;
- l’historique du staging reste accessible;
- `hermesclaw-ci` est intacte;
- le tree distant de A correspond au corpus local;
- le manifeste de B référence le vrai A;
- les cinq projections sont byte-identical;
- aucun blob divergent n’est référencé.
