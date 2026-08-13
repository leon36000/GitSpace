---
doc_id: GS-P00-BOOTSTRAP-TRANSPORT-001
title: GitSpace — Bootstrap Transport Qualification and Publication Plan
status: PARTIALLY_VERIFIED
version: 0.2.0
updated: 2026-08-13
planner: CHATGPT_PROJECT_GITSPACE
target_repository: leon36000/GitSpace
expected_base_commit: f69b22d2bd09aa5eae96693acf501b2464c3be25
product_code_allowed: false
---

# P00-BOOTSTRAP-TRANSPORT-001

## Goal

Qualifier un transport Git byte-preserving, produire les commits réels du bootstrap, vérifier leur intégrité, ouvrir une PR brouillon et préserver toutes les branches non ciblées.

## Résultat exécuté

```yaml
base_verified: f69b22d2bd09aa5eae96693acf501b2464c3be25
branch: bootstrap/canonical-corpus-v0.3
canonical_commit_a: 488fd399314ad834881c7c59d78915ed236c9239
canonical_tree_a: da903750e480beb2806882e0603ab3822dae00bb
projection_commit_b: 08a38c4360a8e5e83332aa5f8f39917576c20030
projection_tree_b: 7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879
pull_request: 1
pull_request_state: DRAFT_OPEN_MERGEABLE
main_modified: false
hermesclaw_ci_modified: false
product_code_added: false
```

## Non-scope respecté

- aucun push direct sur `main`;
- aucune suppression/modification de `hermesclaw-ci`;
- aucun code produit;
- aucune licence;
- aucune CI produit;
- aucun merge;
- aucun blob divergent référencé.

## Méthode qualifiée

1. Branche créée depuis le SHA exact de `main`.
2. Contenus textuels envoyés en UTF-8 direct.
3. Inventaire du tree distant.
4. Commit A créé avec parent et tree explicites.
5. Cinq projections créées par réutilisation des blobs sources.
6. Manifeste créé avec `source_commit=A`.
7. Commit B créé comme unique descendant de A.
8. Diff A→B vérifié : exactement six fichiers.
9. PR #1 ouverte en brouillon.
10. `main` et `hermesclaw-ci` revérifiées.

## Contre-exemple et méthode rejetée

La transcription manuelle d’un payload base64 a produit des blobs divergents. Ces objets sont orphelins et non référencés. La méthode est définitivement rejetée pour les publications canoniques.

## Evidence disponible

- parents et trees A/B;
- inventaire des blobs;
- comparaison A→B;
- identité des cinq couples source/projection;
- métadonnées de PR;
- registres de provenance, risques et conflits;
- rapport `GS-BOOTSTRAP-VERIFICATION-001`.

## Étape de clôture

Le commit C met à jour l’état courant après ouverture de la PR. Le commit D projette `00/02/04` depuis C et enregistre `source_commit=C`.

## Critères restants

- trois revues indépendantes;
- correction de toute finding matérielle;
- décision propriétaire de merge;
- merge sans effet sur `hermesclaw-ci`;
- remplacement atomique des cinq sources du Projet ChatGPT;
- packetisation de Task 1 depuis le SHA canonique fusionné.

## Verdict

`PARTIALLY_VERIFIED`.

Le transport et la publication de branche sont prouvés pour ce bootstrap. Le changement d’autorité de `main` n’est pas prouvé tant que le propriétaire n’a pas accepté et fusionné la PR.
