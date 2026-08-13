---
doc_id: GS-CONFLICT-REGISTER
title: GitSpace — Conflict Register
authority: CONFLICT_REGISTER
status: ACTIVE
version: 0.3.1
updated: 2026-08-13
---

# GitSpace — Conflict Register

## Règle

Un conflit n’est pas résolu en supprimant la source perdante. La source plus autoritaire devient active; l’autre est conservée comme mémoire négative ou historique.

## Conflits

### GS-CONFLICT-DOC-001 — RAGLite v0.2.1 versus correction v0.2.2

- **Sources :**
  - `02`/`04` v0.2.1 centrés sur l’exécution Claude Code;
  - correction v0.2.2 enregistrant ChatGPT comme planificateur.
- **Autorité appliquée :** correction explicite du propriétaire, puis ADR-0010.
- **Résolution :** v0.3.0 reprend la séparation des rôles; les sections Claude Code du plan v0.2 sont `STALE`.
- **Statut : `RESOLVED`**.

### GS-CONFLICT-PLAN-001 — Plan maître versus overlay fournisseur

- **Sources :**
  - `GS-P00-PLAN-001` v0.1 executor-neutral;
  - v0.2 contenant `CLAUDE_CODE`, `EXEC-E0`, `.claude/` et `dontAsk`.
- **Autorité appliquée :** ADR-0010 et instruction propriétaire.
- **Résolution :** `GS-P00-PLAN-001` v0.3.0 est executor-neutral. Les instructions fournisseur appartiennent uniquement à des paquets ou annexes de handoff.
- **Preuve :** scan de termes interdits.
- **Statut : `RESOLVED_PENDING_REPOSITORY_PUBLICATION`**.

### GS-CONFLICT-REPO-001 — Dépôt GitSpace versus staging HermesClaw

- **Observation antérieure :** dépôt déclaré vide le 2026-08-12.
- **Observation fraîche :**
  - `main` = `f69b22d2bd09aa5eae96693acf501b2464c3be25`;
  - README « Private CI staging repository »;
  - branche `hermesclaw-ci` = `91f55525b231116fd431430f46c87667e5c1f140` lors de la dernière vérification;
  - la branche a avancé au moins deux fois pendant la session, dont un rafraîchissement d’artefact puis la suppression d’un manifeste de preuve abandonné.
- **Conflit :** le dépôt cible de GitSpace porte actuellement une identité de staging pour un autre projet.
- **Résolution sûre proposée :** branche dédiée et pull request, sans suppression.
- **Statut : `OPEN_BLOCKING_DIRECT_MAIN_WRITE`**.

### GS-CONFLICT-RAG-001 — Manifeste auto-référentiel

- **Ancienne règle :** le manifeste RAGLite du premier commit devait contenir le SHA de ce même commit.
- **Contre-exemple :** le SHA dépend du contenu du manifeste; l’inscription du SHA change donc le SHA.
- **Résolution :**
  - commit A : sources canoniques;
  - commit B : projection + manifeste référençant A.
- **Décision :** TDR-P00-008.
- **Statut : `RESOLVED`**.

### GS-CONFLICT-TOOLCHAIN-001 — Pins exacts versus qualification fraîche

- **Ancienne formulation :** Rust 1.97.1 et Python 3.12.13 étaient déjà acceptés.
- **Nouvelle autorité :** TDR-P00-001-AMENDED.
- **Evidence :**
  - Rust 1.97.1 est un candidat officiel corrigeant une miscompilation;
  - Inspect Evals recommande 3.11/3.12;
  - Harbor requiert actuellement Python >=3.12;
  - Python 3.12.13 est source-only et en phase security-only.
- **Résolution :** versions candidates dans l’Atlas; lock exact seulement après qualification.
- **Statut : `RESOLVED_AS_PILOT`**.

### GS-CONFLICT-STATE-001 — Corpus local versus canon publié

- **Situation :** le corpus v0.3.0 est produit et vérifié localement, mais absent du dépôt.
- **Règle :** un artifact local n’est pas canonique par simple existence.
- **Résolution :** statut `COMMIT_READY_NOT_PUBLISHED`; publication par PR.
- **Statut : `OPEN_EXPECTED`**.


### GS-CONFLICT-TRANSPORT-001 — Transcription manuelle versus intégrité des octets

- **Probe :** huit appels `create_blob` ont créé des objets Git non référencés.
- **Résultat :** six SHA correspondaient aux fichiers locaux; deux SHA divergeaient.
- **Cause :** un gros payload encodé a été copié à travers une frontière conversationnelle au lieu d’être lu directement depuis le filesystem.
- **Portée distante :** aucun tree, commit, ref, branche ou pull request n’a été créé.
- **Résolution :** interdire la transcription manuelle; exiger un checkout local authentifié ou un connecteur acceptant un chemin de fichier local avec vérification des hashes.
- **Statut : `OPEN_BLOCKING_REMOTE_PUBLICATION`**.

### GS-CONFLICT-PATCH-001 — Patch B synthétique versus SHA A distant

- **Situation :** le replay local produit un commit A synthétique puis un patch B dont le manifeste référence ce SHA A.
- **Contre-exemple :** appliqué sur le vrai parent distant, le commit A reçoit un autre SHA; le patch B local référencerait alors le mauvais commit.
- **Résolution :** le patch A peut servir de représentation du diff; le patch B est `PROOF_ONLY`. Après le vrai commit A, la projection et son manifeste sont régénérés puis committés comme B.
- **Statut : `RESOLVED_IN_PLAN_PENDING_REMOTE_EXECUTION`**.
