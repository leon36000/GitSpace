---
evidence_id: P00-TASK-012-INTERFACE-CONTRACT
status: PROPOSED_INTERFACE_CONTRACT
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
packet_ref: docs/phase-00/tasks/P00-TASK-012.md@packet_version=4
updated: 2026-08-18
---
# P00-TASK-012 — Contrat exact des interfaces Harbor

Ce document ferme les signatures nommées par le paquet Task 12. Il n'autorise aucun code avant le RED exact. Le module replay reste importable avec Harbor, Docker et `subprocess` indisponibles.

## 1. Constantes qualifiées

```python
HARBOR_VERSION: Final[str] = "0.21.0"
HARBOR_TAG: Final[str] = "v0.21.0"
HARBOR_COMMIT: Final[str] = "64afbbcb62165950301e1a6407c729aa26d844ff"
HARBOR_WHEEL_SHA256: Final[str] = (
    "c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21"
)
TERMINAL_BENCH_COMMIT: Final[str] = (
    "7131e4375048a0e408a8fb404b5f499d726b695b"
)
TERMINAL_BENCH_TASK: Final[str] = "terminal-bench/regex-log"
```

Les valeurs sont revalidées par les qualifications versionnées; ces constantes ne remplacent pas leurs preuves.

## 2. Replay record

```python
@dataclass(frozen=True, slots=True)
class HarborReplayRecord:
    version: int
    run_purpose: str
    framework: str
    framework_version: str
    framework_commit: str
    framework_wheel_sha256: str
    dataset_repository: str
    dataset_commit: str
    task_name: str
    source_task_sha256: str
    normalized_task_sha256: str
    environment_image_ref: str
    environment_image_id: str
    environment_platform: str
    runtime_network_mode: str
    verifier_environment_mode: str
    verifier_python: str
    agent: str
    oracle_exit_code: int | None
    job_id: str
    trial_id: str
    harbor_process_return_code: int
    harbor_status: str
    observed_reward: int | None
    exception_type: str | None
    exception_stage: str | None
    stage_timings: dict[str, JsonValue]
    artifacts: dict[str, str]
    artifact_sha256: dict[str, str]
    cleanup_obligations: dict[str, bool]

    @classmethod
    def from_json(cls, value: object) -> "HarborReplayRecord": ...
    def to_json(self) -> JsonObject: ...
```

Règles :

- `version == 1` exact int non-bool;
- `run_purpose` exactement `qualification_oracle | status_control`;
- framework/version/commit/wheel et dataset commit exactement pinés;
- `environment_platform == "linux/amd64"`;
- `runtime_network_mode == "no-network"`;
- `verifier_environment_mode == "shared"`;
- `verifier_python == "3.13.15"` pour `qualification_oracle`;
- `agent == "oracle"` pour `qualification_oracle`;
- `harbor_process_return_code` exact int non-bool;
- `harbor_status` exactement `completed | exception` et dérivé de la présence de `TrialResult.exception_info`, jamais d'un message texte;
- reward `None | exact int 0 | exact int 1`, jamais bool/float;
- `exception_stage` vaut `None | environment_setup | agent_setup | agent_execution | verifier | unknown`;
- IDs non vides, bornés et sans contrôle Unicode;
- maps exactes, builtins JSON profonds uniquement;
- URI artefact `cas://sha256/<64hex>` uniquement;
- chaque `artifact_sha256[name]` vaut `sha256:<64hex>` et possède la même key que l'artefact correspondant;
- `cleanup_obligations` contient un set fermé de bool exacts.

Un `harbor_process_return_code != 0` est toujours `INFRA`, même si des fichiers partiels semblent fonctionnels. `harbor_status="exception"` n'est jamais à lui seul un `FAIL`: la classification dépend du type structuré, du stage et des gates supérieures.

## 3. Replay result

```python
@dataclass(frozen=True, slots=True)
class HarborReplayResult:
    status: AdapterStatus
    obligations: dict[str, bool]
    record_sha256: str
    task_invalid_candidate: bool

    def to_json(self) -> JsonObject: ...
```

Obligations fermées :

```text
qualification_pinned
run_purpose_valid
process_exit_zero
network_closed
job_cardinality_one
trial_cardinality_one
reward_well_typed
oracle_exit_consistent
artifact_integrity
cleanup_complete
policy_clear
infra_clear
timeout_attribution_valid
```

`task_invalid_candidate` est `true` uniquement pour un défaut de la référence/normalisation qualifiante (par exemple oracle exit non-zéro ou oracle reward `0` avec infra autrement saine). Ce champ ne promeut jamais lui-même l'état canonique `TASK_INVALID`.

## 4. Projection Harbor-free

```python
def project_harbor_capture(capture: object) -> JsonObject: ...
```

Entrée : builtins JSON profonds uniquement, produits par la couche adapter après extraction de `job/config.json`, `job/result.json`, `trial/config.json`, `trial/result.json`, return code Harbor, reward, exception, timings, oracle exit status, ressources et cleanup.

Le projecteur :

- exige exactement un job et un trial pour un record complet;
- extrait seulement les champs explicitement qualifiés;
- dérive `harbor_status` de `TrialResult.exception_info is None`;
- attribue `exception_stage` depuis types structurés et timings fermés; si le stage ne peut pas être démontré, il vaut `unknown` et la classification est `INFRA`;
- ignore aucune clé inconnue : champ inconnu dans le noyau fermé => erreur contrat;
- traite les noms/types/messages Harbor comme données non fiables;
- ne lit aucun fichier, ne lance aucun process, ne contacte aucun runtime;
- retourne une projection JSON profonde et copiée.

## 5. Construction du record et binding CAS

```python
def build_replay_record(
    projection: object,
    *,
    artifact_bytes: dict[str, bytes],
    artifact_uris: dict[str, str],
) -> HarborReplayRecord: ...
```

Règles :

1. `artifact_bytes` et `artifact_uris` sont des dict exacts.
2. Les keys obligatoires correspondent au paquet; `oracle_exit_code` est la seule key conditionnelle.
3. Chaque valeur `artifact_bytes` est `bytes` exact.
4. SHA-256 recalculé depuis les bytes.
5. Chaque URI CAS doit correspondre exactement au digest recalculé.
6. `harbor_stdout` et `harbor_stderr` sont toujours conservés, même vides.
7. `oracle_exit_status` est toujours obligatoire; le raw `oracle_exit_code` n'existe que si `present=true`.
8. Si `present=false`, `oracle_exit_code` raw doit être absent.
9. Si `present=true`, le raw doit exister, parser en exact int non-bool et égaler `value`.
10. Le record contient seulement les URI et digests, jamais les blobs.

## 6. Canonical record

```python
def canonical_record_bytes(record: HarborReplayRecord) -> bytes: ...
```

- refuse tout type différent de `HarborReplayRecord`;
- revalide le record après construction;
- JSON UTF-8, clés triées, séparateurs compacts, `allow_nan=False`;
- aucune timestamp volatile n'est ajoutée par cette fonction.

## 7. Classification / replay

```python
def classify_harbor_record(
    record: HarborReplayRecord | object,
    *,
    read_artifact: Callable[[str], bytes] | None,
) -> HarborReplayResult: ...
```

Règles :

- `read_artifact=None` => `INFRA`, `artifact_integrity=false`, jamais PASS/FAIL/TIMEOUT/POLICY;
- loader appelé uniquement avec URI CAS déjà validées;
- chaque blob est re-hashé et comparé à `artifact_sha256`;
- loader absent, exception loader, blob non-bytes, blob manquant ou digest divergent => `INFRA`;
- aucune écriture/réparation CAS;
- précédence : `POLICY → INFRA → TIMEOUT → terminal`;
- `harbor_process_return_code != 0` => `INFRA` avant toute reward;
- `exception_stage="unknown"` avec exception présente => `INFRA`;
- `qualification_oracle` : terminal fonctionnel admissible = PASS seulement; reward 0 ou oracle exit non-zéro => INFRA + `task_invalid_candidate=true`;
- `status_control` : PASS ou FAIL selon reward 1/0 après gates;
- TIMEOUT uniquement exact `AgentTimeoutError` attribué à `agent_execution`;
- exception Harbor inconnue => INFRA;
- message texte d'une exception ne crée jamais POLICY.

## 8. Adapter-side executor seam

Ces types vivent dans `harbor_adapter.py`; ils ne traversent pas le résultat canonique.

```python
@dataclass(frozen=True, slots=True)
class HarborExecutionRequest:
    run_root: str
    fixture_root: str
    job_config: dict[str, JsonValue]
    environment_image_ref: str
    environment_image_id: str
    egress_sidecar_image_ref: str
    egress_sidecar_image_id: str


@dataclass(frozen=True, slots=True)
class HarborExecutionCapture:
    process_return_code: int
    harbor_stdout: bytes
    harbor_stderr: bytes
    job_config_bytes: bytes
    job_result_bytes: bytes
    trial_config_bytes: bytes
    trial_result_bytes: bytes
    agent_stdout: bytes
    agent_stderr: bytes
    oracle_exit_code_bytes: bytes | None
    verifier_stdout: bytes
    verifier_stderr: bytes
    verifier_reward_json_bytes: bytes | None
    resource_manifest_before_bytes: bytes
    resource_manifest_after_bytes: bytes
    cleanup_report_bytes: bytes


class HarborExecutor(Protocol):
    def run_oracle(
        self,
        request: HarborExecutionRequest,
    ) -> HarborExecutionCapture: ...
```

`HarborExecutionRequest` est construit seulement depuis valeurs internes revalidées; aucun path utilisateur brut n'est accepté comme commande. Le real executor est la seule couche autorisée à importer `subprocess` ou à lancer Harbor. Le fake executor des tests ne lance aucun process.

## 9. Adapter public API

```python
class HarborAdapter:
    descriptor: AdapterDescriptor

    def __init__(
        self,
        publish_artifact: Callable[[bytes], str],
        *,
        executor: HarborExecutor,
        read_artifact: Callable[[str], bytes] | None = None,
    ) -> None: ...

    def prepare(self, request: dict[str, JsonValue]) -> dict[str, JsonValue]: ...
    def invoke(self, prepared: dict[str, JsonValue]) -> dict[str, JsonValue]: ...
    def collect(self, raw: dict[str, JsonValue]) -> dict[str, JsonValue]: ...
```

- `prepare` reçoit déjà une requête validée par Task 10; il la copie sans perte avant tout accès Harbor/runtime;
- `invoke` revalide le snapshot préparé avant real/fake executor;
- `collect` reconstruit le record, vérifie le binding CAS, appelle le replay avec loader, puis retourne un payload Task 10 JSON;
- classes/exceptions Harbor ne traversent jamais ces retours;
- le descriptor est piné à Harbor 0.21.0 + digest d'implémentation GitSpace calculé par la discipline Task 10.

## 10. Compatibilité Task 10

`execute_adapter` valide Task + Agent avant `prepare`, force l'égalité du `canonical_request` avant `invoke`, puis normalise `collect` vers `AdapterResult`.

Le payload final `collect` doit donc contenir exactement :

```text
status
summary
artifacts
metrics
extensions
```

avec :

```text
status     : une valeur AdapterStatus
summary    : texte Unicode mono-ligne borné
artifacts  : URI CAS uniquement
metrics    : exact int/float fini non-bool uniquement
extensions : JSON profond namespacé gitspace.harbor
```

L'`adapter_identity` est injectée par le SDK depuis `descriptor.identity`; `collect` ne la duplique pas. Aucun score Harbor ne devient autorité; les métriques sont observatoires.

## 11. RED lié à ce contrat

Le premier RED importe `gs_eval_adapters.harbor_replay` et échoue uniquement parce que le module n'existe pas. Le premier GREEN implémente seulement le record/result et la classification `status_control` minimale exigée par ce test; le seam executor et l'adapter arrivent dans des RED ultérieurs.
