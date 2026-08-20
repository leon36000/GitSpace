---
task_id: P00-TASK-012
evidence_type: LOCAL_CODE_HARDENING
status: PARTIALLY_VERIFIED
repository_head: 380fbe1
updated: 2026-08-20
---
# P00-TASK-012 — durcissement local Codex

Cette preuve couvre le commit d’implémentation `380fbe1` et uniquement les comportements exécutables sans Harbor/Docker. Elle ne qualifie pas le worker, l’image runtime, le sidecar egress ni un oracle Harbor réel.

## Changements vérifiés

- Le record de replay passe en version `2` et sépare `exception_discriminant` de `exception_type_diagnostic`.
- `TIMEOUT` exige le discriminant souverain `agent_timeout_exact`, le stage `agent_execution`, l’absence de reward et les six obligations de phase exactes. Un nom d’exception JSON seul, un timeout setup/verifier/environment ou un stage divergent devient `INFRA`.
- Les obligations de phase et de cleanup ont des clés fermées et des booléens exacts. Le cleanup vérifie l’absence du process group, du temp root, des conteneurs, des réseaux et des images dérivées, ainsi que la préservation des ressources étrangères.
- La frontière d’exception est conservée comme artefact CAS et doit correspondre au record avant classification.
- Le verifier normalisé produit atomiquement `reward.json` et `gitspace-result.json` pour `PASS`/`FAIL`; toute exception non fonctionnelle sort `70` sans reward; une reward préexistante est rejetée.
- Le manifeste de fixture lie les fichiers générés par SHA-256, taille et mode.

## Vérifications fraîches

```text
tests/adapters/harbor: 53 tests OK
mutations Harbor: 11/11 tuées
tests/adapters: 43 tests OK
tests/contracts ciblés: 13 tests OK
uv lock --check: OK
compileall Python ciblé: OK
```

## Limites

- Aucun Harbor/Docker n’a été lancé sur PC1; le daemon est partagé/rootful et le projet l’interdit pour cette tâche.
- Aucun RED toolchain exact sur worker dédié, qualification runtime base/SBOM/scanner, oracle réel, CAS runtime, replay post-run, cleanup physique ou revue indépendante n’est prouvé ici.
- Le statut maximal reste `implementation_ready_external_runtime_blocked`; aucune promotion `PROVEN`, merge canonique ou projection RAGLite n’est autorisée par cette preuve.
