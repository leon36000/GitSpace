---
doc_id: GS-REPO-STATE-001
title: GitSpace — Repository State Evidence
authority: REPOSITORY_EVIDENCE
status: ACTIVE
version: 0.3.3
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
  files:
    - README.md
preserved_branch:
  name: hermesclaw-ci
  last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
  latest_message: "ci: remove abandoned HermesClaw proof manifest"
bootstrap:
  branch: bootstrap/canonical-corpus-v0.3
  pull_request: 1
  state: DRAFT_OPEN_MERGEABLE
  canonical_commit_a: 488fd399314ad834881c7c59d78915ed236c9239
  canonical_tree_a: da903750e480beb2806882e0603ab3822dae00bb
  projection_commit_b: 08a38c4360a8e5e83332aa5f8f39917576c20030
  projection_tree_b: 7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879
  state_closure_pair: pending_in_this_branch
product_code_files: 0
main_writes_performed: 0
hermesclaw_writes_performed: 0
```

## Historique de staging préservé

Contenu initial observé du README :

```markdown
# GitSpace

Private CI staging repository.

The `hermesclaw-ci` branch is an isolated, temporary build mirror for the HermesClaw Rust vertical spine. It is not the canonical HermesClaw repository.
```

Ce contenu reste dans l’historique de `main`. La PR propose de changer le rôle courant de `main` sans réécriture de l’historique.

## Preuve du commit A

```yaml
commit: 488fd399314ad834881c7c59d78915ed236c9239
parent: f69b22d2bd09aa5eae96693acf501b2464c3be25
tree: da903750e480beb2806882e0603ab3822dae00bb
message: "docs(canon): bootstrap GitSpace native world engine corpus"
canonical_blobs: 19
product_code_blobs: 0
```

Le tree A contient uniquement des documents Markdown et remplace le README dans la branche proposée.

## Preuve du commit B

```yaml
commit: 08a38c4360a8e5e83332aa5f8f39917576c20030
parent: 488fd399314ad834881c7c59d78915ed236c9239
tree: 7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879
changed_files_from_a: 6
```

Les six fichiers sont :

- `raglite/RAGLITE-MANIFEST.yaml`;
- les cinq fichiers sous `raglite/mobile/`.

Chaque fichier mobile a le même blob SHA que sa source racine.

## Preuve négative de transport

Des probes antérieurs ont créé des blobs non référencés, dont certains divergeaient des fichiers visés. Aucun tree, commit, ref ou PR ne les référence. Ils sont `NEGATIVE_EVIDENCE_UNREACHABLE` et ne doivent jamais être réutilisés.

## Classification

```text
main_and_hermesclaw: PRESERVED
bootstrap_branch: PUBLISHED_DRAFT
pull_request: MERGEABLE_NOT_ACCEPTED
canonical_authority: PROJECT_SOURCES_UNTIL_OWNER_MERGE
```

## Conditions de fermeture

`GS-CONFLICT-REPO-001` devient `CLOSED_WITH_EVIDENCE` lorsque :

- les revues requises sont satisfaites;
- le propriétaire accepte le merge;
- la PR est fusionnée sans modifier `hermesclaw-ci`;
- le RAGLite du Projet ChatGPT est remplacé depuis la projection acceptée;
- le commit fusionné devient la base de packetisation de Task 1.
