---
doc_id: GS-P00-BOOTSTRAP-TRANSPORT-001
title: GitSpace — Bootstrap Transport Qualification and Publication Plan
status: BLOCKED_WITH_EVIDENCE
version: 0.1.0
updated: 2026-08-13
planner: CHATGPT_PROJECT_GITSPACE
target_repository: leon36000/GitSpace
expected_base_commit: f69b22d2bd09aa5eae96693acf501b2464c3be25
product_code_allowed: false
---

# P00-BOOTSTRAP-TRANSPORT-001

## Goal

Qualifier un transport Git authentifié et byte-preserving, préparer les deux commits réels, vérifier leur intégrité, pousser une branche dédiée et ouvrir une pull request brouillon.

## Non-scope

- aucune modification de `main` directe;
- aucune suppression ou modification de `hermesclaw-ci`;
- aucun code produit;
- aucune licence;
- aucun force push;
- aucun blob construit par transcription manuelle;
- aucun merge.

## Préconditions

```yaml
repository: leon36000/GitSpace
expected_main: f69b22d2bd09aa5eae96693acf501b2464c3be25
branch: bootstrap/canonical-corpus-v0.3
working_tree: clean
authenticated_transport: required
byte_preserving_filesystem_access: required
candidate_validator: PASS
```

Si une précondition échoue : `BLOCKED_WITH_EVIDENCE`, zéro écriture additionnelle.

## Paquet source

Utiliser le snapshot `repository/` du pack v0.3.1. Les patches sous `patches/` prouvent le replay local :

- patch 1 : diff canonique réutilisable sous réserve de base exacte;
- patch 2 : `PROOF_ONLY`, non publiable tel quel.

La méthode préférée est la copie directe depuis `repository/`, suivie de commits locaux, afin de préserver les octets.

## Étapes exactes

### T0 — Qualifier l’environnement

- vérifier `git --version`;
- vérifier l’identité Git;
- vérifier l’authentification au dépôt privé;
- vérifier la capacité de fetch et push sur une branche non protégée;
- ne créer aucune branche si la lecture distante échoue.

### T1 — Vérifier la base

```bash
git fetch --prune origin
test "$(git rev-parse origin/main)" = "f69b22d2bd09aa5eae96693acf501b2464c3be25"
git status --porcelain=v1
```

Résultat attendu : SHA exact et sortie status vide.

### T2 — Préparer la branche locale

Utiliser le helper du pack :

```bash
python3 prepare_bootstrap_branch.py \
  --checkout /chemin/vers/GitSpace \
  --candidate-repo /chemin/vers/pack/repository \
  --expected-base f69b22d2bd09aa5eae96693acf501b2464c3be25 \
  --branch bootstrap/canonical-corpus-v0.3 \
  --result /chemin/vers/bootstrap-result.json
```

Le helper ne pousse rien. Il doit produire :

```text
commit A : canon complet
commit B : RAGLite + manifeste(source_commit=A)
```

### T3 — Vérifier localement

- validator du corpus candidat `PASS`;
- commit B touche exactement six fichiers;
- `manifest.source_commit = A`;
- les cinq projections égalent byte-for-byte les sources de A;
- tous les `git hash-object` sont enregistrés;
- aucun fichier produit;
- `git diff origin/main..HEAD` ne contient aucune suppression non prévue hors remplacement de `README.md`.

### T4 — Revue pré-push

Un reviewer en lecture seule inspecte :

- parent de A;
- portée de A;
- portée de B;
- hashes;
- absence de référence aux blobs orphelins;
- absence d’effet sur `hermesclaw-ci`.

### T5 — Push non forcé

```bash
git push --set-upstream origin bootstrap/canonical-corpus-v0.3
```

Aucun `--force`.

### T6 — Vérification distante

- fetch de la branche poussée;
- comparaison SHA A/B attendus;
- comparaison `git ls-tree -r` et blobs;
- vérification que `main` et `hermesclaw-ci` sont inchangés;
- fermeture immédiate en cas de divergence.

### T7 — Pull request brouillon

Titre :

```text
docs: bootstrap the canonical GitSpace corpus
```

Le corps décrit :

- le remplacement du README de staging uniquement sur la branche proposée;
- la préservation de l’historique;
- l’absence de code produit;
- l’absence d’effet sur `hermesclaw-ci`;
- le protocole deux commits;
- le statut `PARTIALLY_VERIFIED`;
- les reviewers requis.

## Evidence Bundle attendu

```text
transport-environment.json
remote-before.json
candidate-validation.json
commit-a.json
commit-b.json
local-blobs.sha256
remote-after.json
remote-blob-comparison.json
branch-diff.txt
pr.json
reviews/
terminal-result.json
```

## Rollback

Avant push : supprimer uniquement la branche locale.

Après push avant merge : fermer la PR et supprimer uniquement `bootstrap/canonical-corpus-v0.3`.

Ne jamais supprimer `hermesclaw-ci` et ne jamais réécrire `main`.

## Critères de terminaison

`PARTIALLY_VERIFIED` si la branche et la PR existent mais les revues ne sont pas fermées.

`PROVEN` pour le bootstrap seulement si :

- tous les blobs distants égalent les fichiers locaux;
- A et B respectent leur portée;
- le manifeste référence le vrai A;
- les trois revues indépendantes passent;
- le propriétaire accepte le merge;
- le RAGLite du Projet ChatGPT est remplacé atomiquement depuis le commit accepté.

Sinon : `BLOCKED_WITH_EVIDENCE`.
