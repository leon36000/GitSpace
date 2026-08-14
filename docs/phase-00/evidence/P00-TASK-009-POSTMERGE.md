---
evidence_id: P00-TASK-009-POSTMERGE
status: PROVEN_BOUNDED_CONTRACT
recorded_at: 2026-08-14
implementation_pr: 41
review_id: 4939711264
merge_commit: b15a2b74f16e8fa6bf1d88832c9191eab44f2a25
merge_tree: 0104defea61adab4f1ef250d5eabfa8851bbb369
base_commit: 7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd
postmerge_workflow_run: 31824037711
postmerge_workflow_job: 94843810930
identity_independent_review: false
---
# P00-TASK-009 — Preuve post-merge

## Verdict utile

`P00-TASK-009 = PROVEN` dans son contrat d’implémentation borné.

Le milestone M0 global reste `PARTIALLY_VERIFIED` parce qu’aucune reproduction par une identité de reviewer séparée n’est enregistrée. Cette limite n’est ni compensée par la CI ni transformée en preuve implicite.

## Merge signé

GitHub a créé le commit de merge squash :

```text
b15a2b74f16e8fa6bf1d88832c9191eab44f2a25
```

Provenance vérifiée :

```yaml
parent: 7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd
tree: 0104defea61adab4f1ef250d5eabfa8851bbb369
verification:
  verified: true
  reason: valid
```

Le commit fusionné est la tête de `main`. La branche `hermesclaw-ci` reste intacte à `91f55525b231116fd431430f46c87667e5c1f140`.

## Replay frais sur `main`

Le workflow final read-only Task 9 a été déclenché par le push du merge signé lui-même :

```yaml
workflow: P00 Task 009 Native Foundry
run: 31824037711
job: 94843810930
head: b15a2b74f16e8fa6bf1d88832c9191eab44f2a25
checkout: detached_exact_head
os: Ubuntu 24.04
rust: 1.97.1
permissions:
  contents: read
conclusion: success
```

Le même push a également produit :

```yaml
P00_TASK_006: {run: 31824037655, conclusion: success}
P00_TASK_007: {run: 31824037841, conclusion: success}
P00_TASK_008: {run: 31824037632, conclusion: success}
P00_TASK_009: {run: 31824037711, conclusion: success}
```

Le job Task 9 a reproduit depuis le lockfile committé :

- les cinq classifications `PASS`, `FAIL`, `TIMEOUT`, `POLICY`, `INFRA`;
- le contrôle explicite `false_done=true` du scénario FAIL;
- le verdict PASS historique bloqué sans auto-attribution des gates de preuve;
- l’identité déterministe liée à `(source_commit, scénario)`;
- la coexistence de deux commits sans alias de run;
- les substitutions CAS sémantiquement valides mais incorrectes;
- le replay read-only sans initialisation ni réparation du store;
- les substitutions symlink Foundry/CAS/journal;
- les trois événements typés du journal et le trace reconstruit;
- les tests du workspace complet;
- Clippy avec `-D warnings`;
- rustfmt;
- le graphe Cargo verrouillé;
- le gate de dépôt propre.

## Contrat prouvé

Le vertical slice M0 prouvé est :

```text
EvalTaskSpec validé
→ fixture déterministe
→ runner local tool-mediated
→ oracle protégé
→ artefacts CAS immuables
→ journal append-only
→ verdict historique non compensable
→ EvidenceBundle
→ EvalRunManifest
→ replay/rescore sans modèle et sans écriture
```

Propriétés couvertes :

1. Les artefacts `task`, `plan`, `state_before`, `state_after`, `patch`, `scoring`, `verdict`, `evidence`, `manifest` et `trace` sont liés par CAS et références croisées.
2. Le replay compare la sémantique qualifiée, pas seulement la validité cryptographique d’un objet.
3. Les identités run/verdict/evidence sont déterministes, namespacées par commit source et scénario, tandis que le commit complet reste dans la preuve.
4. Le verdict historique PASS reste `blocked`, `safe_success=false`, `false_done=false`, avec `regression`, `evidence`, `replay` et `independent_verification` ouverts.
5. Le scénario FAIL déclare volontairement success après oracle négatif et produit `false_done=true`.
6. Replay revalide les artefacts, recompose le verdict byte-à-byte et ne réécrit pas le verdict historique.
7. Replay ne crée pas un store absent, ne répare pas une disposition incomplète et ne recrée pas le runner.
8. Les liens symboliques présents avant ouverture sont refusés.
9. Le second replay est bit-stable.
10. Aucun modèle, réseau, shell, code natif arbitraire, container, VM ou base distante ne participe à ce contrat.

## Mémoire négative conservée

- cycle cryptographique RunManifest ↔ EvidenceBundle;
- substitutions CAS seulement hash-valides;
- alias d’identité entre commits;
- initialisation filesystem par un chemin présenté comme read-only;
- auto-attribution de `replay_passed`, `independent_verification_passed` ou `regression_free`;
- fixture symlink invalide testant un dossier journal non encore créé.

Chaque finding a été reproduit avant correction ou classé comme défaut de tâche/fixture avant promotion.

## Limites et contre-exemples ouverts

- `BLOCKED` — aucune reproduction par une identité de reviewer séparée; le Gate M0 complet n’est donc pas fermé.
- `LIMIT` — hors harness exact-head, `source_commit` est fourni par l’appelant et n’est pas signé par Task 9.
- `LIMIT` — l’identité routée tronque SHA-256 à 128 bits; le commit complet demeure l’autorité de provenance.
- `LIMIT` — le M0 local ne protège pas contre une course filesystem conduite par un processus hostile concurrent.
- `UNKNOWN` — le dénominateur canonique futur des obligations visibles, protégées et runtime n’est pas encore représenté par un registre typé.
- `LIMIT` — la fixture n’exécute pas de code arbitraire et ne qualifie aucun framework externe.

## Décision

Task 9 est `PROVEN` uniquement dans le contrat borné ci-dessus. La Phase 00 et le milestone M0 restent `PARTIALLY_VERIFIED`.

Task 10 peut être packetisée seulement après fusion de cette promotion d’état et de sa projection RAGLite byte-identical.
