---
task_id: P00-TASK-012
evidence_type: ROOTLESS_RUNTIME_POSITIVE_PATH
status: PARTIALLY_VERIFIED
implementation_commit: 0ea1acefb2454dcf3d5706cb58dc66c77f8a8322
updated: 2026-08-20
---
# P00-TASK-012 — chemin Harbor réel positif

Cette preuve documente un chemin positif réellement exécuté après le commit
`0ea1acefb2454dcf3d5706cb58dc66c77f8a8322`. Elle ne vaut pas qualification
formelle complète ni promotion `PROVEN`.

## Worker et pins observés

- Worker Docker dédié rootless jetable : `linux/amd64`, Docker `29.6.1`,
  driver `overlayfs`, options de sécurité `rootless` et `cgroupns`.
- uv exact `0.12.0`, binaire téléchargé :
  `b6e3cb5b4858d920c63e1d88e31a7a4d8f567073ee4e5e4a1889f93984dc28ea`.
- Python du projet : `3.12.13`.
- mypy `2.3.0`, déclaré dans le groupe dev et présent dans `uv.lock`;
  `uv run --frozen --no-build mypy ...` résout `.venv/bin/mypy`.
- Harbor `0.21.0`, commit
  `64afbbcb62165950301e1a6407c729aa26d844ff`.
- Image tâche :
  `gitspace-p00/regex-log@sha256:63dbf5cd3a8fb6dab72c4a99bb972564bc3d725d134355f1312991a57cb2f06b`
  (`linux/amd64`).
- Sidecar egress :
  `harbor-prebuilt@sha256:6e12f40cb0f39ade388d0330e50be5d5e7a067545de2b0eea97c6c3a045d3e4a`
  (`linux/amd64`).

Le run a utilisé `uv run --frozen --no-build`, Harbor `run --config`, une
tentative, une trial, l’agent `oracle`, le réseau `no-network` et un
observateur de ressources avant/après lié au record.

## Résultat frais

- Harbor process return code : `0`.
- Job : `58061379-ffb2-40f4-b7d9-fae9beb03b53`.
- Trial : `fcf1ecbe-6abe-4495-a105-5f5f2952b5c5`, nom
  `terminal-bench-2.1-regex-log__diQfZUd`.
- Reward : `1`; statut adapter/replay : `pass`.
- Record CAS :
  `sha256:cabf877ef98dca901df2eb8a88df6be97eabb23a0bad31f84b003ee7e2690b1e`.
- Avant : 9 ressources observées, dont deux ressources GitSpace de scope
  process/temp et sept ressources Docker étrangères.
- Après : 7 ressources étrangères, aucune ressource attribuée à GitSpace;
  état étranger inchangé.
- Cleanup dérivé : process group, temp root, containers, networks et images
  dérivées absents; `foreign_resources_untouched=true`.
- Les obligations `artifact_integrity`, `qualification_pinned`,
  `job_cardinality_one`, `trial_cardinality_one`, `network_closed`,
  `reward_well_typed`, `stage_obligations_consistent`, `oracle_exit_consistent`
  et `infra_clear` sont vraies. `timeout_attribution_valid=false` est attendu
  pour un chemin sans timeout.

## Portée et gates restantes

Ce résultat prouve le chemin positif de l’exécuteur, la fixture, le sidecar
préchargé, la reward, le CAS/replay et le cleanup observé sur ce worker. Il ne
ferme pas encore :

- SBOM SPDX 2.3, provenance OCI, scanner et base de vulnérabilités fraîches;
- dispositions signées pour les vulnérabilités HIGH/CRITICAL;
- preuve indépendante de non-egress et revue sécurité/conformité séparée;
- exact-head/worktree propre au moment de la qualification formelle;
- replay post-merge sur `main`, signature de merge et promotion d’état.

Le statut correct reste donc `PARTIALLY_VERIFIED`; aucune déclaration
`PROVEN` n’est autorisée sur cette seule exécution.
