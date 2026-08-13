---
doc_id: GS-TRANSPORT-STATE-001
title: GitSpace — Canonical Transport State
authority: TRANSPORT_EVIDENCE
status: QUALIFIED_WITH_EVIDENCE
version: 0.2.0
updated: 2026-08-13
---

# GitSpace — Canonical Transport State

## Verdict

`QUALIFIED_FOR_BOOTSTRAP_WITH_EVIDENCE`

Le transport utilisé pour la PR #1 a préservé les octets et l’identité des blobs pour le corpus canonique et sa projection. Cette qualification ne rend pas toute méthode de transport sûre : elle qualifie précisément le chemin UTF-8 direct + Git object tree + vérification distante.

## Evidence positive

```yaml
base_main: f69b22d2bd09aa5eae96693acf501b2464c3be25
bootstrap_branch: bootstrap/canonical-corpus-v0.3
pull_request: 1
canonical_commit_a:
  sha: 488fd399314ad834881c7c59d78915ed236c9239
  parent: f69b22d2bd09aa5eae96693acf501b2464c3be25
  tree: da903750e480beb2806882e0603ab3822dae00bb
  blobs: 19
projection_commit_b:
  sha: 08a38c4360a8e5e83332aa5f8f39917576c20030
  parent: 488fd399314ad834881c7c59d78915ed236c9239
  tree: 7b6bb98c414cfbd8e81f5c820c75deb3ed9e2879
  changed_files: 6
projection_blob_identity:
  pairs_checked: 5
  pairs_equal: 5
main_writes: 0
hermesclaw_writes: 0
```

Les cinq projections sont les mêmes objets Git que les sources. Cette propriété est plus forte qu’une comparaison textuelle après transfert.

## Evidence négative conservée

```yaml
manual_encoding_route:
  status: REJECTED
  orphan_blobs_created_across_probes: 9
  known_mismatches: 3
  reachable_trees: 0
  reachable_commits: 0
  reachable_refs: 0
```

La dernière divergence observée concernait une tentative `AGENTS.md` dont le blob créé ne correspondait pas au hash attendu. Aucun de ces objets n’est référencé.

## Méthode canonique qualifiée

```text
1. créer ou vérifier la branche dédiée;
2. envoyer le contenu UTF-8 direct ou lire les octets du filesystem;
3. vérifier le blob SHA retourné lorsque le contenu est nouveau;
4. construire le tree depuis des blobs identifiés;
5. créer un commit avec parent explicite;
6. relire le commit et le tree;
7. réutiliser le blob source pour toute projection byte-identical;
8. comparer le diff attendu;
9. vérifier les branches non ciblées;
10. ouvrir une PR brouillon.
```

## Interdictions permanentes

- base64 recopié manuellement par un modèle;
- gros document recomposé depuis un résumé;
- création fichier par fichier sans inventaire final du tree;
- réutilisation d’un blob orphelin non comparé;
- patch projection généré depuis un parent synthétique;
- push direct sur `main`;
- poursuite après divergence.

## Limites de la qualification

- les commits sont non signés au sens GitHub;
- la PR n’est pas fusionnée;
- aucune revue GitHub indépendante distincte n’est encore soumise;
- la qualification porte sur des documents UTF-8, pas sur des artefacts binaires;
- toute future méthode ou autre dépôt doit être requalifié.

## Prochaine action

Revue indépendante de la PR #1, puis décision propriétaire de merge. Le transport n’est plus le blocage courant.
