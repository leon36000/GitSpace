---
evidence_id: P00-TASK-010-VERDICT
status: PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE
recorded_at: 2026-08-14
base_commit: a5dc165ff78df74db35779695dd116c0b085a6a5
implementation_pr: 45
red_pr: 44
pre_final_head: 398ea125653496fe312a2512d6d0b1404c41ec38
pre_final_workflow_run: 31829611615
pre_final_workflow_job: 94861886711
identity_independent_review: false
---
# P00-TASK-010 — Verdict de vérification pré-merge

## Résultat sous revue

Task 10 ajoute une frontière Python provider-neutral entre l’Evaluation IR souverain de GitSpace et les frameworks externes :

```text
EvalTaskSpec + AgentConfiguration
→ validation locale Draft 2020-12
→ copie JSON canonique stricte
→ prepare + snapshot sémantique
→ invoke
→ collect
→ résultat normalisé PASS/FAIL/TIMEOUT/POLICY/INFRA
```

Aucune classe, exception, collection, valeur numérique non interopérable, identité forgée ou référence d’artefact externe ne peut traverser cette frontière comme donnée canonique.

## TDD RED initial

### RED corrigé

- branche : `agent/p00-task-010-red-v1`;
- PR fermée sans merge : #44;
- head : `07bcba61a25fa3a32a4b92cdddbff58b2aaa881e`;
- workflow : `31825786291`;
- job : `94849477467`;
- Python : `3.12.13`;
- permissions : `contents: read`;
- package produit : absent;
- erreur interne : `ModuleNotFoundError: No module named 'gs_eval_adapters'`;
- dépôt propre : PASS.

Le premier run avait déjà observé le bon import impossible, mais écrivait son log dans le checkout et violait son propre gate de propreté. Le log a été déplacé vers `/tmp`, sans ajouter de code produit, puis le RED a été réobservé.

## Dépendances verrouillées

```yaml
python: 3.12.13
uv: 0.12.0
jsonschema: 4.26.0
pyproject_blob: 194aa5f719526a813cec49b78cf8c162a2b60eb6
uv_lock_blob: e279733d2a0897679cec5f8a7cd7cde2a212b406
```

Le lock contient le package virtuel GitSpace et les dépendances résolues de `jsonschema` avec URLs, hashes et versions exactes. Aucun framework externe concret n’est ajouté.

## GREEN et findings adversariaux

### Premier GREEN complet

- workflow `31826454763`;
- job `94851641001`;
- contrats SDK, schémas Python, workspace Rust, Clippy et rustfmt : PASS.

### Finding — sous-classes Python et exceptions hostiles

Le RED `31826694790` / `94852394083` a démontré que :

- des sous-classes de `dict`, `list`, `str`, `int` ou `float` pouvaient être acceptées comme JSON;
- une propriété `descriptor` pouvait propager son exception;
- une exception externe dont `__str__` échoue pouvait casser la normalisation INFRA.

Correction : seuls les builtins exacts traversent la frontière; descriptor/method access est encapsulé; le type d’exception et un fallback déterministe remplacent toute stringification hostile.

### Finding — scalaires canoniques et ordre de validation

Le RED `31827077799` / `94853616585` a démontré :

- zéro négatif accepté;
- surrogates Unicode isolés acceptés;
- `repr` hostile d’une clé non-string déclenché pendant l’erreur;
- descriptor externe consulté avant rejet d’un EvalTaskSpec invalide.

Corrections : zéro négatif et surrogates refusés; aucune représentation externe avant validation de type; tâche et configuration validées avant le premier accès à l’adaptateur.

### Finding — constructeur public AdapterResult

Le RED `31827661778` / `94855529349` a démontré qu’un appelant pouvait construire directement un `AdapterResult` avec statut, artefact, métrique ou résumé invalide sans passer par `execute_adapter`.

Le RED `31827970831` / `94856568066` a ensuite démontré qu’une clé hostile pouvait encore déclencher `str(key)` dans cette voie directe.

Corrections : le constructeur public valide identité, statut typé, texte borné, noms, URI CAS, métriques finies, safe integers, zéro négatif, extensions et clés exactes avant tout formatage externe.

### Finding — identité, lookup et métadonnées hostiles

Le RED `31829183050` / `94860543008` a démontré :

- un entier gigantesque pouvait faire échouer la construction du message d’erreur;
- `AdapterRegistry.resolve` pouvait exécuter `__hash__` d’une clé externe;
- des métadonnées de type d’exception hostiles pouvaient casser la normalisation;
- un descriptor pouvait produire une identité non bornée;
- un `AdapterResult` direct pouvait accepter une identité structurée non canonique.

Corrections : les messages d’entier n’interpolent pas la valeur hostile; le registre valide une clé string exacte avant lookup; les labels de type sont bornés et extraits sans confiance dans `__module__`, `__name__`, `__qualname__` ou `__str__`; l’identité est bornée à 512 caractères et doit être exactement celle qu’un `AdapterDescriptor` canonique reproduirait.

## Preuve GREEN lecture seule

Head candidat avant l’ajout de ce dossier :

```text
398ea125653496fe312a2512d6d0b1404c41ec38
```

Workflow exact-head :

```yaml
run: 31829611615
job: 94861886711
checkout: detached_exact_head
os: Ubuntu 24.04
python: 3.12.13
uv: 0.12.0
rust: 1.97.1
permissions:
  contents: read
conclusion: success
```

Gates reproduits :

- `uv lock --check --python 3.12.13`;
- `uv sync --frozen`;
- identité exacte `jsonschema==4.26.0`;
- 43 tests contractuels et adversariaux Task 10;
- validation offline sans socket, y compris références HTTP/URN inconnues;
- `compileall`;
- contrat toolchain Python historique;
- 12 tests de schémas Evaluation IR souverains;
- replay depuis `git archive` sans métadonnées Git;
- workspace Rust complet verrouillé;
- Clippy `-D warnings`;
- rustfmt;
- dépôt propre.

## Mutation testing

Dix-neuf mutations critiques ont été injectées dans des copies jetables; toutes ont été tuées :

```text
skip-task-schema
skip-agent-schema
skip-semantic-snapshot
allow-unnamespaced-extension
allow-unsafe-integer
reflect-huge-integer-value
allow-nonfinite-float
allow-negative-zero
allow-nonstr-key
allow-arbitrary-artifact-uri
allow-prepared-core-fields
trust-exception-type-metadata
allow-incomplete-adapter
allow-descriptor-subclass
allow-nonstr-registry-lookup
allow-scalar-subclass
allow-unbounded-descriptor-identity
allow-noncanonical-result-identity
drop-result-core-check
```

```yaml
mutations: 19
killed: 19
survived: 0
```

## Propriétés vérifiées

1. EvalTaskSpec et AgentConfiguration sont validés avant toute propriété ou méthode externe.
2. Les huit schémas sont enregistrés localement; aucune résolution réseau n’est nécessaire ou tentée.
3. Seuls les builtins JSON exacts traversent : null, bool, string Unicode scalar-only, safe integer, float fini non négatif-zéro, list et dict à clés string exactes.
4. Cycles, profondeur excessive, sous-classes, objets arbitraires, tuples, sets, bytes, NaN, infinis, unsafe integers et surrogates échouent fermés.
5. Toute valeur acceptée est copiée en profondeur.
6. `prepare` doit conserver un snapshot canonique exact; toute perte sémantique bloque `invoke`.
7. Request, prepared et result ferment leurs champs core et exigent des extensions namespacées.
8. PASS, FAIL, TIMEOUT, POLICY et INFRA sont normalisés déterministement.
9. Timeout/policy externes restent distincts; les autres exceptions deviennent INFRA avec texte borné, single-line et résistant à `__str__` et métadonnées de type hostiles.
10. Artefacts = noms bornés + URI CAS canoniques seulement.
11. Métriques = noms bornés + nombres exacts, finis, non-bool, safe-range et non négatif-zéro.
12. Descriptor, identité et registre sont déterministes; adaptateurs incomplets, noms ou identités dupliqués échouent.
13. Lookup du registre n’exécute pas `__hash__` d’un objet non-string.
14. Le constructeur public `AdapterResult` ne contourne pas la frontière et exige une identité canonique bornée.
15. `to_json()` retourne une nouvelle copie JSON-only.
16. Deux exécutions identiques produisent des payloads JSON byte-équivalents avec clés triées.

## Portée vérifiée

La PR touche seulement :

- `pyproject.toml` et `uv.lock`;
- `python/gs_eval_adapters/**`;
- `tests/adapters/**`;
- workflow Task 10;
- packet et preuves Task 10.

Aucun schéma v1, crate Rust, CAS, journal, verdict, runner, Foundry, adaptateur concret, canon, RAGLite ou `hermesclaw-ci` n’est modifié.

## Limites et risques résiduels

- `LIMIT` — frontière in-process Python; aucune isolation de processus ou de mémoire native.
- `LIMIT` — aucun adaptateur Inspect, Harbor, SWE-bench ou AgentDojo n’est qualifié.
- `LIMIT` — le SDK valide et normalise les références d’artefacts, mais n’authentifie pas lui-même le contenu externe.
- `LIMIT` — la plage safe integer vise l’interopérabilité JSON multi-langage.
- `LIMIT` — le bornage des erreurs n’est pas une classification ou redaction complète des secrets.
- `LIMIT` — la sécurité des packages verrouillés n’est pas déclarée universellement prouvée par les tests fonctionnels.
- `BLOCKED` — la revue finale est rôle-séparée mais pas identité-indépendante.
- `BLOCKED` — merge signé, replay frais sur `main`, promotion canonique et projection RAGLite manquent encore.

## Décision

Statut actuel : `PARTIALLY_VERIFIED_PENDING_FINAL_HEAD_AND_MERGE`.

Le commit de ce dossier et les corrections documentaires créent un nouveau head. Son workflow exact doit donc être vérifié et enregistré dans la revue PR, pas inscrit ici, afin d’éviter une auto-référence infinie.

Task 10 devient `PROVEN` uniquement après :

1. succès read-only sur le head final incluant ce dossier;
2. revue rôle-séparée sans finding matériel;
3. merge GitHub signé;
4. replay frais sur le merge exact de `main`;
5. promotion d’état;
6. projection RAGLite byte-identical.

Task 11 reste bloquée jusque-là.
