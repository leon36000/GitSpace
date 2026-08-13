---
doc_id: GS-REPO-STATE-001
title: GitSpace — Repository State Evidence
authority: REPOSITORY_EVIDENCE
status: ACTIVE
version: 0.3.4
observed_at: 2026-08-13
repository: leon36000/GitSpace
---

# GitSpace — Repository State Evidence

## État observé

```yaml
repository: leon36000/GitSpace
visibility: public
default_branch: main
main:
  sha: f69b22d2bd09aa5eae96693acf501b2464c3be25
  commit_message: "chore: initialize private CI staging repository"
  tree_sha: 97f1018a95ed503738d8a101b21f7041bbee57c5
preserved_branch:
  name: hermesclaw-ci
  last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
  latest_message: "ci: remove abandoned HermesClaw proof manifest"
bootstrap:
  branch: bootstrap/canonical-corpus-v0.3
  pull_request: 1
  state: DRAFT_OPEN_MERGEABLE_REVIEWED
  canonical_commit_a: 488fd399314ad834881c7c59d78915ed236c9239
  canonical_tree_a: da903750e480beb2806882e0603ab3822dae00bb
  projection_commit_b: 08a38c4360a8e5e83332aa5f8f39917576c20030
  state_commit_c: 4802c26f6ffc8c17d005cb41685bd2244cbd7593
  projection_commit_d: 0c6ed111dea42efb9b4a27e4c305b5ae5f2d1c25
  active_pair_source: raglite/RAGLITE-MANIFEST.yaml
canonical_documents: 20
projection_files: 6
product_code_files: 0
main_writes_performed: 0
hermesclaw_writes_performed: 0
```

## Historique de staging préservé

Le README initial décrivait un dépôt de staging CI HermesClaw. Ce contenu reste dans l’historique de `main`; la PR propose de changer le rôle courant de `main` sans réécriture.

## Preuve A/B

```yaml
A:
  commit: 488fd399314ad834881c7c59d78915ed236c9239
  parent: f69b22d2bd09aa5eae96693acf501b2464c3be25
  tree: da903750e480beb2806882e0603ab3822dae00bb
  canonical_blobs: 19
B:
  commit: 08a38c4360a8e5e83332aa5f8f39917576c20030
  parent: 488fd399314ad834881c7c59d78915ed236c9239
  tree: 7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879
  changed_files_from_a: 6
```

## Preuve C/D

```yaml
C:
  commit: 4802c26f6ffc8c17d005cb41685bd2244cbd7593
  parent: 08a38c4360a8e5e83332aa5f8f39917576c20030
  tree: 77870bdc204c6f3481d4f2c511e7485cd5e53253
  purpose: state_closure_and_verification_report
D:
  commit: 0c6ed111dea42efb9b4a27e4c305b5ae5f2d1c25
  parent: 4802c26f6ffc8c17d005cb41685bd2244cbd7593
  tree: 97b302180bd85579c25b28da8fa8b3d339d85465
  changed_files_from_c: 4
```

D modifie le manifeste et les trois projections dont la source a changé. Les cinq chemins mobiles utilisent néanmoins le même blob que leur source racine.

## Paire de correction de revue

Les corrections d’autorité, de décompte et de type épistémique sont publiées dans une nouvelle paire canon/projection. Son identité exacte est dans le manifeste final, afin d’éviter toute auto-référence des documents à leur propre commit.

## Preuve négative de transport

Des probes ont créé des blobs non référencés, dont certains divergeaient des fichiers visés. Aucun tree, commit, ref ou PR ne les référence. Ils sont `NEGATIVE_EVIDENCE_UNREACHABLE` et interdits de réutilisation.

## Classification

```text
main_and_hermesclaw: PRESERVED
bootstrap_branch: PUBLISHED_DRAFT_REVIEWED
pull_request: MERGEABLE_NOT_ACCEPTED
canonical_authority: PROJECT_SOURCES_UNTIL_OWNER_MERGE
```

## Conditions de fermeture

`GS-CONFLICT-REPO-001` devient `CLOSED_WITH_EVIDENCE` lorsque :

- le propriétaire accepte le merge;
- la PR est fusionnée sans modifier `hermesclaw-ci`;
- le RAGLite du Projet ChatGPT est remplacé depuis la projection acceptée;
- le commit fusionné devient la base de packetisation de Task 1.
