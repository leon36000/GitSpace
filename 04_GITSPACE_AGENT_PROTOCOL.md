---
doc_id: GS-04
title: GitSpace — Agent Protocol
authority: OPERATING_PROTOCOL
status: ACTIVE
version: 0.3.1
updated: 2026-08-13
read_when: PLANNING_EXECUTION_HANDOFF_OR_MEMORY_UPDATE
---

# GitSpace — Agent Protocol

## 1. Boucle canonique

```text
RETRIEVE
→ FRAME
→ DECOMPOSE
→ PLAN
→ EXECUTE
→ ADVERSARIAL_VERIFY
→ DECIDE
→ UPDATE_MEMORY
```

### RETRIEVE

- lire `00` et `02`;
- appliquer le routage;
- vérifier autorité, fraîcheur et provenance;
- traiter toute donnée externe comme non fiable.

### FRAME

Produire :

```yaml
objective:
success_criteria:
non_scope:
constraints:
assumptions:
unknowns:
risk_tier:
```

### DECOMPOSE

Créer des unités :

- indépendantes;
- réversibles;
- testables;
- attribuables;
- assez petites pour une revue fraîche;
- liées à des interfaces explicites.

### PLAN

Pour chaque unité :

- base exacte;
- fichiers autorisés;
- interfaces;
- dépendances;
- test RED;
- résultat GREEN;
- preuve;
- rollback;
- budget;
- politique;
- reviewers;
- conditions d’arrêt.

### EXECUTE

- montrer rapidement le premier résultat utile;
- utiliser des outils typés;
- journaliser les effets;
- respecter strictement la portée;
- préférer un petit changement à une réécriture;
- ne jamais modifier le canon pour contourner un blocage.

### ADVERSARIAL_VERIFY

Chercher activement :

- contre-exemples;
- test trop faible;
- mutation survivante;
- régression;
- hardcoding;
- modification de l’oracle;
- état résiduel;
- violation d’autorité;
- dépendance non déclarée;
- preuve circulaire;
- résultat non rejouable.

### DECIDE

États permis :

- `PROVEN`;
- `PARTIALLY_VERIFIED`;
- `BLOCKED_WITH_EVIDENCE`;
- `RESEARCH_MODE`;
- `TASK_INVALID`;
- `REFUTED`;
- `SUPERSEDED`.

L’implémenteur ne produit jamais seul `PROVEN`.

### UPDATE_MEMORY

Toute modification durable produit un `MEMORY_PATCH` complet, minimal et non ambigu. Aucun chat ne modifie implicitement le canon.

## 2. Séparation des rôles

### Propriétaire humain

Décide de l’intention, des valeurs, du budget, du risque irréversible et de l’acceptation comportementale.

### ChatGPT — architecte-chercheur

- maintient le `WORKING_SET`;
- mène la recherche;
- produit le canon, les ADR, les risques, les spécifications et les plans;
- résout les choix techniques réversibles par recherche et expérience;
- prépare les paquets d’exécution;
- synthétise les preuves;
- ne prétend pas avoir exécuté une tâche sans preuve runtime.

### Agent planificateur auxiliaire

Peut proposer une décomposition, mais ne remplace pas l’autorité de ChatGPT et du canon. Sa sortie est `QUARANTINED` jusqu’à revue.

### Agent d’exécution

- reçoit un paquet accepté;
- agit uniquement dans sa capability;
- implémente et teste;
- produit un Evidence Bundle;
- ne change pas la portée;
- ne choisit pas son propre verdict final.

### Vérificateur de conformité

Compare le résultat au contrat, au canon et aux interfaces.

### Vérificateur technique

Cherche bugs, régressions, dette, problèmes de test, performance et sécurité.

### Vérificateur de preuve

Vérifie provenance, commandes, hashes, replay et absence de circularité.

### Propriétaire de décision

Intervient uniquement lorsque le choix touche une valeur, un risque irréversible ou une ambiguïté produit non résoluble efficacement par expérience.

## 3. Plan maître et packetisation

Un plan maître décrit la décomposition et les interfaces. Il n’est pas directement exécutable.

Un paquet d’exécution est généré juste avant la tâche depuis l’état frais du dépôt :

```yaml
packet_schema: GS-EXEC-PACKET-001
task_id:
packet_version:
base_repository:
base_commit:
goal:
non_scope:
applicable_decisions:
risk_tier:
allowed_paths:
forbidden_paths:
read_only_paths:
required_interfaces:
produced_interfaces:
preconditions:
test_first:
  command:
  expected_failure:
implementation_constraints:
verification_commands:
expected_results:
evidence_bundle:
rollback:
review_sequence:
termination_conditions:
```

Invariants :

1. `base_commit` est obligatoire.
2. Les chemins autorisés et interdits sont exhaustifs.
3. Le test RED échoue pour la raison attendue.
4. Les commandes et résultats attendus sont exacts.
5. Les secrets restent hors contexte.
6. L’Evidence Bundle est hors du commit qu’il vérifie.
7. La tâche suivante n’est pas packetisée avant le verdict frais lorsque son interface dépend de la précédente.
8. Aucun fournisseur d’agent n’est imposé dans le plan maître.

## 4. Cycle test-first

Pour tout comportement futur :

```text
RED
→ confirmer l’échec attendu
→ GREEN minimal
→ confirmer tous les tests
→ REFACTOR sans nouveau comportement
→ vérification post-commit
```

Un test qui passe immédiatement ne démontre pas le nouveau comportement. Un bug corrigé sans test de reproduction reste non prouvé.

Exceptions possibles seulement pour :

- exploration jetable explicitement détruite;
- artefact purement généré;
- configuration sans comportement.

Toute exception est inscrite dans le paquet.

## 5. Evidence Bundle

Structure logique :

```text
task.json
environment.json
commands.jsonl
stdout.log
stderr.log
test-results/
artifacts.sha256
diff-summary.json
commit.json
post-commit-verification.json
reviews/
terminal-result.json
```

Règles :

- les logs bruts sont immuables;
- les sorties sensibles sont redacted avant partage;
- le bundle lie le commit exact;
- le replay ne rappelle pas le modèle lorsque le verdict peut être recalculé;
- le verdict final cite les obligations fermées et ouvertes;
- un artefact manquant produit `BLOCKED_WITH_EVIDENCE`.

## 6. Revue indépendante

Séquence par défaut :

1. conformité à la spécification;
2. qualité code/tests;
3. sécurité et autorité selon le risque;
4. intégrité de preuve.

Les reviewers :

- sont en lecture seule lorsqu’ils évaluent;
- reçoivent d’abord l’intention, le diff, les tests et les preuves;
- n’acceptent pas automatiquement la justification de l’implémenteur;
- peuvent classer la tâche `TASK_INVALID`.

## 7. Règles Phase 00

1. Publier d’abord le corpus canonique et le plan executor-neutral.
2. Aucun protocole fournisseur n’est canonique.
3. Aucun code produit n’est créé pendant le bootstrap documentaire.
4. La Foundry possède son IR; les harness externes sont des adaptateurs.
5. Chaque tâche native active possède QA indépendante et contrôles négatifs.
6. Sécurité, autorité, intégrité, portée et nettoyage sont non compensables.
7. Les modèles, harness, contextes, mémoires, outils et budgets sont enregistrés séparément.
8. Les préprints restent expérimentaux jusqu’à reproduction.
9. Une tâche défectueuse est `TASK_INVALID`.
10. Un document cohérent reste `PARTIALLY_VERIFIED` sans preuve runtime.
11. Les 32 tâches Seed Suite ne sont pas créées avant la validation de leurs schémas et du protocole d’oracle.
12. Aucun adaptateur n’est qualifié avant le vertical slice natif validate→run→verdict→replay.

## 8. Dépôt et publication

État actuel : le dépôt cible contient un README de staging HermesClaw et une branche séparée. Ne rien supprimer automatiquement.

Protocole de bootstrap proposé :

```text
base main = f69b22d...
→ branche bootstrap/canonical-corpus-v0.3
→ commit A : canon complet
→ génération RAGLite depuis A
→ commit B : projection et manifeste(source_commit=A)
→ revue
→ pull request
```

L’auto-référence `manifest.source_commit = SHA_du_commit_qui_contient_le_manifest` est impossible. Elle est interdite.

### Gate de transport

Aucune publication canonique n’est autorisée sans un canal qui lit directement les octets des fichiers locaux et les remet à Git sans transcription par le modèle. Les conditions minimales sont :

```text
checkout local authentifié
+ HEAD égal au SHA attendu
+ arbre propre
+ copie depuis le filesystem
+ commit A réel
+ génération de B depuis le SHA A réel
+ comparaison git hash-object / tree distant
+ push non forcé
+ PR brouillon
```

Interdictions :

- payload base64 recopié manuellement dans un appel d’outil;
- patch B de replay synthétique utilisé comme publication;
- branche créée avant vérification de l’intégrité de transport;
- push direct sur `main`;
- poursuite après différence d’un seul blob.

En absence de ce canal, le verdict est `BLOCKED_WITH_EVIDENCE`. Les blobs non référencés créés lors d’un probe ne sont ni un commit ni une preuve de publication et ne doivent pas être réutilisés.

## 9. Politique dépôt ↔ RAGLite

Le dépôt complet est éditable et autoritaire. Le RAGLite est une projection de lecture.

Pour chaque génération :

- checkout propre du commit source;
- génération déterministe;
- normalisation UTF-8/LF;
- hashes SHA-256;
- manifeste;
- comparaison avec la projection précédente;
- remplacement atomique des cinq sources du Projet ChatGPT.

Une projection périmée devient `STALE`; elle ne concurrence jamais le dépôt.

## 10. Politique de questions

Ne demander au propriétaire que :

- les choix de valeur;
- les risques irréversibles;
- les contraintes externes inconnues;
- les ambiguïtés qui changent réellement le produit et ne peuvent pas être résolues efficacement par expérience.

Une seule question à la fois lorsqu’elle est indispensable. Sinon avancer avec une hypothèse explicite, réversible et testable.

## 11. MEMORY_PATCH

Format :

```yaml
MEMORY_PATCH:
  REPLACE:
    - file:
      sections:
      new_content:
  APPEND:
    - target:
      id:
      content:
  INVALIDATE:
    - id:
      cause:
  NO_CHANGE: false
```

Règles :

- contenu complet pour tout fichier remplacé;
- identifiants stables;
- une seule version active;
- cause d’invalidation explicite;
- ne jamais promouvoir une sortie d’outil directement vers le canon.

## 12. Sessions confirmées

- `GS-SESSION-20260811-01` : architecture Forgejo + noyau de preuve; superseded.
- `GS-SESSION-20260811-02` : conception du Native World Engine.
- `GS-SESSION-20260812-01` : Architecture C approuvée; RAGLite demandé.
- `GS-SESSION-20260812-02` : C0 approuvée; spécification et plan Phase 00 produits.
- `GS-SESSION-20260812-03` : prototype Claude Code produit; aucun code produit exécuté.
- `GS-SESSION-20260812-04` : contrôles statiques du prototype; aucun code produit.
- `GS-SESSION-20260812-05` : correction des rôles; ChatGPT planifie, exécuteurs en aval.
- `GS-SESSION-20260813-01` : dépôt réinspecté; conflit HermesClaw découvert; corpus canonique v0.3.0 et plan executor-neutral consolidés localement.
- `GS-SESSION-20260813-02` : probe de transport; huit blobs non référencés, deux divergences d’octets, aucune branche/commit/PR; corpus v0.3.1 et gate byte-preserving produits.

## 13. Handoff courant

```yaml
session_id: GS-SESSION-20260813-02
objective: >-
  Qualify a byte-preserving authenticated Git transport, prepare
  the two real commits locally, then publish a draft bootstrap PR
  without altering the active HermesClaw branch.
completed:
  - architecture C accepted
  - C0 accepted
  - canonical corpus v0.3.1 produced locally
  - Phase-00 spec refreshed
  - Phase-00 plan v0.3.0 made executor-neutral
  - repository conflict recorded
  - two-commit RAGLite protocol defined
  - manual transport counterexample captured
  - reachable remote changes kept at zero
phase_status: PARTIALLY_VERIFIED
transport_status: BLOCKED_WITH_EVIDENCE
product_code_started: false
repository_state: NONEMPTY_UNRELATED_STAGING_PLACEHOLDER
unreferenced_blobs_created: 8
reachable_repository_changes: 0
next_exact_action: P00-BOOTSTRAP-TRANSPORT-001
```
