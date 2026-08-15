---
evidence_id: P00-TASK-011-POSTMERGE
status: PROVEN_BOUNDED_CONTRACT
recorded_at: 2026-08-14
implementation_pr: 49
hardening_pr: 52
final_review_id: 4942612349
merge_commit: 0eb361843cb67d798f8030763f1fffbcffd665ca
merge_tree: 3602f5d3ddc7236ab700dcca6d5d2f3d1bd8778b
base_commit: c30d8f0a2b0683f11c147e8447facfed91bf1403
postmerge_workflow_run: 31861648147
postmerge_workflow_job: 94955991327
task10_regression_run: 31861648140
task10_regression_job: 94955991418
sonar_premerge_state: NOT_COMPUTED_EXTERNAL
identity_independent_review: false
---
# P00-TASK-011 — Preuve post-merge finale

## Verdict utile

`P00-TASK-011 = PROVEN` dans son contrat borné de fixture Inspect AI 0.3.258, après intégration du durcissement correctif.

La Phase 00 et le milestone M0 restent `PARTIALLY_VERIFIED`. Cette preuve ne qualifie ni Inspect en général, ni un provider externe, ni un sandbox hostile, ni une revue indépendante par identité.

## Merge signé final

GitHub a créé le commit squash correctif :

```text
0eb361843cb67d798f8030763f1fffbcffd665ca
```

```yaml
parent: c30d8f0a2b0683f11c147e8447facfed91bf1403
tree: 3602f5d3ddc7236ab700dcca6d5d2f3d1bd8778b
verification:
  verified: true
  reason: valid
  verified_at: 2026-08-15T03:22:30Z
```

Le commit signé est la tête produit de `main`. La branche `hermesclaw-ci` reste intacte à `91f55525b231116fd431430f46c87667e5c1f140`.

## Replay frais sur main

Le workflow Task 11 a été déclenché par le push du merge signé lui-même :

```yaml
workflow: P00 Task 011 Inspect Adapter
run: 31861648147
job: 94955991327
head: 0eb361843cb67d798f8030763f1fffbcffd665ca
event: push
checkout: detached_exact_head
permissions:
  contents: read
  checks: read
conclusion: success
```

Le même merge a reproduit Task 10 :

```yaml
workflow: P00 Task 010 Adapter SDK
run: 31861648140
job: 94955991418
head: 0eb361843cb67d798f8030763f1fffbcffd665ca
conclusion: success
```

Le job Task 11 a reproduit depuis les locks committés :

- Python 3.12.13, uv 0.12.0, Inspect AI 0.3.258 et jsonschema 4.26.0;
- 49 tests Inspect et Sonar-evidence;
- 26/26 mutations Inspect tuées;
- 43 tests de la frontière provider-neutral;
- vrai run local contrôlé `mockllm/model`, un Task, un Sample et une epoch;
- réseau bloqué, mapping version/commit/model/solver/scorer fermé;
- log complet et record sous URI CAS correspondant aux bytes;
- projection du log complet et replay exact-match sans import Inspect;
- fermeture du receiver AnyIO abandonné par la release pinée;
- restauration du shim après succès ou exception;
- sérialisation de toute installation concurrente du shim;
- replay depuis `git archive HEAD` sans métadonnées Git;
- workspace Rust complet verrouillé;
- Clippy `-D warnings`;
- rustfmt;
- dépôt propre.

Le step Sonar du workflow push est volontairement `skipped`, car le classificateur interroge les objets spécifiques à une pull request. La preuve Sonar pertinente est l’évidence pré-merge exacte du head revu.

## Évidence Sonar pré-merge

```yaml
head: ee6add231bdfbb6060ccb9945295c445f857c683
check_id: 94955475668
check_status: completed
check_conclusion: cancelled
annotations_count: 0
issues_api:
  http_status: 200
  unresolved_total: 0
quality_gate_api:
  http_status: 404
  status: null
classification: NOT_COMPUTED_EXTERNAL
```

Interprétation canonique :

- `EVIDENCE` — zéro annotation et zéro issue PR ouverte;
- `UNKNOWN/EXTERNAL` — aucun objet quality gate n’a été calculé;
- `REFUTED` — cet état n’est jamais présenté comme `SONAR_PASS`;
- `DECISION_REVERSIBLE` — une dérogation explicite a permis le merge car les findings Sonar initiaux sont fermés et toutes les preuves exécutables indépendantes du service sont vertes.

## Contrat prouvé

```text
EvalTaskSpec + AgentConfiguration validés
→ mapping Inspect fermé
→ Task/Sample en mémoire
→ mockllm/model
→ generate
→ scorer match exact
→ EvalLog JSON complet
→ log et record CAS
→ projection et rescoring sans Inspect
```

Propriétés couvertes :

1. Release, commit source, wheel et sdist sont pinés et concordent avec `uv.lock`.
2. Task 10 valide le canon avant le premier accès Inspect.
3. Aucun provider, endpoint, secret, socket, tool, agent ou sandbox externe ne participe.
4. Les types runtime acceptés sont bornés au wrapper officiel exact ou à la forme qualifiée, avec un unique `EvalLog` exact.
5. Le log complet est projeté dans un module qui n’importe pas Inspect.
6. Log et record sont liés par SHA-256 à leurs URI CAS.
7. Record et résultat replay sont fermés et revalidés après mutation.
8. Le score Inspect doit être reproduit par le scorer exact-match indépendant; une divergence échoue fermée.
9. Les états `error` ou `cancelled` sont INFRA et ne deviennent pas un échec agent.
10. L’ordre des événements participe au digest du record.
11. Le receiver AnyIO est fermé; sender, receiver et completion refs sont nettoyés.
12. Le shim privé utilise les symboles exacts de la release pinée, est sérialisé et toujours restauré.
13. Le workflow final et le replay sont strictement en lecture seule.

## Mémoire négative conservée

- harness RED échouant avant le seam faute de dépendance Task 10;
- fixture Evaluation IR invalide;
- dataclass tentant de franchir la frontière JSON;
- score indépendant masqué lors d’un désaccord;
- wrapper runtime non couvert par l’annotation publique;
- URI record non liée aux bytes;
- mutation post-construction non revalidée;
- bool accepté comme entier de projection;
- projection du log complet absente du module Inspect-free;
- receiver AnyIO abandonné par la release pinée;
- premier shim fondé sur des symboles privés inexistants;
- installation concurrente du monkey-patch;
- quality gate Sonar absent incorrectement traité comme un échec ou comme un succès;
- ancienne projection RAGLite #51 dérivée du produit pré-durcissement, fermée `STALE` sans merge.

## Limites et risques résiduels

- `LIMIT` — une seule fixture Inspect 0.3.258, pas le framework complet.
- `LIMIT` — API privée utilisée sous pin exact; chaque future release exige suppression ou requalification du shim.
- `LIMIT` — aucun appel direct concurrent à Inspect hors lock GitSpace n’est qualifié.
- `LIMIT` — aucun modèle/provider externe, réseau, tool, agent, sandbox ou scorer model-graded.
- `LIMIT` — le sink injecté est vérifié par digest mais le stockage durable externe est hors scope.
- `LIMIT` — le replay indépendant couvre uniquement le sous-ensemble exact-match qualifié.
- `LIMIT` — Sonar est `NOT_COMPUTED_EXTERNAL`, pas `PASS`.
- `BLOCKED` — aucune reproduction par une identité de reviewer séparée.

## Décision

Task 11 est `PROVEN` uniquement dans la frontière bornée ci-dessus. La Phase 00 et M0 restent `PARTIALLY_VERIFIED`.

Les workflows temporaires de promotion qui ciblaient l’ancien merge `0d55958ae2527f91cde0f27fb7cb2c2abceb3bff` sont supprimés comme `STALE`. Task 12 peut être packetisée seulement après fusion de cette promotion finale et de sa projection RAGLite byte-identical.
