---
doc_id: GS-P00-BOOTSTRAP-PLAN-001
title: GitSpace — Canonical Repository Bootstrap Plan
status: ACCEPTED_PLAN_NOT_PUBLISHED
version: 0.3.0
updated: 2026-08-13
planner: CHATGPT_PROJECT_GITSPACE
target_repository: leon36000/GitSpace
base_commit: f69b22d2bd09aa5eae96693acf501b2464c3be25
product_code_allowed: false
---

# GitSpace — Bootstrap canonique du dépôt

## Goal

Publier le corpus canonique de GitSpace dans le dépôt cible sans perdre l’historique de staging existant, sans code produit et sans dépendance à un exécuteur particulier.

## Architecture de publication

Le bootstrap utilise deux commits sur une branche dédiée :

```text
main@f69b22d...
        │
        └── bootstrap/canonical-corpus-v0.3
              ├── commit A — corpus canonique complet
              └── commit B — projection RAGLite générée depuis A
```

`commit B` contient `RAGLITE-MANIFEST.yaml` avec `source_commit: <commit A>`. Il ne tente jamais de contenir son propre SHA.

## Non-scope

- aucun crate Rust;
- aucun package Python;
- aucun prototype du World Engine;
- aucun adaptateur;
- aucune benchmark task;
- aucune CI produit;
- aucun choix de licence;
- aucune suppression de `hermesclaw-ci`;
- aucune réécriture d’historique;
- aucune qualification d’agent d’exécution.

## État de base

```yaml
repository: leon36000/GitSpace
default_branch: main
base_commit: f69b22d2bd09aa5eae96693acf501b2464c3be25
base_readme_role: HERMESCLAW_CI_STAGING_PLACEHOLDER
preserved_branch:
  name: hermesclaw-ci
  last_observed_sha: 91f55525b231116fd431430f46c87667e5c1f140
  moving: true
  recheck_before_and_after_push: true
conflict: GS-CONFLICT-REPO-001
```

Le commit de base est conservé dans l’historique. La branche de staging n’est pas touchée.

## Arborescence — commit A

```text
GitSpace/
├── README.md
├── AGENTS.md
├── 00_GITSPACE_START_HERE.md
├── 01_GITSPACE_MASTER_CANON.md
├── 02_GITSPACE_NOW_DECISIONS_ROADMAP.md
├── 03_GITSPACE_RESEARCH_ATLAS.md
├── 04_GITSPACE_AGENT_PROTOCOL.md
├── docs/
│   ├── adr/ADR-REGISTER.md
│   ├── conflicts/CONFLICT-REGISTER.md
│   ├── history/GS-CC-PROTOTYPE-STATUS.md
│   ├── phase-00/
│   │   ├── GS-P00-SPEC-001.md
│   │   ├── GS-P00-PLAN-001.md
│   │   ├── P00-BOOTSTRAP-PLAN-001.md
│   │   └── P00-BOOTSTRAP-TRANSPORT-001.md
│   ├── provenance/SOURCE-REGISTER.md
│   ├── repository/GS-REPO-STATE-001.md
│   ├── risks/RSK-REGISTER.md
│   └── transport/GS-TRANSPORT-STATE-001.md
└── raglite/
    └── README.md
```

## Arborescence — commit B

```text
raglite/
├── RAGLITE-MANIFEST.yaml
└── mobile/
    ├── 00_GITSPACE_START_HERE.md
    ├── 01_GITSPACE_MASTER_CANON.md
    ├── 02_GITSPACE_NOW_DECISIONS_ROADMAP.md
    ├── 03_GITSPACE_RESEARCH_ATLAS.md
    └── 04_GITSPACE_AGENT_PROTOCOL.md
```

## Invariants

1. Le dépôt complet est l’unique canon éditable après merge.
2. Le RAGLite est une projection de lecture.
3. `source_commit` de la projection est le SHA du commit A.
4. Les digests de la projection sont reproductibles.
5. L’historique de staging reste accessible.
6. `hermesclaw-ci` n’est pas modifiée.
7. Aucun fichier ne prétend que le produit est implémenté.
8. Aucun fournisseur d’agent n’apparaît comme dépendance du plan maître.
9. Toutes les décisions `ACCEPTED` ont une autorité.
10. Tous les claims externes ont type et limites.
11. Aucun pin toolchain exact n’est présenté comme accepté sans qualification.
12. Les identifiants stables sont uniques dans leur registre.
13. Le merge est séparé de la production locale des documents.
14. Le propriétaire peut refuser le changement de rôle de `main` sans perte de travail.

## Unités de travail

### B1 — Consolidation

**Entrées**

- cinq sources RAGLite;
- spécification Phase 00;
- plans v0.1 et v0.2;
- correction de rôles;
- observation GitHub fraîche.

**Sortie**

- corpus v0.3.0;
- registre de conflits;
- registre de provenance.

**Gate**

Zéro contradiction critique non classée.

### B2 — Plan Phase 00 v0.3

**Sortie**

- plan maître executor-neutral;
- statut non exécutable sans paquet;
- Task 1 révisée pour dépôt documenté et toolchain qualifiée;
- aucune occurrence des marqueurs fournisseur interdits.

**Marqueurs interdits dans `GS-P00-PLAN-001.md`**

```text
Claude Code
dontAsk
.claude/
EXEC-E0
executor_harness: CLAUDE_CODE
```

La mention d’un fournisseur peut exister seulement dans un fichier historique.

### B3 — Registres

Produire :

- ADR;
- TDR;
- risques;
- conflits;
- provenance;
- état du dépôt.

**Gate**

- identifiants uniques;
- statut valide;
- source et date;
- aucune ADR acceptée sans autorité.

### B3.5 — Qualification du transport

Avant toute branche distante :

- utiliser un checkout local authentifié;
- interdire toute transcription manuelle de base64;
- vérifier le SHA de `main`;
- préparer A et B localement;
- régénérer B depuis le vrai SHA A;
- comparer les blobs avant et après push.

Le patch B du replay local est `PROOF_ONLY`.

**Gate**

`P00-BOOTSTRAP-TRANSPORT-001` satisfait ou `BLOCKED_WITH_EVIDENCE`.

### B4 — Commit A

Créer la branche depuis le SHA observé et appliquer uniquement les fichiers du corpus complet.

**Message recommandé**

```text
docs(canon): bootstrap GitSpace native world engine corpus
```

**Gate**

- diff attendu;
- aucun code produit;
- aucun fichier de la branche HermesClaw;
- historique parent exact;
- revue documentaire.

### B5 — Projection

Depuis un checkout propre de commit A :

1. lire la `projection_map`;
2. copier byte-for-byte les cinq documents routés;
3. vérifier que chaque hash source égale le hash projection;
4. écrire le manifeste avec `source_commit = A`;
5. régénérer une seconde fois;
6. comparer bit-à-bit.

Aucune synthèse ou reformulation LLM n’est autorisée pendant la génération.

### B6 — Commit B

**Message recommandé**

```text
docs(raglite): publish mobile projection of <short-A>
```

**Gate**

- seuls `raglite/mobile/**` et le manifeste changent;
- le manifeste référence A;
- les digests correspondent;
- la projection se régénère depuis A.

### B7 — Pull request

La pull request doit expliquer :

- pourquoi le README existant est remplacé;
- que son historique est préservé;
- que `hermesclaw-ci` n’est pas modifiée;
- qu’aucun code produit n’est inclus;
- que le RAGLite est publié séparément;
- que le statut reste `PARTIALLY_VERIFIED`.

### B8 — Revue indépendante

Reviewer 1 : autorité et cohérence.

Reviewer 2 : recherche, dates, limites et statuts.

Reviewer 3 : provenance, hashes, protocole deux commits et absence de code produit.

## Critères d’acceptation

Le bootstrap devient `PROVEN` seulement si :

- un transport byte-preserving a été qualifié;
- la branche part du SHA attendu;
- les deux commits sont distincts;
- la PR est revue;
- le commit A contient le canon complet;
- le commit B contient la projection exacte de A et a été régénéré après le vrai A;
- le manifeste est reproductible;
- le dépôt n’a subi aucune suppression non autorisée;
- la branche HermesClaw est intacte;
- l’état courant et la prochaine action sont cohérents;
- une revue indépendante ferme les conflits documentaires;
- le propriétaire accepte le changement de rôle de `main`.

Avant le merge et la régénération depuis le SHA réel, le statut maximal est `PARTIALLY_VERIFIED`.

## Rollback

Avant merge : fermer la PR et supprimer uniquement la branche de bootstrap.

Après merge : revert des commits A et B; ne jamais réécrire l’historique.

## Prochaine unité après merge

`P00-RESEARCH-ATLAS-001 — verrouiller le schéma ResearchClaim, préenregistrer les premières reproductions et préparer le paquet exact de la première tâche d’implémentation.`
