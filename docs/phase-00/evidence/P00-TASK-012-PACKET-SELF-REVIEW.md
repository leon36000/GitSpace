---
evidence_id: P00-TASK-012-PACKET-SELF-REVIEW
status: PACKET_REVIEW_READY_BLOCKED_WITH_EVIDENCE
reviewed_at: 2026-08-18
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
reviewed_branch: agent/p00-task-012-packet-v4
reviewer: CHATGPT_PROJECT_GITSPACE
independent_identity: false
---
# P00-TASK-012 — Self-review du paquet v4

## Résultat

Le paquet v4 est **review-ready comme proposition documentaire**, pas accepté, pas canonique et pas exécutable au-delà de ce que ses gates autorisent. Le runtime Harbor reste `BLOCKED_WITH_EVIDENCE` et aucun code produit Task 12 n'est présent dans le diff.

```yaml
packet_schema: GS-EXEC-PACKET-001
packet_version: 4
packet_status: PROPOSED_REVIEW_READY_BLOCKED_WITH_EVIDENCE
self_review_status: PACKET_REVIEW_READY_BLOCKED_WITH_EVIDENCE
canonical_task_status: NOT_PACKETIZED_UNTIL_AUTHORIZED_MERGE
production_code_present: false
red_observed: false
runtime_qualified: false
independent_identity_review: false
```

## 1. Diff / portée

Comparaison fraîche :

```text
base: dcde1142cf76996a6ba0074cb7eab9d3c870c561
head: agent/p00-task-012-packet-v4
merge-base: dcde1142cf76996a6ba0074cb7eab9d3c870c561
behind: 0
```

Le diff contient uniquement :

```text
docs/phase-00/tasks/P00-TASK-012.md
docs/phase-00/evidence/P00-TASK-012-PREFLIGHT-PC1.md
docs/phase-00/evidence/P00-TASK-012-TOOLCHAIN-SUPPLY-CHAIN.md
docs/phase-00/evidence/P00-TASK-012-ADVERSARIAL-REVIEW-V4.md
docs/phase-00/evidence/P00-TASK-012-ADVERSARIAL-REVIEW-V4-ROUND2.md
docs/phase-00/evidence/P00-TASK-012-INTERFACE-CONTRACT.md
```

Aucun `python/`, `tests/`, `pyproject.toml`, `uv.lock`, `schemas/`, `crates/`, état canonique ou RAGLite n'est modifié par cette proposition.

## 2. Couverture GS-EXEC-PACKET-001

| Champ | Couverture |
|---|---|
| `task_id` | frontmatter |
| `packet_version` | frontmatter |
| `base_repository` | frontmatter |
| `base_commit` | frontmatter + §11 lineage |
| `goal` | §1 |
| `non_scope` | §4 |
| `applicable_decisions` | §3 |
| `risk_tier` | frontmatter `T3` |
| `allowed_paths` | §14 |
| `forbidden_paths` / effects | §16 |
| `read_only_paths` | §15 |
| `required_interfaces` | §6 + interface contract |
| `produced_interfaces` | §6 + interface contract |
| `preconditions` | §§2, 10, 11 |
| `test_first.command` | §11 |
| `test_first.expected_failure` | §11 exact `ModuleNotFoundError` |
| `implementation_constraints` | §§5–10, 16 |
| `verification_commands` | §17 |
| `expected_results` | §§9–12, 20 |
| `evidence_bundle` | §18 |
| `rollback` | §21 |
| `review_sequence` | §19 |
| `termination_conditions` | §20 |

Aucun champ obligatoire du packet schema n'est volontairement laissé `TBD`.

## 3. RED lineage corrigée

Le packet `base_commit` reste le canon frais `dcde114...`. Un RED externe commité ne prétend plus avoir ce même HEAD : il doit être un descendant test-only dont le merge-base est exactement `dcde114...`.

Le RED externe autorise seulement : packet/evidence, `tests/adapters/harbor/**`, workflow RED. Il interdit modules production et ajout Harbor à `pyproject.toml`/`uv.lock`. Le SHA exact du head RED doit être enregistré.

Échec attendu :

```text
ModuleNotFoundError: No module named 'gs_eval_adapters.harbor_replay'
```

Un autre échec est un RED invalide.

## 4. Pins et faits Harbor relus

Les valeurs suivantes ont été recoupées contre les sources primaires Harbor 0.21.0 :

```yaml
version: 0.21.0
tag: v0.21.0
commit: 64afbbcb62165950301e1a6407c729aa26d844ff
wheel_sha256: c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21
sdist_sha256: 93f7c2e4b150b2983a90b226c61daf071c35a9dd0f76e1053413d9ee0d738395
task_schema: "1.4"
```

Le packet encode explicitement les observations adversariales suivantes :

- `network_mode="no-network"`, pas nouveau recours au champ legacy `allow_internet`;
- `harbor run --config` pour un vrai Job 1×1;
- reward JSON entière, `reward.txt` interdit;
- `OracleAgent` non-zéro traité fail-closed;
- telemetry Harbor désactivée;
- verifier partagé mais tests uploadés seulement après agent;
- sidecar egress Harbor préqualifié avant run;
- process return code Harbor conservé et non-zéro => `INFRA`.

## 5. Compatibilité Task 10

Le SDK Task 10 a été relu :

```text
validate task+agent
→ adapter.prepare
→ exact canonical_request comparison
→ adapter.invoke
→ adapter.collect
→ exact result keys: status/summary/artifacts/metrics/extensions
→ AdapterResult with descriptor identity injected by SDK
```

Le contrat Harbor respecte cette frontière. `collect` ne renvoie pas lui-même `adapter_identity`.

## 6. Contradictions recherchées

Recherches ciblées et dispositions :

| Risque | Disposition v4 |
|---|---|
| infra comptée FAIL | interdit; précédence POLICY→INFRA→TIMEOUT→terminal |
| oracle référence reward 0 = agent FAIL | interdit; INFRA + task-invalid candidate |
| reward `1` transformée en float | `reward.json` exact int uniquement |
| CLI trial sans job artifact | rejet; `harbor run` Job 1×1 |
| build/pull caché pendant run | images tâche+sidecar préqualifiées, daemon egress bloqué |
| tests visibles à l'agent | verifier shared, upload post-agent exigé |
| telemetry externe | `HARBOR_TELEMETRY=0` |
| faux digest runtime | runtime reste `BLOCKED_TO_QUALIFY` |
| vieux `allow_internet` comme contrôle | interdit dans fixture normalisée |
| absence normale `exit-code.txt` | `oracle_exit_status` obligatoire + raw conditionnel |
| erreur CLI perdue | `harbor_process_return_code` dans replay |
| statut Harbor inventé | `completed|exception` dérivé de `TrialResult.exception_info` |
| replay dépend de Harbor | imports Harbor/Docker/subprocess interdits dans replay |
| loader CAS absent | `INFRA`, jamais succès |
| daemon PC1 partagé implicitement accepté | explicitement bloqué |

Aucune contradiction matérielle supplémentaire n'a été identifiée dans cette passe. Cette phrase est une conclusion de revue documentaire, pas une preuve runtime.

## 7. Limites non fermées

```yaml
red_observed: false
harbor_dependency_locked_in_gitspace: false
runtime_parent_python_3_13_15_digest: unknown
runtime_derived_image_id: unknown
harbor_sidecar_image_id: unknown
sbom_scan_runtime: missing
qualified_docker_worker: missing
real_harbor_job: not_run
cas_replay: not_run
mutations: not_run
independent_identity_review: missing
signed_merge: missing
postmerge_replay: missing
```

Ces limites empêchent toute promotion `PROVEN` et empêchent le démarrage de Task 13.

## 8. Décision de self-review

```text
PACKET_REVIEW_READY_BLOCKED_WITH_EVIDENCE
```

Cela signifie seulement : la proposition documentaire est suffisamment fermée pour être soumise à revue/acceptation. Cela ne signifie pas Task 12 exécutée, GREEN, vérifiée ou prouvée.

## 9. Next exact action

Ouvrir une PR **draft** de `agent/p00-task-012-packet-v4` vers `main`, vérifier son diff exact, collecter toute revue/CI disponible, puis accepter/fusionner le packet documentaire seulement si aucune finding matérielle n'est ouverte. Après merge, rebaser la packetisation d'exécution depuis le nouveau `main` et créer le RED test-only avant tout module production.
