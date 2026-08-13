---
doc_id: GS-ADR-REGISTER
title: GitSpace — Architecture Decision Register
authority: DECISION_REGISTER
status: ACTIVE
version: 0.3.0
updated: 2026-08-13
---

# GitSpace — ADR Register

## Règles

- Une décision est `ACCEPTED` seulement après approbation propriétaire explicite ou inscription canonique autorisée.
- Une décision réversible de pilote utilise `TDR`, pas `ADR`.
- Une entrée superseded reste dans le registre.
- Les conséquences négatives sont conservées.
- Aucun agent d’exécution ne modifie le statut d’une ADR.

## Architecture decisions

### ADR-0001 — Native Software World Engine

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** GitSpace possède un modèle du monde logiciel natif. Git et les forges sont des périphéries.
- **Alternatives rejetées :** fork profond de Forgejo; plan de contrôle uniquement autour de Git.
- **Conséquences positives :** primitives réellement agent-native; état durable; changement sémantique.
- **Coûts/risques :** nouveau modèle d’objets; compatibilité à construire.
- **Preuve requise :** Phase 00 doit comparer l’approche native à une forge agentisée.

### ADR-0002 — Rust principal, sans mono-langage dogmatique

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** Rust est le langage principal du noyau de confiance.
- **Utilisations prévues :** état, politiques, capacités, changement, preuve, protocole, indexation performante.
- **Exceptions :** TypeScript pour UI; Python pour adaptateurs et recherche; autres langages si mieux adaptés.
- **Risque :** complexité d’intégration et disponibilité de bibliothèques.
- **Preuve requise :** frontière Rust/Python qualifiée en Phase 00.

### ADR-0003 — Souveraineté humaine

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** l’humain conserve intention, valeurs, budget, risque irréversible et acceptation comportementale.
- **Conséquence :** les questions techniques réversibles sont résolues par recherche et expérience.
- **Interdit :** forcer le propriétaire à vérifier du code.

### ADR-0004 — AgentProcess comme contributeur natif

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** les contributeurs techniques natifs sont des processus agentiques avec identité, contexte, capabilities, budget et état durable.
- **Conséquence :** aucun compte humain simulé n’est nécessaire dans le noyau.

### ADR-0005 — Faux DONE cible zéro

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** un agent ne se déclare pas lui-même terminé.
- **Conséquence :** terminaison par obligations, preuves, replay et vérification indépendante.
- **Échec acceptable :** `BLOCKED_WITH_EVIDENCE`.
- **Échec interdit :** réussite supposée faute de preuve.

### ADR-0006 — Mémoire hiérarchique et quarantinée

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-11**
- **Décision :** toute mémoire possède type, provenance, portée, fraîcheur et statut.
- **Cycle :** `RAW → QUARANTINED → VERIFIED → ACCEPTED → STALE/REVOKED`.
- **Interdit :** mémoire vectorielle comme vérité ou capability.

### ADR-0007 — Transformations sémantiques avant patches textuels

- **Statut : `ACCEPTED_DIRECTION_REQUIRES_QUALIFICATION`**
- **Date : 2026-08-11**
- **Décision :** privilégier symboles, AST et opérations typées.
- **Compatibilité :** patch textuel conservé comme mode dégradé.
- **Preuve requise :** expériences multilingues Phase 00/03.

### ADR-0008 — RAGLite Markdown pour le Projet ChatGPT

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-12**
- **Décision :** cinq fichiers compacts servent de mémoire projet mobile.
- **Conséquence :** mémoire chaude limitée et routage documentaire.
- **Contrainte :** le RAGLite devient une projection du dépôt après bootstrap.

### ADR-0009 — C0 Native Evaluation Foundry hybride

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-12**
- **Décision :**
  - Evaluation IR GitSpace souverain;
  - adaptateurs externes remplaçables;
  - Seed Suite native initiale de 32 tâches.
- **Alternatives rejetées :** simple agrégation de benchmarks; suite uniquement propriétaire.
- **Gate :** quinze critères de sortie Phase 00.

### ADR-0010 — ChatGPT planifie; les exécuteurs restent en aval

- **Statut : `ACCEPTED_OWNER`**
- **Date : 2026-08-12**
- **Décision :** ChatGPT dans le Projet GitSpace est l’architecte-chercheur, le mainteneur du canon et l’auteur des plans.
- **Conséquence :** Claude Code, Codex ou tout autre agent peuvent exécuter, mais ne sont ni le planificateur canonique ni la mémoire.
- **Interdit :** coupler le plan maître à un fournisseur.

## Technical decisions — Phase 00

### TDR-P00-001-AMENDED — Frontière Rust/Python et toolchains

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** Rust pour l’autorité; Python pour les adaptateurs.
- **Amendement :** aucune version exacte n’est canonique avant qualification fraîche.
- **Candidats observés :** Rust 1.97.1; Python 3.12.
- **Expériences :** `EXP-P00-010`, `EXP-P00-011`, `EXP-P00-012`.

### TDR-P00-002 — Dimensions non compensables

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** sécurité, autorité, intégrité, portée et nettoyage ne sont jamais moyennés.

### TDR-P00-003 — QA indépendante obligatoire

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** aucune tâche native ne devient active sans QA indépendante ou procédure expedited explicitement justifiée.

### TDR-P00-004 — Journal local + CAS pour M0

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** premier vertical slice avec journal append-only et CAS local reconstructible.
- **Risque :** extension ultérieure vers un stockage distribué.

### TDR-P00-005-AMENDED — Harness d’exécution remplaçable

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** aucun fournisseur n’est canonique. Le harness est choisi et enregistré par paquet.
- **Supersedes :** Claude Code comme harness initial imposé.

### TDR-P00-006 — Dépôt cible

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** `leon36000/GitSpace` reçoit le canon complet.
- **État :** conflit de staging enregistré dans `GS-CONFLICT-REPO-001`.

### TDR-P00-007-AMENDED — Provenance RAGLite

- **Statut : `PILOT_ACCEPTED`**
- **Décision :** la projection porte commit source, digests et date.

### TDR-P00-008 — Publication RAGLite en deux commits

- **Statut : `PILOT_ACCEPTED`**
- **Date : 2026-08-13**
- **Décision :**
  1. commit A contient le canon;
  2. commit B contient la projection et référence A.
- **Raison :** éviter l’auto-référence impossible d’un commit vers son propre SHA.
- **Test :** régénérer la projection depuis A et comparer bit-à-bit à B.

### TDR-P00-009 — Packetisation juste-à-temps

- **Statut : `PILOT_ACCEPTED`**
- **Date : 2026-08-13**
- **Décision :** le plan maître n’est pas exécutable. Chaque tâche reçoit un paquet exact depuis un commit frais.
- **Raison :** éviter les chemins, versions et interfaces spéculatifs.

### TDR-P00-010 — Résolution sûre du dépôt de staging

- **Statut : `PROPOSED_SAFE_RESOLUTION`**
- **Date : 2026-08-13**
- **Décision proposée :** branche dédiée, deux commits, pull request; préserver `hermesclaw-ci` et l’historique.
- **Interdit sans décision :** supprimer la branche ou réécrire l’historique.
