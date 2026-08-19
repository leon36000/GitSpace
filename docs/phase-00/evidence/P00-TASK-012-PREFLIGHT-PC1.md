---
evidence_id: P00-TASK-012-PREFLIGHT-PC1
status: EVIDENCE_NONQUALIFYING
observed_at_utc: 2026-08-18T01:52:50Z
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
host: pc1
observers: [codex, chatgpt_project_gitspace]
mutation_policy: READ_ONLY
---
# P00-TASK-012 — Préflight PC1

## Résultat

`NEEDS_DEDICATED_WORKER` et `EXACT_PROJECT_TOOLCHAIN_AVAILABLE=false`.

Cette observation ne constitue ni un run Harbor ni une preuve Task 12. Elle qualifie seulement l'aptitude de PC1 à héberger le RED exact et le futur run conteneur.

## Provenance

Deux sondes Codex ont été exécutées en lecture seule depuis des worktrees enfants propres basés sur `dcde1142cf76996a6ba0074cb7eab9d3c870c561`. Aucun package n'a été installé, aucune image n'a été pull/build/run, et aucun conteneur ni état Docker n'a été modifié.

Les deux workers ont d'abord rencontré `bwrap: No permissions to create new namespace`; ils ont ensuite exécuté les lectures autorisées sans Bubblewrap. Ce finding décrit la frontière d'exécution de PC1 et n'est pas présenté comme défaut GitSpace.

## Toolchain observé

```yaml
repository:
  head: dcde1142cf76996a6ba0074cb7eab9d3c870c561
  clean_in_probe_worktree: true
rust:
  rustc: 1.97.1
  cargo: 1.97.1
python:
  required: 3.12.13
  observed_python3: 3.12.3
  observed_python3_12: 3.12.3
  exact_3_12_13_offline_lookup: NOT_FOUND
uv:
  required: 0.12.0
  observed: 0.11.26
  exact_0_12_0_on_path: NOT_FOUND
```

La recherche `uv python find 3.12.13` a été effectuée avec `--offline --no-python-downloads --no-project --no-config`; aucun interpréteur 3.12.13 n'a été trouvé. Aucun téléchargement n'a été tenté.

## Docker observé

```yaml
docker:
  engine: 29.6.1
  api: 1.55
  architecture: x86_64
  os: Ubuntu 24.04.4 LTS
  storage: overlayfs/containerd-snapshotter
  root_dir: /media/pc1/Storage/Serveur/docker
  rootless: false
  cgroups: v2
  cgroup_driver: systemd
  buildx: 0.35.0
  default_runtime: nvidia
  containers_total: 17
  containers_running: 11
  images_total: 45
socket:
  path: /var/run/docker.sock
  exists: true
  mode: "0660"
  owner: nobody
  group: nogroup
qualification_tools:
  syft: NOT_FOUND
  grype: NOT_FOUND
  trivy: NOT_FOUND
  cosign: 2.4.1
  crane: NOT_FOUND
  skopeo: NOT_FOUND
```

## Classification rationale

Docker est disponible, donc `DOCKER_UNAVAILABLE` serait faux. Le daemon observé est néanmoins rootful et partagé avec des charges existantes; il ne satisfait pas le contrat `rootless_or_dedicated_disposable`. Les outils nécessaires à une fermeture reproductible des gates SBOM/vulnérabilités sont absents. En parallèle, Python et uv ne correspondent pas aux pins projet, donc PC1 ne peut pas produire le RED qualifiant tel que packetisé.

## Pairs distants

`pc2`, `pc3` et `pc4-grs-b` étaient joignables via Tailscale et leurs sondes SSH étaient vertes. Un lancement de worker sur `pc2` a été refusé par le contrôleur avec `remote worker launch requires a ForgeAI node agent; host health remains available`. Les autres pairs présentent la même absence de voie native de worker connue. Aucun contournement SSH manuel n'a été utilisé.

## Gate

```yaml
pc1_exact_red_gate: BLOCKED_WITH_EVIDENCE
pc1_runtime_gate: BLOCKED_WITH_EVIDENCE
remote_worker_gate: BLOCKED_WITH_EVIDENCE
reasons:
  - exact_python_3_12_13_missing
  - exact_uv_0_12_0_missing
  - shared_rootful_docker_daemon
  - sbom_and_vulnerability_scanners_missing
  - forgeai_node_agent_missing_on_remote_peers
```

## Prochaine action exacte

Conserver Task 12 au stade packetisation/revue. Avant tout code de production, fournir un environnement Python 3.12.13 + uv 0.12.0 et enregistrer le RED exact. Avant tout run Harbor réel, qualifier un worker rootless ou dédié jetable avec Docker/BuildKit et outils supply-chain pinés, puis qualifier la base runtime par digest `linux/amd64`, OCI manifest, SBOM et scan. Toute installation ou modification d'un hôte distant requiert une autorisation propriétaire distincte.
