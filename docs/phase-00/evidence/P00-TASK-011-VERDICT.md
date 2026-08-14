---
evidence_id: P00-TASK-011-VERDICT
status: PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE
recorded_at: 2026-08-14
base_commit: e082cf941d865d71347feae475e4a8e43aeab5e2
implementation_pr: 49
red_pr: 48
pre_documentation_head: 134f110f4917b137ef1151ba2ad77345a8d75cb0
pre_documentation_workflow_run: 31843227076
pre_documentation_workflow_job: 94904335561
identity_independent_review: false
---
# P00-TASK-011 — Verdict de vérification pré-merge

## Résultat sous revue

Task 11 qualifie une seule fixture Inspect AI 0.3.258 derrière la frontière provider-neutral Task 10 :

```text
EvalTaskSpec + AgentConfiguration validés
→ Task / Sample Inspect en mémoire
→ mockllm/model
→ generate
→ match exact
→ EvalLog JSON complet
→ log et record CAS
→ projection/replay sans Inspect
→ rescoring indépendant
```

Cette preuve ne qualifie pas Inspect en général.

## Qualification officielle

```yaml
framework: inspect-ai
version: 0.3.258
tag: 0.3.258
source_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
wheel_sha256: 638da28a5f3a021152481c5aa22d440a2855e462804dce2d49a44e6e47be16a4
sdist_sha256: 785a14b5348c57a188e8790a1919106bff539645d93c4e9d1dfdd8f2b0896405
python: 3.12.13
uv: 0.12.0
model: mockllm/model
network: forbidden
```

`pyproject.toml`, `uv.lock` et le manifeste de qualification concordent sur la version et les hashes de package.

## TDD RED

### Premier harness incomplet

Le premier run RED `31838580017` / `94890314317` échouait avant le seam Task 11 parce que le harness n’avait pas installé la dépendance Task 10 `jsonschema`.

Ce résultat a été rejeté comme preuve. Seul le harness a été corrigé; aucun module Inspect ni dépendance Inspect n’a été ajouté.

### RED externe valide

```yaml
branch: agent/p00-task-011-red-v1
pr: 48
head: 5c3ba0e74c214b478e539936e3bef335e4187bde
workflow_run: 31838641477
workflow_job: 94890506040
permissions:
  contents: read
inner_failure: "ModuleNotFoundError: No module named 'gs_eval_adapters.inspect_adapter'"
inspect_dependency_present: false
production_modules_present: false
repository_clean: true
```

PR #48 a été fermée sans merge. Le GREEN est reparti du même commit canonique.

## Findings adversariaux reproduits et fermés

### Fixture Evaluation IR invalide

Le premier GREEN utilisait `origin.kind="adapted"`, valeur absente du schéma souverain. La fixture est devenue `imported`; le schéma n’a pas été affaibli.

### Objet de test hors frontière JSON

Un test passait un `InspectReplayRecord` dataclass dans le raw Task 10. Le test a été corrigé pour passer `record.to_json()`. La frontière n’a pas été élargie.

### Score indépendant masqué

En cas de divergence, le résultat replay devenait INFRA mais perdait le score recalculé. Le replay conserve désormais le score indépendant et expose séparément l’échec d’accord.

### Wrapper runtime Inspect non documenté par le type public

Le run réel a mesuré `inspect_ai._eval.eval.EvalLogs`, sous-classe officielle de list, cardinalité 1. L’adaptateur accepte seulement :

- `list` builtin exacte; ou
- le type officiel exact `EvalLogs` de la release pinée.

Une classe qui imite uniquement le module et le nom est rejetée. L’unique élément doit être un `EvalLog` exact.

### Replay insuffisamment lié

Des REDs ont démontré :

- absence de projection du log complet dans le module Inspect-free;
- `record_uri` non vérifié contre les bytes du record;
- mutation de `scorer_options` après construction non revalidée;
- bool accepté comme alias d’int dans version/epoch;
- constructeur `InspectReplayResult` insuffisamment strict;
- mutation post-construction des obligations non détectée.

Corrections : projection complète hors Inspect, revalidation avant sérialisation/rescore, types exacts, champs fermés, obligations exactes et liaison cryptographique des deux artefacts.

### Fuite de receiver AnyIO dans Inspect 0.3.258

Un run unique laissait un `MemoryObjectReceiveStream` ouvert : receiver=1, sender=0, buffer=0, aucun waiter.

La source officielle pinée montre que `drain_sample_events` draine le receiver puis supprime la référence sans le fermer.

REDs :

```yaml
warning_red:
  head: 40331a8c168f37ba0f55facf40f70d5f6f3c03e7
  run: 31842092901
  job: 94900961438
state_red:
  head: 1a9c7e23d6744e58f72b0adba6c3e9d7182cd849
  run: 31842288104
  job: 94901542755
invalid_first_shim:
  head: f27b704fb1e68b412b8263a81bbf876a87644986
  run: 31842865496
  job: 94903273992
```

Le premier shim utilisait des symboles privés inexistants et a échoué fermé. Le correctif final reproduit la fonction officielle pinée, ajoute uniquement `await receive.aclose()`, sérialise les appels par lock et restaure la fonction originale après succès ou exception.

La distribution Inspect n’est pas modifiée.

## GREEN pré-documentation

```yaml
head: 134f110f4917b137ef1151ba2ad77345a8d75cb0
workflow: P00 Task 011 Inspect Adapter
run: 31843227076
job: 94904335561
checkout: detached_exact_head
permissions:
  contents: read
python: 3.12.13
uv: 0.12.0
inspect_ai: 0.3.258
jsonschema: 4.26.0
rust: 1.97.1
conclusion: success
```

Gates reproduits :

- lock Python vérifié et sync frozen;
- version Inspect exacte;
- run réel à un sample sur `mockllm/model` sans socket;
- log complet et record sous URI CAS correspondant aux bytes;
- projection du log complet et fixture statique;
- replay dans un subprocess bloquant tout import `inspect_ai`;
- score exact-match indépendant;
- zéro/multiple logs et samples refusés;
- états error/cancelled classés INFRA;
- mapping altéré refusé avant eval;
- type `EvalLogs` spoofé refusé;
- cycle de vie AnyIO sans receiver ouvert;
- shim restauré après succès et exception;
- suite provider-neutral Task 10 complète;
- schémas offline et toolchain historiques;
- replay depuis `git archive HEAD` sans `.git`;
- workspace Rust complet verrouillé;
- Clippy `-D warnings`;
- rustfmt;
- dépôt propre.

## Mutation testing

Vingt-quatre mutations critiques ont été injectées dans des copies jetables; toutes ont été tuées :

```text
skip-installed-version
allow-arbitrary-log-wrapper
allow-non-eval-log
skip-published-artifact-digest
skip-record-uri-digest
skip-independent-score-agreement
skip-framework-mapping-check
drop-event-receiver-close
drop-cleanup-shim-restore
accept-multiple-full-log-samples
route-full-log-as-static-projection
allow-projection-bool-version
allow-projection-bool-epoch
allow-projection-scorer-options
allow-record-scorer-options
allow-record-string-subclasses
drop-record-json-revalidation
drop-replay-result-revalidation
allow-incomplete-replay-obligations
force-independent-match
force-score-agreement
drop-record-field-closure
sort-event-order
couple-replay-to-inspect
```

```yaml
mutations: 24
killed: 24
survived: 0
```

## Propriétés vérifiées

1. La release, le commit, le wheel et le sdist sont explicitement pinés.
2. Task 10 valide la requête avant tout accès Inspect.
3. Le mapping qualifié est fermé et contrôlé avant eval.
4. Le run utilise uniquement un modèle mock local, un sample, une epoch, generate et match exact.
5. Les tentatives de connexion socket sont bloquées et le run réussit.
6. Le wrapper et l’EvalLog runtime doivent être les types exacts autorisés.
7. Le log complet est sérialisé sans NaN/Infinity et son URI correspond aux bytes.
8. Le record est fermé, revalidé et son URI correspond à ses bytes.
9. Aucun objet Inspect ne traverse la frontière Task 10.
10. Le module replay importe zéro code Inspect.
11. Le log complet peut être projeté hors Inspect.
12. Le replay statique fonctionne lorsque tout import Inspect est bloqué.
13. L’ordre des événements participe au digest du record.
14. Le scorer qualifié est reproduit sans Inspect.
15. Toute divergence score Inspect/replay échoue fermée.
16. Les états non-success sont INFRA et non agent FAIL.
17. La fuite AnyIO pinée est fermée et le shim est restauré.
18. Le workflow final est en lecture seule.

## Portée vérifiée

La PR touche uniquement :

- dépendance/lock Python;
- `inspect_adapter.py` et `inspect_replay.py`;
- README du SDK;
- tests Inspect;
- qualification, packet et preuves Task 11;
- workflow Task 11.

Aucun schéma Evaluation IR, crate Rust, CAS, journal, verdict, runner, Foundry, canon, RAGLite ou `hermesclaw-ci` n’est modifié.

## Limites et risques résiduels

- `LIMIT` — qualification d’une seule fixture Inspect 0.3.258, pas du framework complet.
- `LIMIT` — API privée utilisée pour le shim; pin et mutation testing obligatoires.
- `LIMIT` — aucune concurrence directe d’Inspect hors lock GitSpace.
- `LIMIT` — aucun provider externe, réseau, tool, agent, sandbox ou scorer model-graded.
- `LIMIT` — le sink injecté publie les bytes; Task 11 vérifie l’URI mais ne fournit pas lui-même un stockage durable.
- `LIMIT` — le rescoring reproduit seulement le sous-ensemble exact-match qualifié.
- `LIMIT` — les tests/locks ne constituent pas une preuve universelle d’absence de vulnérabilité de dépendance.
- `BLOCKED` — revue rôle-séparée mais non identité-indépendante.
- `BLOCKED` — merge signé, replay post-merge, promotion canonique et RAGLite manquent encore.

## Décision

Statut actuel : `PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE`.

Ce dossier et les documents de qualification créent un nouveau head. Son run exact final doit être enregistré dans la revue PR, afin d’éviter une auto-référence infinie.

Task 11 devient `PROVEN` uniquement après :

1. CI read-only sur le head final;
2. revue rôle-séparée sans finding matériel;
3. merge GitHub signé;
4. replay frais sur le merge exact de `main`;
5. promotion canonique;
6. projection RAGLite byte-identical.

Task 12 reste bloquée jusque-là.
