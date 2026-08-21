---
task_id: P00-TASK-012
evidence_type: CODE_HARDENING_AND_ROOTLESS_POSITIVE_PATH
status: PARTIALLY_VERIFIED
repository_head: 0ea1acefb2454dcf3d5706cb58dc66c77f8a8322
updated: 2026-08-20
---
# P00-TASK-012 — durcissement local Codex

Cette preuve couvre le commit `0ea1acefb2454dcf3d5706cb58dc66c77f8a8322`, les comportements locaux et un chemin Harbor/Docker réel exécuté sur un worker Linux/amd64 rootless dédié. Elle ne constitue pas encore la qualification formelle complète.

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
tests Harbor/exécuteur/replay: 81 méthodes de test OK, 11 sous-tests OK
tests fixture/verifier normalisés: OK
mutations SDK: 19/19 tuées
mutations Harbor: 11/11 tuées
tests/adapters: 43 méthodes de test OK
Rust workspace: tests, clippy et fmt OK
Harbor CLI `run --help` sans job: OK
mypy 2.3.0 verrouillé (adapter/replay/runtime): OK
ruff, compileall, lock check et diff check: OK

## Chemin runtime positif

Sur le worker rootless dédié, Harbor `0.21.0` a exécuté la fixture avec
reward `1`, statut `pass`, une trial et zéro retry. Job
`58061379-ffb2-40f4-b7d9-fae9beb03b53`, trial
`fcf1ecbe-6abe-4495-a105-5f5f2952b5c5`, record
`sha256:cabf877ef98dca901df2eb8a88df6be97eabb23a0bad31f84b003ee7e2690b1e`.
Le cleanup a laissé zéro ressource GitSpace attribuée et les ressources
étrangères inchangées. Le détail reproductible est dans
`P00-TASK-012-RUNTIME-POSITIVE-PATH.md`.
```

## Limites

- Le chemin positif ne ferme pas le SBOM SPDX 2.3, la provenance OCI, le scanner et sa base fraîche, les dispositions de vulnérabilités, ni la revue indépendante de sécurité/conformité et de non-egress.
- Le replay post-merge sur `main`, la signature de merge et la promotion d’état restent à produire.
- Le statut maximal reste `PARTIALLY_VERIFIED`; aucune promotion `PROVEN`, merge canonique ou projection RAGLite n’est autorisée par cette preuve seule.
