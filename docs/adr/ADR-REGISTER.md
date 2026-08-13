---
doc_id: GS-ADR-REGISTER
title: GitSpace — Architecture Decision Register
authority: DECISION_REGISTER
status: ACTIVE
version: 0.3.1
updated: 2026-08-13
---

# GitSpace — ADR Register

## Règles

- Une décision est `ACCEPTED` seulement après approbation propriétaire explicite ou inscription canonique autorisée.
- Une décision réversible de pilote utilise `TDR`, pas `ADR`.
- Une entrée superseded reste visible.
- Les conséquences négatives sont conservées.
- Aucun agent d’exécution ne modifie le statut d’une ADR.

## Architecture decisions

### ADR-0001 — Native Software World Engine

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** GitSpace possède un modèle du monde logiciel natif. Git et les forges sont des périphéries.
- **Alternative rejetée :** forge agentisée comme noyau.
- **Preuve future :** comparer l’approche native à une forge agentisée.

### ADR-0002 — Rust principal, sans mono-langage dogmatique

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** Rust porte principalement le noyau de confiance; TypeScript, Python et d’autres langages restent possibles aux frontières appropriées.
- **Preuve future :** qualifier la frontière Rust/Python.

### ADR-0003 — Souveraineté humaine

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** l’humain conserve intention, valeurs, budget, risque irréversible et acceptation comportementale.

### ADR-0004 — AgentProcess contributeur natif

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** les contributeurs techniques natifs sont des processus agentiques avec identité, contexte, capabilities, budget et état durable.

### ADR-0005 — Faux DONE cible zéro

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** un agent ne se déclare pas lui-même terminé; terminaison par obligations, preuves, replay et vérification indépendante.

### ADR-0006 — Mémoire hiérarchique et quarantinée

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** toute mémoire possède type, provenance, portée, fraîcheur et statut; une base vectorielle n’est pas la vérité.

### ADR-0007 — Transformations sémantiques avant patches textuels

- **Statut : `ACCEPTED_DIRECTION_REQUIRES_QUALIFICATION`**
- **Décision :** privilégier symboles, AST et opérations typées; conserver le patch textuel comme compatibilité.

### ADR-0008 — RAGLite Markdown

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** cinq fichiers servent de mémoire mobile; après bootstrap ils sont une projection du dépôt.

### ADR-0009 — C0 Native Evaluation Foundry hybride

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** Evaluation IR GitSpace souverain, adaptateurs externes remplaçables et Seed Suite native initiale de 32 tâches.

### ADR-0010 — ChatGPT planifie; exécuteurs en aval

- **Statut : `ACCEPTED_OWNER`**
- **Décision :** ChatGPT dans le Projet GitSpace maintient recherche, canon et plans; Claude Code, Codex et autres agents restent des exécuteurs remplaçables.

## Technical decisions — Phase 00

### TDR-P00-001-AMENDED — Frontière Rust/Python et toolchains

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** Rust pour l’autorité; Python pour les adaptateurs. Les versions exactes sont verrouillées après qualification fraîche.

### TDR-P00-002 — Dimensions non compensables

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** sécurité, autorité, intégrité, portée et nettoyage ne sont jamais moyennés.

### TDR-P00-003 — QA indépendante obligatoire

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** aucune tâche native ne devient active sans QA indépendante ou procédure expedited explicitement justifiée.

### TDR-P00-004 — Journal local + CAS pour M0

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** premier vertical slice avec journal append-only et CAS local reconstructible.

### TDR-P00-005-AMENDED — Harness remplaçable

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** aucun fournisseur n’est canonique; le harness est choisi et enregistré par paquet.

### TDR-P00-006 — Dépôt cible

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** `leon36000/GitSpace` reçoit le canon complet.

### TDR-P00-007-AMENDED — Provenance RAGLite

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** chaque projection porte commit source, digests et mapping source/projection.

### TDR-P00-008 — Paire canon/projection

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** un commit canonique X est suivi d’un commit projection Y avec `manifest.source_commit = X`.
- **Raison :** éviter toute auto-référence impossible.

### TDR-P00-009 — Packetisation juste-à-temps

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** le plan maître n’est pas exécutable; chaque tâche reçoit un paquet exact depuis un commit frais.

### TDR-P00-010 — Résolution sûre du dépôt de staging

- **Statut : `EXECUTED_PENDING_OWNER_ACCEPTANCE`**
- **Décision :** branche dédiée et PR; préserver `hermesclaw-ci` et l’historique.
- **Evidence :** PR #1, base `f69b22d...`, A `488fd399...`, B `08a38c43...`.
- **Reste à fermer :** décision propriétaire de merge.

### TDR-P00-011 — Transport canonique byte-preserving

- **Statut : `PILOT_ACCEPTED_WITH_EVIDENCE`**
- **Décision :** publier par contenu UTF-8 direct ou filesystem authentifié, trees/blobs vérifiés et comparaison distante; interdire la transcription manuelle base64.
- **Evidence négative :** plusieurs blobs orphelins divergents pendant les probes.
- **Evidence positive :** A/B construits depuis blobs identifiés; cinq projections réutilisent les blobs sources.

### TDR-P00-012 — Projection après clôture d’état

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** lorsqu’une publication change l’état canonique `00/02/04`, créer un commit de clôture C puis un commit de projection D avec `source_commit = C`.
- **Raison :** la projection finale doit refléter l’état de la PR, pas seulement l’état prépublication.

## Décisions différées

- Temporal versus moteur durable alternatif;
- Neon versus Postgres local/auto-hébergé;
- SonarQube et Fallow pour le code produit;
- AMD optimizations;
- moteur de politique;
- sandbox;
- backend workspace;
- licence.

Elles seront décidées par dossier de recherche et expérience, pas par préférence implicite.
