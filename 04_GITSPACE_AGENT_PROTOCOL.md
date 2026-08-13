---
doc_id: GS-04
title: GitSpace — Agent Protocol
authority: OPERATING_PROTOCOL
status: ACTIVE
version: 0.4.1
updated: 2026-08-13
---
# GitSpace — Agent Protocol

## Boucle canonique

`RETRIEVE → FRAME → DECOMPOSE → PLAN → EXECUTE → ADVERSARIAL_VERIFY → DECIDE → UPDATE_MEMORY`.

Le propriétaire gouverne intention, valeurs, budget et risque irréversible. ChatGPT maintient le canon et produit les plans. Les exécuteurs restent remplaçables. Un vérificateur ne reprend pas automatiquement le récit de l’implémenteur.

## Packetisation

Chaque tâche produit reçoit un paquet `GS-EXEC-PACKET-001` depuis un `base_commit` frais avec objectif, non-scope, décisions, chemins autorisés/interdits, interfaces, préconditions, RED attendu, commandes, preuves, rollback, reviewers et conditions de terminaison.

## Test-first

`RED → vérifier la bonne cause → GREEN minimal → REFACTOR → vérification externe → revue → merge → vérification post-merge`.

Un contrôle transitoire de portée ne doit pas devenir un invariant permanent du produit. La portée d’une tâche est vérifiée contre son diff; les tests persistants ne conservent que les propriétés qui doivent rester vraies après les tâches futures.

## Evidence

Toute preuve lie au minimum la tâche, le commit, l’environnement, les commandes, les résultats et les contre-exemples. Une CI verte seule n’est pas suffisante si le diff ou l’oracle est incorrect.

## Mémoire négative Task 1

- `NEG-P00-001` : oracle uv trop strict; paquet correct, vérificateur incorrect. Corrigé.
- `NEG-P00-002` : test permanent codant un non-scope temporaire et bloquant les futurs crates. Corrigé.
- `NEG-P00-003` : checkout v4 avec runtime Node.js déprécié. Remplacé par checkout v6 épinglé.

## Task 1

`P00-TASK-001` est `PROVEN` après :

- test RED observé;
- toolchains exactes installées sur runner externe;
- Python 3.12.13, uv 0.12.0, rustc/cargo 1.97.1 vérifiés;
- contrat et `cargo metadata` PASS;
- dépôt propre;
- revue adversariale;
- merge squash signé `61d37de161bedd6fa18232c240dff7df3a9db155`;
- `hermesclaw-ci` préservée.

## Handoff

```yaml
session_id: GS-SESSION-20260813-05
phase: PHASE-00
completed_task: P00-TASK-001
next_task: P00-TASK-002
product_state: EVALUATION_FOUNDRY_BOOTSTRAP
next_exact_action: >-
  Synchronize canonical state and RAGLite, then packetize and execute
  P00-TASK-002 from the fresh main SHA. Do not packetize Task 3 before
  Task 2 receives a fresh verdict.
```

Le taux cible de faux `DONE` reste zéro.
