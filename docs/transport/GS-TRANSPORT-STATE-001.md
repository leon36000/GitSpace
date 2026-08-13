---
doc_id: GS-TRANSPORT-STATE-001
title: GitSpace — Canonical Transport State
authority: TRANSPORT_EVIDENCE
status: BLOCKED_WITH_EVIDENCE
version: 0.1.0
updated: 2026-08-13
---

# GitSpace — Canonical Transport State

## Verdict

`BLOCKED_WITH_EVIDENCE`

Le corpus local est prêt, mais l’environnement de planification ne possède pas de canal sûr pour pousser les fichiers du filesystem vers le dépôt privé.

## Evidence

```yaml
local_gh_cli: NOT_INSTALLED
local_git_network: UNAVAILABLE
connector_local_file_upload_for_git_objects: NOT_AVAILABLE
manual_blob_probe:
  unreferenced_blobs_created: 8
  attempts: 8
  exact: 6
  mismatched: 2
remote_reachable_effects:
  trees: 0
  commits: 0
  refs: 0
  branches: 0
  pull_requests: 0
```

Le probe a démontré qu’une transcription manuelle peut produire un blob valide au sens Git mais incorrect au sens du fichier attendu. L’existence d’un SHA ne suffit donc pas à établir l’intégrité.

## Propriété requise

```text
BYTE_PRESERVING_TRANSPORT ⇔
  local filesystem bytes are read directly
  ∧ authenticated Git creates the commit
  ∧ local blob hashes are recorded
  ∧ the remote tree is fetched after push
  ∧ every remote blob equals its local counterpart
```

## Canaux acceptables

- checkout local authentifié avec `git push`;
- agent d’exécution possédant un filesystem et des credentials Git limités à la branche;
- connecteur futur acceptant un chemin de fichier local comme argument natif et retournant l’arbre créé;
- archive signée transférée par un mécanisme binaire puis appliquée localement.

## Canaux rejetés

- base64 recopié manuellement dans un appel d’outil;
- contenu Markdown volumineux recomposé par un modèle;
- création fichier par fichier sans comparaison des blobs;
- push direct sur `main`;
- réutilisation des huit blobs orphelins;
- application du patch B synthétique sans régénération.

## Gate de qualification

1. `main` est toujours `f69b22d2bd09aa5eae96693acf501b2464c3be25`.
2. Le checkout est propre et authentifié.
3. La branche n’existe pas encore ou son SHA attendu est vérifié.
4. Le corpus local passe le validator.
5. Le commit A est créé localement.
6. Son SHA réel est capturé.
7. Le commit B est généré depuis A.
8. Le commit B touche exactement six fichiers.
9. Les hashes locaux sont comparés avant push.
10. Après push, les arbres et blobs distants sont relus.
11. Toute divergence produit un arrêt et une branche rejetée.
12. La PR reste brouillon jusqu’à revue indépendante.

## Prochaine action

`P00-BOOTSTRAP-TRANSPORT-001`.
