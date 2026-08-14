---
doc_id: GS-CONFLICT-REGISTER
title: GitSpace — Conflict Register
authority: CONFLICT_REGISTER
status: ACTIVE
version: 0.4.0
updated: 2026-08-14
---

# GitSpace — Conflict Register

## Règle

Un conflit n’est pas résolu en supprimant la source perdante. La source la plus autoritaire devient active; l’autre est conservée comme mémoire négative ou historique.

## Conflits historiques fermés

### GS-CONFLICT-DOC-001 — RAGLite v0.2.1 versus correction v0.2.2

- **Autorité :** correction explicite du propriétaire et ADR-0010.
- **Résolution :** v0.3 sépare propriétaire, ChatGPT planificateur, exécuteurs et reviewers.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-PLAN-001 — Plan maître versus overlay fournisseur

- **Résolution :** `GS-P00-PLAN-001` est executor-neutral; le prototype fournisseur est archivé comme mémoire négative.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-REPO-001 — GitSpace versus staging HermesClaw

- **Finding historique :** le dépôt cible avait initialement un README de staging et une branche `hermesclaw-ci` distincte.
- **Résolution :** bootstrap GitSpace fusionné sur `main` sans réécriture; `hermesclaw-ci` reste préservée et hors scope.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-RAG-001 — Manifeste auto-référentiel

- **Contre-exemple :** un commit ne peut pas contenir son propre SHA stable.
- **Résolution :** paire canon X / projection Y; le manifeste porte l’identité exacte de la paire active.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-TOOLCHAIN-001 — Pins exacts versus qualification fraîche

- **Résolution :** Task 1 a qualifié et verrouillé les toolchains; toute future requalification reste fraîche et versionnée.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-STATE-001 — Corpus local versus canon publié

- **Résolution :** le dépôt fusionné est le canon éditable; RAGLite est une projection byte-identical liée au commit source.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-TRANSPORT-001 — Transcription manuelle versus intégrité

- **Evidence négative :** des blobs orphelins divergents ont réfuté la transcription manuelle de payloads encodés.
- **Résolution :** objets Git vérifiés, UTF-8 direct et réutilisation exacte des blobs sources pour RAGLite.
- **Statut : `CLOSED_FOR_BOOTSTRAP_WITH_EVIDENCE`**.
- **Mémoire négative permanente :** transport base64 manuel interdit.

### GS-CONFLICT-PATCH-001 — Patch synthétique versus vrai parent

- **Résolution :** les projections sont générées depuis le vrai commit canonique; aucun patch synthétique lié à un parent fictif n’est publié.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-CURRENT-STATE-001 — État de publication périmé

- **Résolution :** chaque changement d’état durable est suivi d’une projection RAGLite séparée.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-COUNT-001 — Décompte documentaire incohérent

- **Résolution :** décompte corrigé pendant le bootstrap et contrôlé par les revues documentaires.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

### GS-CONFLICT-EPISTEMIC-001 — Type épistémique non enregistré

- **Résolution :** `EVIDENCE_SYNTHESIS` supprimé au profit du type enregistré `EVIDENCE`.
- **Statut : `CLOSED_WITH_EVIDENCE`**.

## Conflit Phase 00 actif

### GS-CONFLICT-P00-IR-001 — Boucle de hachage RunManifest ↔ EvidenceBundle

- **Découverte :** packetisation de `P00-TASK-009`, première matérialisation réelle du RunManifest et de l’EvidenceBundle.
- **Contrat actuel :**
  - `EvalRunManifest.artifacts.evidence_bundle` exige une URI CAS vers le bundle;
  - `EvidenceBundle.run_manifest_digest` exige le digest du manifest complet.
- **Contre-exemple :** avec deux objets immuables adressés par contenu, chacun dépend du digest final de l’autre; aucun ordre de construction déterministe n’existe sans chercher un fixed point cryptographique ou introduire une convention non déclarée.
- **RED :** PR #37, workflow `31778117998`, job `94697773347`; le nouveau test d’acyclicité échoue exactement parce que `run_manifest_digest` reste obligatoire.
- **Résolution proposée et réversible :** conserver un seul lien autoritaire `EvalRunManifest → EvidenceBundle` et retirer le lien retour. L’URI CAS du manifest fixe déjà les octets complets du bundle.
- **Compatibilité :** aucune instance Foundry réelle d’EvidenceBundle n’a encore été matérialisée; la correction intervient avant le premier vertical slice.
- **Gate :** Task 2 + Task 4 parity + workspace complet doivent repasser après correction; le champ supprimé doit être rejeté comme propriété inconnue.
- **Statut : `CORRECTION_UNDER_VERIFICATION`**.

## Blocage courant

`P00-TASK-009` reste `BLOCKED_WITH_EVIDENCE` jusqu’à fermeture de `GS-CONFLICT-P00-IR-001`. Aucun code du vertical slice n’est autorisé avant revalidation du schéma et des types Rust.
