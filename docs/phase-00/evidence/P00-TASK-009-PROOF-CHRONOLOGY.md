---
evidence_id: GS-EVIDENCE-P00-TASK-009-PROOF-CHRONOLOGY
subject: P00-TASK-009
status: GREEN_VERIFIED_PRE_REVIEW
updated: 2026-08-14
---
# P00-TASK-009 — Chronologie de preuve du verdict historique

## Finding

**EVIDENCE:** le scoring Task 9 marquait initialement `regression_free=true` au moment où le verdict historique était émis.

À cet instant :

- le run natif avait observé son résultat fonctionnel et son cleanup;
- l’EvidenceBundle n’était pas encore construit;
- le replay n’avait pas encore eu lieu;
- aucune vérification indépendante n’avait eu lieu;
- aucun artefact de non-régression n’était persisté.

Le gate `regression_free`, non compensable dans `gs-verdict`, était donc auto-attribué sans provenance.

## RED

```text
commit: 7cd027436d779428bc90af7e2f25ff1359af1611
workflow run: 31790953822
job: 94737496727
checkout: exact detached head
permissions: contents: read
result: failure attendue
```

Le nouveau test :

```text
historical_verdict_does_not_self_award_regression_proof
```

échouait après que tous les contrats antérieurs eurent passé. Le message observé était :

```text
historical verdict self-awarded regression_free without a persisted regression proof
```

## Correction

Le scoring historique fixe désormais :

```text
regression_free = false
```

Le verdict expose donc `regression` dans l’extension déterministe `gitspace.verdict.failed_gates`.

Cette correction ne transforme pas une absence de preuve en échec fonctionnel. Elle maintient simplement le gate ouvert jusqu’à une vérification ultérieure capable de fournir une preuve de non-régression.

Le replay reproduit exactement ce verdict historique; il ne le réécrit pas et ne s’accorde pas rétroactivement le gate de régression.

## GREEN

```text
commit: bebd21608eb5e718c8ca010d5cda2069799a4116
Task 9 workflow run: 31791708102
Task 9 job: 94739850064
checkout: exact detached head
permissions: contents: read
Task 9 conclusion: success
all eight Phase 00 workflows at this head: success
```

Les preuves fraîches couvrent :

- `regression_free=false` dans le verdict historique PASS;
- présence du gate `regression` dans `failed_gates`;
- replay byte-identical du verdict corrigé;
- cinq classifications inchangées;
- false-DONE du scénario FAIL inchangé;
- read-only replay, substitutions sémantiques et provenance multi-commit toujours verts;
- workspace complet, Clippy `-D warnings`, rustfmt, locked metadata et clean-tree verts.

## Limites et risques résiduels

- **LIMIT:** Task 9 ne produit pas encore de verdict de promotion post-CI; le gate de régression reste donc volontairement ouvert dans le verdict historique.
- **UNKNOWN:** la granularité canonique future de `obligation_coverage` entre obligations visibles, protégées et runtime n’est pas définie par un registre d’obligations typé dans M0. Aucun changement de sémantique n’est introduit ici.
- **BLOCKED:** aucune revue par une identité séparée n’est encore enregistrée.
- **BLOCKED:** aucun merge signé, replay frais sur `main`, promotion canonique ou RAGLite byte-identical n’est encore disponible.

## Status

`P00-TASK-009` reste `PARTIALLY_VERIFIED` / `GREEN_VERIFIED_PRE_REVIEW`.
