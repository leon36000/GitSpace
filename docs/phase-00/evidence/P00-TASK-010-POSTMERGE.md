---
evidence_id: P00-TASK-010-POSTMERGE
status: PROVEN_BOUNDED_CONTRACT
recorded_at: 2026-08-14
implementation_pr: 45
review_id: 4940243975
merge_commit: 06e480d8869f4d2e5e5fce1a670f7074c5be854e
merge_tree: f1c451e1bb5806b46cc680ddf62e1518e9ef9d17
base_commit: a5dc165ff78df74db35779695dd116c0b085a6a5
postmerge_workflow_run: 31830147076
postmerge_workflow_job: 94863626878
identity_independent_review: false
---
# P00-TASK-010 — Preuve post-merge

## Verdict utile

`P00-TASK-010 = PROVEN` dans son contrat borné de frontière Python provider-neutral in-process.

La Phase 00 et le milestone M0 restent `PARTIALLY_VERIFIED`. Cette promotion ne qualifie aucun framework externe concret et ne remplace pas une revue indépendante par identité.

## Merge signé

GitHub a créé le commit squash :

```text
06e480d8869f4d2e5e5fce1a670f7074c5be854e
```

```yaml
parent: a5dc165ff78df74db35779695dd116c0b085a6a5
tree: f1c451e1bb5806b46cc680ddf62e1518e9ef9d17
verification:
  verified: true
  reason: valid
  verified_at: 2026-08-14T18:45:22Z
```

Le merge exact est la tête de `main`. `hermesclaw-ci` reste intacte à `91f55525b231116fd431430f46c87667e5c1f140`.

## Replay frais sur main

Le workflow final Task 10 a été déclenché par le push du merge signé :

```yaml
workflow: P00 Task 010 Adapter SDK
run: 31830147076
job: 94863626878
head: 06e480d8869f4d2e5e5fce1a670f7074c5be854e
checkout: detached_exact_head
os: Ubuntu 24.04
python: 3.12.13
uv: 0.12.0
jsonschema: 4.26.0
rust: 1.97.1
permissions:
  contents: read
conclusion: success
```

Le job a reproduit depuis les locks committés :

- `uv lock --check --python 3.12.13`;
- `uv sync --frozen`;
- identité exacte de `jsonschema==4.26.0`;
- 43 tests contractuels et adversariaux;
- 19/19 mutations critiques tuées;
- validation des schémas offline sans socket;
- compilation Python;
- contrats toolchain et schémas historiques;
- replay depuis `git archive` sans métadonnées Git;
- workspace Rust complet verrouillé;
- Clippy avec `-D warnings`;
- rustfmt;
- dépôt propre.

## Contrat prouvé

```text
EvalTaskSpec + AgentConfiguration
→ validation souveraine offline
→ copie JSON stricte
→ prepare avec snapshot canonique
→ invoke externe
→ collect
→ AdapterResult normalisé
```

Propriétés couvertes :

1. Task et configuration sont validés avant toute propriété ou méthode de l’adaptateur.
2. Les huit schémas Draft 2020-12 sont résolus localement; références HTTP/URN inconnues échouent sans réseau.
3. Seuls les builtins JSON exacts traversent : null, bool, string Unicode scalar-only, safe integer, float fini non négatif-zéro, list et dict à clés string exactes.
4. Sous-classes, objets arbitraires, bytes, tuples, sets, cycles, profondeur excessive, NaN, infinis, unsafe integers, zéro négatif et surrogates isolés échouent fermés.
5. Chaque arbre accepté est copié en profondeur.
6. Une divergence du snapshot canonique dans `prepare` bloque `invoke`.
7. Request, prepared et result ferment leurs champs core et exigent des extensions namespacées.
8. PASS, FAIL, TIMEOUT, POLICY et INFRA sont normalisés déterministement.
9. Les exceptions externes hostiles restent bornées, single-line et ne peuvent casser la frontière via `__str__`, `__module__`, `__name__`, `__qualname__`, `repr` ou `hash`.
10. Les artefacts sont uniquement des URI CAS canoniques.
11. Les métriques sont des nombres exacts, finis, non-bool, safe-range et non négatif-zéro.
12. Descriptor, identité, registre et résultat public sont déterministes et fail-closed.
13. Le constructeur public `AdapterResult` n’est pas une voie de contournement.
14. Deux entrées identiques et le même adaptateur factice produisent un JSON byte-équivalent.
15. Le workflow final est strictement en lecture seule.

## Mutation testing

```yaml
mutations: 19
killed: 19
survived: 0
```

Familles couvertes : validation task/agent, snapshot sémantique, extensions, nombres, zéro négatif, clés, URI CAS, champs core, métadonnées d’exception, adaptateur incomplet, sous-classe descriptor, lookup registre, sous-classe scalaire, identité bornée/canonique et result core.

## Mémoire négative conservée

- log RED écrit dans le checkout et cassant le gate de propreté;
- sous-classes Python acceptées comme JSON;
- descriptor/property et exception `__str__` hostiles;
- zéro négatif et surrogates Unicode isolés;
- accès à l’adaptateur avant validation du canon;
- voie directe `AdapterResult` moins stricte que le SDK;
- clés à `repr`, `str` ou `hash` hostiles;
- entier gigantesque cassant son propre message d’erreur;
- identité non bornée ou structurée de manière non canonique;
- métadonnées de type d’exception non fiables.

## Limites et risques résiduels

- `LIMIT` — frontière Python in-process; aucune isolation de processus ou de mémoire native.
- `LIMIT` — aucun adaptateur Inspect, Harbor, SWE-bench, Terminal-Bench ou AgentDojo n’est qualifié.
- `LIMIT` — le SDK valide les références CAS mais n’authentifie pas lui-même le contenu externe.
- `LIMIT` — safe integers visent l’interopérabilité JSON multi-langage.
- `LIMIT` — le bornage des erreurs n’est pas une classification/redaction complète des secrets.
- `LIMIT` — les tests fonctionnels et locks ne constituent pas une preuve universelle d’absence de vulnérabilité de dépendance.
- `BLOCKED` — aucune revue par une identité séparée n’est enregistrée.

## Décision

Task 10 est `PROVEN` uniquement dans la frontière bornée ci-dessus. La Phase 00 et M0 restent `PARTIALLY_VERIFIED`.

Task 11 peut être packetisée seulement après fusion de cette promotion d’état et de sa projection RAGLite byte-identical.
