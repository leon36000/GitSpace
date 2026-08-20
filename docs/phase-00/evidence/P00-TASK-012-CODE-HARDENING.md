---
task_id: P00-TASK-012
evidence_type: LOCAL_CODE_HARDENING
status: PARTIALLY_VERIFIED
repository_head: 500a7d382133d0a2d948356d9c4eff6f6a393540
updated: 2026-08-20
---
# P00-TASK-012 — durcissement local Codex

Cette preuve couvre le commit d’implémentation local `500a7d382133d0a2d948356d9c4eff6f6a393540` et uniquement les comportements exécutables sans Harbor/Docker. Elle ne qualifie pas le worker, l’image runtime, le sidecar egress ni un oracle Harbor réel.

## Changements vérifiés

- Le record de replay passe en version `2` et sépare `exception_discriminant` de `exception_type_diagnostic`.
- `TIMEOUT` exige le discriminant souverain `agent_timeout_exact`, le stage `agent_execution`, l’absence de reward et les six obligations de phase exactes. Un nom d’exception JSON seul, un timeout setup/verifier/environment ou un stage divergent devient `INFRA`.
- Les obligations de phase et de cleanup ont des clés fermées et des booléens exacts. Le cleanup vérifie l’absence du process group, du temp root, des conteneurs, des réseaux et des images dérivées, ainsi que la préservation des ressources étrangères.
- La frontière d’exception est conservée comme artefact CAS et doit correspondre au record avant classification.
- JobConfig et TrialConfig effectifs sont revalidés après sérialisation Harbor : les champs de tâche, agent, environnement, UUID de job et `trial_name` généré sont fermés; les regrades, `install_only`, verifier désactivé, extra instructions et objets tâche additionnels sont rejetés.
- L’image environnement et le sidecar passent par l’extension Harbor supportée `gs_eval_adapters.harbor_runtime:GitSpaceHarborEnvironment`; les refs sont des références Docker digest-bound, et le worker injecte seulement le `PYTHONPATH` interne nécessaire à l’import.
- L’inventaire CAS lie exactement `source-manifest.json` et les sept fichiers runtime par chemin, hash et taille; les fichiers additionnels, symlinks et compose sont refusés, avec filtrage limité des `__pycache__`/`.pyc` transitoires.
- Un `HarborResourceObserver` est obligatoire sur l’exécuteur qualifié et produit les manifests before/after autour du processus Harbor. Sans observateur, le processus n’est pas lancé et la capture est `INFRA`.
- Les timings enregistrés sont comparés au `trial_result`. Un timeout agent exact peut ne pas avoir encore écrit les deux artefacts verifier; les autres incohérences restent `INFRA`.
- Le verifier normalisé produit atomiquement `reward.json` et `gitspace-result.json` pour `PASS`/`FAIL`; toute exception non fonctionnelle sort `70` sans reward; une reward préexistante est rejetée.
- Le manifeste de fixture lie les fichiers générés par SHA-256, taille et mode.

## Vérifications fraîches

```text
tests/adapters/harbor: 70 tests OK
tests fixture/verifier normalisés: 12 tests OK
mutations Harbor: 11/11 tuées
tests/adapters: 43 tests OK
Rust workspace: tests, clippy et fmt OK
Harbor CLI `run --help` sans job: OK
production mypy (adapter/replay/runtime): OK
ruff, compileall, lock check et diff check: OK
```

## Limites

- Aucun Harbor/Docker n’a été lancé sur PC1; le daemon est partagé/rootful et le projet l’interdit pour cette tâche.
- Le worker qualifié doit encore fournir les manifests de ressources indépendants, le SBOM/scanner, le sidecar egress, le run réel, la preuve CAS/replay et le cleanup physique.
- Aucun RED toolchain exact sur worker dédié, qualification runtime base/SBOM/scanner, oracle réel, CAS runtime, replay post-run, cleanup physique ou revue indépendante n’est prouvé ici.
- Le statut maximal reste `implementation_ready_external_runtime_blocked`; aucune promotion `PROVEN`, merge canonique ou projection RAGLite n’est autorisée par cette preuve.
