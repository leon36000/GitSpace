---
doc_id: GS-CONFLICT-REGISTER
title: GitSpace — Conflict Register
authority: CONFLICT_REGISTER
status: ACTIVE
version: 0.3.3
updated: 2026-08-13
---

# GitSpace — Conflict Register

## Règle

Un conflit n’est pas résolu en supprimant la source perdante. La source la plus autoritaire devient active; l’autre est conservée comme mémoire négative ou historique.

## Conflits

### GS-CONFLICT-DOC-001 — RAGLite v0.2.1 versus correction v0.2.2

- **Autorité :** correction explicite du propriétaire et ADR-0010.
- **Résolution :** v0.3 sépare propriétaire, ChatGPT planificateur, exécuteurs et reviewers.
- **Statut : `RESOLVED`**.

### GS-CONFLICT-PLAN-001 — Plan maître versus overlay fournisseur

- **Résolution :** `GS-P00-PLAN-001` v0.4.0 est executor-neutral; le prototype fournisseur est archivé.
- **Statut : `RESOLVED_WITH_EVIDENCE`**.

### GS-CONFLICT-REPO-001 — GitSpace versus staging HermesClaw

- **Observation :** `main@f69b22d...` contient un README de staging; `hermesclaw-ci` est une branche distincte et active.
- **Contrôle :** branche bootstrap, historique préservé, PR #1 brouillon, aucune modification de `hermesclaw-ci`.
- **Reste :** décision propriétaire sur le merge.
- **Statut : `OPEN_OWNER_DECISION`**.

### GS-CONFLICT-RAG-001 — Manifeste auto-référentiel

- **Contre-exemple :** un commit ne peut pas contenir son propre SHA stable.
- **Résolution :** paire canon X / projection Y; le manifeste porte l’identité exacte de la paire active.
- **Evidence :** A→B, C→D et paire de correction de revue.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-TOOLCHAIN-001 — Pins exacts versus qualification fraîche

- **Résolution :** Rust 1.97.1 et Python 3.12 restent candidats; Task 1 verrouille après revalidation.
- **Statut : `RESOLVED_AS_PILOT`**.

### GS-CONFLICT-STATE-001 — Corpus local versus canon publié

- **Résolution partielle :** corpus publié sur branche et PR #1 ouverte.
- **Reste :** merge propriétaire et remplacement atomique des sources ChatGPT.
- **Statut : `PARTIALLY_RESOLVED`**.

### GS-CONFLICT-TRANSPORT-001 — Transcription manuelle versus intégrité

- **Evidence négative :** blobs orphelins divergents; aucun tree ou commit ne les référence.
- **Résolution :** UTF-8 direct, trees/blobs identifiés, projections par réutilisation des blobs sources.
- **Statut : `CLOSED_FOR_BOOTSTRAP_WITH_EVIDENCE`**.
- **Mémoire négative :** base64 manuel reste interdit.

### GS-CONFLICT-PATCH-001 — Patch B synthétique versus vrai SHA A

- **Résolution :** le vrai A a été créé, puis B construit avec `source_commit=A`; le patch synthétique n’a pas été utilisé.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-CURRENT-STATE-001 — État A/B devenu périmé après publication

- **Finding :** `00/02/04` décrivaient encore un transport bloqué après ouverture de la PR.
- **Résolution :** C `4802c26f...`, D `0c6ed111...`, puis paire de correction de revue.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-COUNT-001 — Décompte 19 versus 20 documents

- **Finding :** le rapport de vérification ajouté en C portait le corpus canonique à 20 documents, tandis que `02` indiquait encore 19.
- **Résolution :** `02` v0.3.4 et README corrigés.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-EPISTEMIC-001 — Type `EVIDENCE_SYNTHESIS` non enregistré

- **Finding :** `RES-P00-030` utilisait un type absent du protocole.
- **Résolution :** remplacement par `EVIDENCE`; la décision `REJECT` reste inchangée.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

## Conflit bloquant restant

Seule la décision propriétaire sur la PR #1 bloque le changement d’autorité de `main`. Les revues rôle-séparées ne sont pas indépendantes par identité; cette limite ne doit pas être masquée.
