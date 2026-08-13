---
doc_id: GS-P00-BOOTSTRAP-PLAN-001
title: GitSpace — Canonical Repository Bootstrap Plan
status: EXECUTED_PENDING_OWNER_ACCEPTANCE
version: 0.3.1
updated: 2026-08-13
planner: CHATGPT_PROJECT_GITSPACE
target_repository: leon36000/GitSpace
base_commit: f69b22d2bd09aa5eae96693acf501b2464c3be25
product_code_allowed: false
---

# GitSpace — Bootstrap canonique du dépôt

## Goal

Publier le corpus canonique de GitSpace sans perdre l’historique de staging, sans code produit et sans dépendance à un exécuteur particulier.

## Architecture exécutée

```text
main@f69b22d...
  └─ A 488fd399... : corpus canonique initial
       └─ B 08a38c43... : projection RAGLite de A
            └─ C : clôture de l’état de publication
                 └─ D : projection RAGLite de C
```

Les SHA C/D sont établis lors de la clôture de cette session. La PR #1 suit la tête de branche.

## Non-scope respecté

- aucun crate Rust ou package Python;
- aucun prototype produit;
- aucun adaptateur ou benchmark;
- aucune CI produit;
- aucune licence;
- aucune suppression de `hermesclaw-ci`;
- aucune écriture directe sur `main`;
- aucun merge.

## Invariants

1. Le dépôt fusionné sera l’unique canon éditable.
2. Le RAGLite est une projection de lecture.
3. Chaque commit projection référence son parent canonique.
4. Les cinq projections sont byte-identical aux sources.
5. L’historique de staging reste accessible.
6. `hermesclaw-ci` reste intacte.
7. Aucun fichier ne prétend que le produit est implémenté.
8. Aucun fournisseur d’agent n’est canonique.
9. Les décisions acceptées ont une autorité.
10. Les préprints non reproduits restent expérimentaux.
11. Les versions exactes de toolchain attendent Task 1.
12. Le merge reste une décision propriétaire.

## Résultats par unité

### B1 — Consolidation

`PASS` : canon, état, Atlas, protocole et registres consolidés.

### B2 — Plan Phase 00

`PASS` : plan maître v0.4.0 executor-neutral avec 22 unités et packetisation obligatoire.

### B3 — Registres

`PASS` : ADR, risques, conflits, provenance, dépôt et transport publiés.

### B3.5 — Qualification transport

`PASS_FOR_BOOTSTRAP_WITH_EVIDENCE` : voie UTF-8/tree qualifiée; voie base64 rejetée.

### B4 — Commit A

`PASS` : A parent direct de `main`, 19 documents, zéro code produit.

### B5/B6 — Projection et commit B

`PASS` : B parent de A, manifeste `source_commit=A`, cinq blobs partagés, diff de six fichiers.

### B7 — Pull request

`PASS` : PR #1 brouillon, ouverte et mergeable.

### B8 — Revue indépendante

`OPEN` : trois axes de revue et décision propriétaire requis.

## Critères d’acceptation

Le bootstrap devient `PROVEN` seulement si :

- les revues indépendantes ne trouvent aucun défaut matériel ouvert;
- le propriétaire accepte le changement de rôle de `main`;
- la PR est fusionnée sans effet sur `hermesclaw-ci`;
- la projection finale est synchronisée dans le Projet ChatGPT;
- le SHA fusionné devient la base du premier paquet Phase 00.

## Rollback

Avant merge : fermer la PR et supprimer uniquement la branche bootstrap.

Après merge : revert explicite; ne jamais réécrire l’historique.

## Prochaine unité après merge

`P00-RESEARCH-ATLAS-001`, puis packetisation exacte de Task 1 depuis le commit fusionné.
