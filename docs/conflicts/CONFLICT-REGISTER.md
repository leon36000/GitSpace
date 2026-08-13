---
doc_id: GS-CONFLICT-REGISTER
title: GitSpace — Conflict Register
authority: CONFLICT_REGISTER
status: ACTIVE
version: 0.3.2
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

- **Sources :** plan executor-neutral et overlay Claude Code.
- **Résolution :** `GS-P00-PLAN-001` v0.4.0 est executor-neutral; le prototype fournisseur est archivé.
- **Statut : `RESOLVED_WITH_EVIDENCE`**.

### GS-CONFLICT-REPO-001 — GitSpace versus staging HermesClaw

- **Observation :** `main@f69b22d...` contient un README de staging; `hermesclaw-ci` est une branche distincte et active.
- **Contrôle :** branche `bootstrap/canonical-corpus-v0.3`, historique préservé, PR #1 brouillon, aucune modification de `hermesclaw-ci`.
- **Reste :** décision propriétaire sur le merge.
- **Statut : `OPEN_OWNER_DECISION`**.

### GS-CONFLICT-RAG-001 — Manifeste auto-référentiel

- **Contre-exemple :** un commit ne peut pas contenir son propre SHA stable.
- **Résolution :** paire canon X / projection Y avec `source_commit=X`.
- **Evidence :** A `488fd399...` puis B `08a38c43...`.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-TOOLCHAIN-001 — Pins exacts versus qualification fraîche

- **Résolution :** Rust 1.97.1 et Python 3.12 restent candidats; Task 1 verrouille les versions après revalidation.
- **Statut : `RESOLVED_AS_PILOT`**.

### GS-CONFLICT-STATE-001 — Corpus local versus canon publié

- **Résolution partielle :** corpus publié sur la branche et PR #1 ouverte.
- **Reste :** merge propriétaire et remplacement atomique des sources ChatGPT.
- **Statut : `PARTIALLY_RESOLVED`**.

### GS-CONFLICT-TRANSPORT-001 — Transcription manuelle versus intégrité

- **Evidence négative :** plusieurs blobs orphelins ont divergé des fichiers visés; aucune branche ou commit ne les référence.
- **Résolution :** contenu UTF-8 direct, trees/blobs identifiés et vérification du diff.
- **Evidence positive :** A/B réels; cinq projections réutilisent exactement les blobs sources.
- **Statut : `CLOSED_FOR_BOOTSTRAP_WITH_EVIDENCE`**.
- **Mémoire négative :** base64 manuel reste interdit pour toute publication future.

### GS-CONFLICT-PATCH-001 — Patch B synthétique versus vrai SHA A

- **Ancienne situation :** le replay local produisait un SHA A synthétique.
- **Résolution :** le vrai A a été créé, puis B construit avec `source_commit=A`; le patch synthétique n’a pas été utilisé.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-CURRENT-STATE-001 — État prépublication versus PR réelle

- **Situation :** A/B décrivaient correctement la stratégie, mais `00/02/04` indiquaient encore transport bloqué et PR absente.
- **Résolution :** commit de clôture d’état C puis projection D conformément à TDR-P00-012.
- **Statut : `RESOLVED_PENDING_C_D_PUBLICATION`**.

## Conflits bloquants restants

Un seul choix bloque le changement d’autorité du dépôt : accepter ou refuser le merge de la PR #1. Aucun conflit restant n’autorise le démarrage de Task 1 avant merge.
