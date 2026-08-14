---
doc_id: GS-CONFLICT-REGISTER
title: GitSpace — Conflict Register
authority: CONFLICT_REGISTER
status: ACTIVE
version: 0.4.1
updated: 2026-08-14
---

# GitSpace — Conflict Register

## Règle

Un conflit n’est pas résolu en supprimant la source perdante. La source plus autoritaire devient active; la source perdante reste accessible comme mémoire négative ou historique.

## Conflits historiques fermés

- `GS-CONFLICT-DOC-001` — RAGLite v0.2.1 versus correction v0.2.2 — `CLOSED_WITH_EVIDENCE`.
- `GS-CONFLICT-PLAN-001` — plan maître versus overlay fournisseur — `CLOSED_WITH_EVIDENCE`.
- `GS-CONFLICT-REPO-001` — GitSpace versus staging HermesClaw — `CLOSED_WITH_EVIDENCE`; `hermesclaw-ci` reste préservée et hors scope.
- `GS-CONFLICT-RAG-001` — manifeste Git auto-référentiel — `CLOSED_WITH_EVIDENCE`; publication par paire canon/projection.
- `GS-CONFLICT-TOOLCHAIN-001` — pins toolchain prématurés — `CLOSED_WITH_EVIDENCE`; Task 1 a qualifié les versions initiales.
- `GS-CONFLICT-STATE-001` — corpus local versus canon publié — `CLOSED_WITH_EVIDENCE`; le dépôt fusionné est le canon éditable.
- `GS-CONFLICT-TRANSPORT-001` — transcription manuelle versus intégrité — `CLOSED_FOR_BOOTSTRAP_WITH_EVIDENCE`; base64 manuel reste interdit.
- `GS-CONFLICT-PATCH-001` — patch synthétique versus vrai parent — `CLOSED_WITH_EVIDENCE`.
- `GS-CONFLICT-CURRENT-STATE-001` — état de publication périmé — `CLOSED_WITH_EVIDENCE`; état et projection sont séparés.
- `GS-CONFLICT-COUNT-001` — décompte documentaire incohérent — `CLOSED_WITH_EVIDENCE`.
- `GS-CONFLICT-EPISTEMIC-001` — type épistémique non enregistré — `CLOSED_WITH_EVIDENCE`.

## GS-CONFLICT-P00-IR-001 — Boucle de hachage RunManifest ↔ EvidenceBundle

### Découverte

La packetisation de `P00-TASK-009` a été la première matérialisation réelle du couple `EvalRunManifest` / `EvidenceBundle`. Le contrat v1 imposait simultanément :

```text
EvalRunManifest.artifacts.evidence_bundle
  → CAS digest du EvidenceBundle complet

EvidenceBundle.run_manifest_digest
  → digest du EvalRunManifest complet
```

Avec deux objets immuables adressés par contenu, chacun exigeait donc le digest final de l’autre avant de pouvoir être construit. Aucun ordre de construction déterministe n’existait sans introduire un faux fixed point cryptographique ou une normalisation non déclarée.

### RED

PR #37, fermée sans merge :

```text
workflow 31778117998
job      94697773347
```

Le nouveau test d’acyclicité a échoué exactement parce que `run_manifest_digest` restait obligatoire; tous les anciens tests de schéma continuaient de passer.

### Résolution

Conserver un seul lien d’autorité :

```text
EvalRunManifest → EvidenceBundle
```

Le champ retour `EvidenceBundle.run_manifest_digest` a été supprimé du schéma v1, du type Rust et des exemples de parité. L’objet restant fermé (`additionalProperties=false`), l’ancien champ est désormais explicitement rejeté.

Cette correction intervient avant toute émission réelle d’un EvidenceBundle par la Foundry. Le RunManifest conserve l’URI CAS du bundle, qui fixe déjà les octets complets du bundle; celui-ci conserve `run_id`, `task_id`, `environment_digest`, `commit_sha` et ses références d’artefacts.

### Vérification GREEN

PR #38 a été fusionnée par squash signé :

```text
merge ce0c58d9012b723fbe276a4a33f3f7598dd976aa
tree  600a3955ac4d65dc0b3b081220b7837d6a93fcc5
verification.verified = true
```

Preuves pré-merge sur la tête exacte `0303c5f75eab054fe59e8889d36dac806af1f790` :

```text
Task 2 schema workflow 31778488400 / job 94698909403 — PASS
Task 4 parity workflow 31778488420 / job 94698909503 — PASS
```

Gates fermés :

- schémas Draft 2020-12 — PASS;
- ancien champ retour rejeté — PASS;
- corpus Python — PASS;
- parité Rust — PASS;
- metadata `--locked` — PASS;
- workspace Rust complet contre l’IR révisé — PASS;
- Clippy — PASS;
- rustfmt — PASS;
- dépôt propre — PASS.

Le workflow Task 4 est maintenant déclenché par toute modification de `schemas/v1/**` et exécute la suite workspace complète, empêchant une future dérive schéma ↔ types ↔ consommateurs.

### Statut

`CLOSED_WITH_EVIDENCE`.

`P00-TASK-009` n’est plus bloquée par ce conflit et doit être redérivée depuis le `main` contenant ce correctif.

## Blocages documentaires actifs

Aucun conflit documentaire connu ne bloque actuellement la packetisation de `P00-TASK-009`. Toute nouvelle contradiction découverte pendant l’intégration doit produire un nouveau RED ou un `BLOCKED_WITH_EVIDENCE`, jamais un contournement implicite.
