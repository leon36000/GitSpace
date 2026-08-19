---
evidence_id: P00-TASK-012-ADVERSARIAL-REVIEW-V4
status: REVIEW_FINDINGS_REQUIRING_PACKET_AMENDMENT
reviewed_at: 2026-08-18
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
reviewed_branch: agent/p00-task-012-packet-v3
reviewer: CHATGPT_PROJECT_GITSPACE
scope: packet_semantics_against_harbor_0_21_0_and_terminal_bench_regex_log
---
# P00-TASK-012 — Revue adversariale du paquet v3

## Verdict de revue

`P00-TASK-012` v3 reste une proposition utile mais n'est pas exécutable telle quelle. Cinq findings matériels doivent être corrigés avant acceptation du paquet. Aucun finding n'autorise du code de production avant le RED exact.

```yaml
packet_v3: PARTIALLY_VERIFIED_PROPOSAL
review_result: CHANGES_REQUIRED
production_code_authorized: false
harbor_runtime_authorized: false
canonical_state_changed: false
```

## F1 — Politique réseau Harbor 0.21.0

**Sévérité : élevée.**

Le paquet v3 normalise `task.toml` avec `allow_internet=false`. Harbor 0.21.0 expose désormais la politique explicite `network_mode = "no-network"`; `allow_internet` est un champ de compatibilité déprécié migré par validation puis effacé.

### Correction obligatoire

La fixture normalisée doit :

- utiliser le schéma Harbor courant qualifié;
- écrire explicitement `network_mode = "no-network"` pour l'environnement agent;
- ne pas émettre `allow_internet` dans le TOML normalisé;
- garder le champ amont `allow_internet=true` uniquement dans la provenance de la tâche source;
- vérifier après parsing Harbor que la politique effective est `no-network`.

Une compatibilité legacy qui transforme silencieusement `allow_internet=false` n'est pas une preuve suffisante pour une nouvelle fixture GitSpace.

## F2 — Contradiction job / trial

**Sévérité : élevée.**

Le paquet exige exactement un job et un trial et liste `job_config`/`job_result` parmi les artefacts, mais ne ferme pas l'entrée CLI exacte. `harbor trial start` ne crée qu'un trial. Le contrat 1×1 doit utiliser le chemin job.

### Correction obligatoire

La voie réelle qualifiée devient :

```text
<venv>/bin/harbor run --config <absolute-job-config.json>
```

avec :

```yaml
n_attempts: 1
n_concurrent_trials: 1
retry.max_retries: 0
agents:
  - name: oracle
    n_concurrent: 1
tasks:
  - path: <absolute-normalized-fixture>
upload: false
```

Les valeurs effectives doivent être revalidées depuis `config.json`, `result.json` et le trial enfant. Toute cardinalité différente de `1 job / 1 trial` devient `INFRA`.

`harbor trial start` est hors contrat Task 12 pour le run qualifiant.

## F3 — Exit code de l'OracleAgent

**Sévérité : critique pour la classification.**

Dans Harbor 0.21.0, `OracleAgent.run` écrit `exit-code.txt` lorsque `solve.sh` retourne non-zéro mais ne lève pas automatiquement `NonZeroAgentExitCodeError`. Un verifier peut donc encore produire une reward après un échec du script de référence.

### Correction obligatoire

Pour le run `qualification_oracle` :

- `agent/exit-code.txt` absent signifie succès process implicite;
- s'il existe, son contenu doit être l'entier exact `0` pour poursuivre;
- valeur non-zéro, absente alors qu'un autre artefact indique un échec, malformée ou contradictoire => `INFRA` et candidat `TASK_INVALID` au niveau de la tâche;
- une reward `0` issue du vrai agent `oracle` ne doit jamais être présentée comme échec d'un agent évalué;
- le chemin `FAIL` reste testé par contrôles synthétiques/fake executor de classification, pas par l'oracle de référence qualifiant.

## F4 — `reward.txt` détruit le type entier

**Sévérité : critique pour la fermeture PASS/FAIL exacte.**

Le verifier Harbor parse `reward.txt` par `float(...)`. Ainsi le texte `1` devient `1.0`, ce qui contredit l'invariant v3 `observed_reward` = exact `int` non-bool `0|1`.

### Correction obligatoire

La fixture normalisée doit écrire exclusivement :

```json
{"reward":1}
```

ou :

```json
{"reward":0}
```

vers `/logs/verifier/reward.json`.

Le runner ne doit pas créer `reward.txt`. Harbor priorise `reward.json`; le JSON natif conserve l'entier. Toute valeur float, bool, clé supplémentaire inattendue, valeur hors `0|1`, reward manquante ou double fichier ambigu devient `INFRA`.

## F5 — Python du verifier conteneur non qualifié

**Sévérité : élevée.**

L'environnement source `regex-log` part de `ubuntu:24.04`; son verifier installe dynamiquement `uv` puis demande Python `3.13`. Le runner normalisé `run_test.py` utilise directement la bibliothèque standard Python. La suppression du bootstrap réseau crée donc une nouvelle dépendance runtime : un interpréteur Python doit être présent dans l'image normalisée.

Python 3.13.15 est la release 3.13 courante observée le 2026-08-18. La source Docker Official Image consultée lors de cette revue restait encore générée avec Python 3.13.14. Aucun tag/digest 3.13.15 n'est donc promu par cette revue.

### Correction obligatoire

```yaml
normalized_verifier_python: 3.13.15
runtime_base_image: BLOCKED_TO_QUALIFY
runtime_base_requirements:
  - exact linux/amd64 digest
  - python3 reports exactly 3.13.15
  - /bin/bash available for solve.sh
  - no build-time dependency download in evaluated image build
  - OCI manifest CAS-bound
  - SBOM CAS-bound
  - scanner/version/database snapshot recorded
  - zero unresolved CRITICAL
  - HIGH requires explicit owner risk acceptance
```

Le choix final de l'image reste bloqué jusqu'à preuve supply-chain fraîche. Aucun tag mutable `python:3.13` ou `latest` n'est admissible.

## F6 — Clarification de l'isolation du verifier partagé

**Sévérité : moyenne, sécurité.**

Harbor 0.21.0 n'upload les tests dans l'environnement partagé qu'au moment de `Verifier.verify`, après la phase agent. Pour `regex-log`, le mode séparé ne retrouve pas automatiquement `/app/regex.txt`; il demanderait une transformation supplémentaire de l'oracle. Le chemin minimal qualifié reste donc le verifier partagé, mais avec une obligation explicite de phase.

### Correction obligatoire

- `verifier.environment_mode = "shared"` explicite;
- tests absents de l'environnement avant fin de l'agent;
- `OracleAgent` qualifiant limité au `solve.sh` verrouillé;
- aucun processus agent résiduel avant upload des tests;
- réseau effectif `no-network` pendant agent et verifier;
- toute présence anticipée des tests ou processus agent résiduel => `POLICY` ou `INFRA` selon attribution, jamais PASS/FAIL.

## F7 — Télémétrie Harbor

**Sévérité : moyenne, effet externe.**

Harbor 0.21.0 active une télémétrie PostHog sauf si `HARBOR_TELEMETRY` vaut une valeur désactivante. Le run qualifiant ne doit pas créer d'effet réseau hôte implicite.

### Correction obligatoire

L'environnement process allowlist doit fixer exactement :

```text
HARBOR_TELEMETRY=0
```

et utiliser HOME/TMP/XDG dédiés. Aucun credential store utilisateur n'est hérité. `DOCKER_HOST`/`XDG_RUNTIME_DIR` ne sont transmis que s'ils sont explicitement liés au worker qualifié.

## Amendements de classification

Pour `run_purpose = qualification_oracle` :

```text
POLICY
→ INFRA
→ TIMEOUT
→ PASS
```

`FAIL` n'est pas un résultat terminal admissible du vrai oracle de référence. Un oracle reward `0` ou exit non-zéro est `INFRA` et déclenche une revue `TASK_INVALID`/normalisation.

Pour les contrôles synthétiques/fake executor utilisés pour prouver la portabilité des cinq statuts :

```text
POLICY
→ INFRA
→ TIMEOUT
→ PASS | FAIL
```

Le record doit porter un `run_purpose` fermé (`qualification_oracle` ou `status_control`) pour empêcher une récompense d'oracle d'être requalifiée en FAIL.

## Sources primaires relues

- Harbor `v0.21.0`, commit source `64afbbcb62165950301e1a6407c729aa26d844ff`;
- `src/harbor/models/task/config.py` : réseau courant + migration legacy;
- `src/harbor/cli/main.py` et `src/harbor/cli/jobs.py` : `harbor run` et JobConfig;
- `src/harbor/trial/single_step.py` : ordre agent → artefacts → verifier;
- `src/harbor/trial/trial.py` : verifier partagé/séparé et écriture des résultats;
- `src/harbor/verifier/verifier.py` : upload tardif des tests et parsing reward;
- `src/harbor/agents/oracle.py` : comportement du script de référence;
- Terminal-Bench 2.1 `regex-log` commit `7131e4375048a0e408a8fb404b5f499d726b695b` : Dockerfile, `test_outputs.py`, `test.sh`, `solve.sh`.

## Décision

Le paquet v4 doit intégrer F1–F7 avant d'être proposé à acceptation. Tant que le RED exact, le worker, l'image et le run réel ne sont pas prouvés :

```yaml
P00-TASK-012: BLOCKED_WITH_EVIDENCE
P00-TASK-013: BLOCKED
false_done: false
```
