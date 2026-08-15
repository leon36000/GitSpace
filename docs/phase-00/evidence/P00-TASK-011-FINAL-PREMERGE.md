---
evidence_id: P00-TASK-011-FINAL-PREMERGE
status: PARTIALLY_VERIFIED_PENDING_SIGNED_MERGE_AND_POSTMERGE
recorded_at: 2026-08-15
implementation_pr: 49
hardening_pr: 52
base_main: c30d8f0a2b0683f11c147e8447facfed91bf1403
pre_evidence_head: ec1d6b4bc9ed9ee01e5c906e0153e07012448f36
workflow_run: 31861248425
workflow_job: 94954909172
sonar_check: 94954954037
sonar_state: NOT_COMPUTED_EXTERNAL
identity_independent_review: false
---
# P00-TASK-011 — Preuve finale pré-merge

## Résultat utile

Le durcissement final de l’adaptateur Inspect 0.3.258 est fonctionnellement et adversarialement vert sur le head exact `ec1d6b4bc9ed9ee01e5c906e0153e07012448f36`.

Task 11 n’est pas encore `PROVEN` : le merge signé, le replay frais sur `main`, la promotion canonique et la projection RAGLite manquent encore.

## Cause racine fermée

Le premier refactor Sonar de la fuite AnyIO avait remplacé les symboles privés de la release pinée par trois symboles inexistants :

```text
inspect_ai.util._sandbox.context.sample_active
_emit_to_all_hooks
event_emitter
```

La source officielle du commit Inspect `e72c73f8a514c53ddf55da180e4bedaf8f0362b4` expose en réalité :

```text
inspect_ai.hooks._hooks.sample_active
inspect_ai.hooks._hooks._emit_to_all
active.event_done
```

Le shim final :

- importe seulement ces symboles de la release pinée;
- ferme `event_send`, attend `event_done`, draine les événements et ferme `event_receive`;
- remet `event_receive`, `event_send` et `event_done` à `None`;
- restaure toujours la fonction officielle;
- sérialise l’installation et le run contrôlé avec un lock global.

## REDs spécifiques

### API privée incorrecte

```yaml
head: 4ec3738270e9a0bc7d59c39ecc962053967d17ac
workflow: 31860312408
job: 94952433797
result: EXPECTED_FAILURE
```

Le test officiel échouait sur l’absence de `sample_active` au mauvais module et sur le mauvais champ de completion.

### Installation concurrente

```yaml
head: 481dee18db9e710eeedeef6179b3da3e996169ad
workflow: 31860407570
job: 94952691962
result: EXPECTED_FAILURE
observed_overlap: [true, true]
```

Deux contexts pouvaient remplacer la même fonction Inspect simultanément. Le lock final tue ce contre-exemple.

### Sonar evidence state

Le premier classificateur imposait un objet quality-gate même lorsque Sonar annulait l’analyse avant d’en publier un. Le RED :

```yaml
head: f3f2e2f7c1db3a3db445c04ef008053d823cb7dd
workflow: 31861164734
job: 94954691542
failure: "ModuleNotFoundError: No module named 'sonar_evidence_gate'"
```

Le classificateur est maintenant testé comme une machine d’état fail-closed :

- `PASS` exige check `success`, quality gate `OK` et zéro issue;
- annotations ou issues non nulles échouent;
- quality gate calculé en erreur échoue;
- check annulé avec quality gate absent et zéro issue devient `NOT_COMPUTED_EXTERNAL`, jamais `PASS`;
- ce dernier état exige une dérogation explicite dans le workflow.

## GREEN exact-head

```yaml
head: ec1d6b4bc9ed9ee01e5c906e0153e07012448f36
workflow: 31861248425
job: 94954909172
checkout: detached_exact_head
permissions:
  contents: read
  checks: read
python: 3.12.13
uv: 0.12.0
inspect_ai: 0.3.258
jsonschema: 4.26.0
rust: 1.97.1
conclusion: success
```

Gates reproduits :

- 49 tests Inspect et Sonar evidence;
- 26/26 mutations Inspect tuées;
- 43 tests du SDK provider-neutral;
- `compileall`;
- contrat toolchain historique;
- 12 tests de schémas Evaluation IR;
- replay depuis `git archive HEAD` sans `.git`;
- workspace Rust complet verrouillé;
- Clippy `-D warnings`;
- rustfmt;
- dépôt propre.

## Évidence Sonar exacte

```yaml
check_id: 94954954037
head_sha: ec1d6b4bc9ed9ee01e5c906e0153e07012448f36
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

Cette preuve signifie :

- `EVIDENCE` — aucun finding Sonar annoté et aucune issue PR ouverte;
- `UNKNOWN/EXTERNAL` — aucun objet de quality gate n’a été calculé pour ce head;
- `REFUTED` — il est interdit de présenter cet état comme `SONAR_PASS`;
- `DECISION_REVERSIBLE` — la PR peut utiliser une dérogation explicite `NOT_COMPUTED_EXTERNAL` parce que toutes les autres preuves indépendantes du service sont vertes et que les findings Sonar initiaux sont fermés.

## Scope

La PR #52 modifie uniquement :

```text
.github/workflows/p00-task-011.yml
python/gs_eval_adapters/inspect_adapter.py
python/gs_eval_adapters/inspect_cleanup.py
python/gs_eval_adapters/inspect_replay.py
tests/adapters/inspect/run_mutations.py
tests/adapters/inspect/sonar_evidence_gate.py
tests/adapters/inspect/test_cleanup_contract.py
tests/adapters/inspect/test_sonar_evidence_gate.py
```

Aucun schéma Evaluation IR, crate Rust, CAS, journal, verdict, runner, Foundry, canon, RAGLite ou `hermesclaw-ci` n’est modifié.

## Limites conservées

- `LIMIT` — le shim cible une API privée strictement pinée à Inspect 0.3.258;
- `LIMIT` — aucun provider externe, réseau, sandbox ou scorer model-graded n’est qualifié;
- `LIMIT` — la concurrence Inspect extérieure au lock GitSpace reste hors contrat;
- `LIMIT` — le quality gate Sonar externe est `NOT_COMPUTED_EXTERNAL`, pas `PASS`;
- `BLOCKED` — la revue est rôle-séparée mais pas identité-indépendante;
- `BLOCKED` — merge signé, post-merge, canon et RAGLite restent ouverts.

## Décision

`PASS_FOR_ROLE_SEPARATED_REVIEW`.

Le commit de ce dossier crée un nouveau head. Son run final exact doit être enregistré dans la revue de PR afin d’éviter une auto-référence documentaire infinie.
