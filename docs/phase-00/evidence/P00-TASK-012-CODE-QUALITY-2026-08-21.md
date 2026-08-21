---
task_id: P00-TASK-012
evidence_type: CODE_QUALITY_AND_EXACT_HEAD
status: PARTIALLY_VERIFIED
repository_head: b3a3dc09c664d092d0360a4083433b78eb822023
updated: 2026-08-21
---

# P00-TASK-012 — preuve de qualité au head exact

Cette preuve couvre les refactorings `1651ef6`, `b8773cf` et `b3a3dc0` sur le
head exact `b3a3dc09c664d092d0360a4083433b78eb822023`. Les validations Harbor,
replay et adapter restent sémantiquement couvertes par les tests et les
mutations; aucune promotion `PROVEN` n'est déduite de cette preuve.

## Vérifications reproductibles

- Archive Git propre : `43` tests adaptateurs OK.
- Mutations Harbor : `11/11` tuées.
- `uv lock --check`, mypy des trois modules adapter/replay/runtime, Ruff,
  compileall et `git diff --check` : OK.
- Rust workspace : tests, clippy et fmt : OK.
- CI exact-head : Task 001, Task 010, Task 012 et GitGuardian : succès.

## Sonar exact-head

Le check Sonar `96735219177` a terminé `cancelled` avec cinq annotations, toutes
dans la fixture benchmark et aucune dans le code de production :

- `tests/adapters/harbor/fixtures/terminal-bench-2.1-regex-log/tests/test.sh`
  — trois recommandations sur les tests shell;
- `tests/adapters/harbor/fixtures/terminal-bench-2.1-regex-log/environment/Dockerfile`
  — deux recommandations sur la référence d'image et l'utilisateur par défaut.

Ces fichiers sont byte-liés par `source-manifest.json` et par le digest de la
fixture; ils n'ont pas été modifiés pour fabriquer un feu vert Sonar. La gate
Task 011 échoue donc honnêtement sur ces cinq annotations résiduelles.

## Garde de merge

Le PR #57 reste draft et `UNSTABLE`. Les gates formelles Task 012 restent
ouvertes : SBOM SPDX 2.3, provenance OCI, scanner/base fraîche et dispositions
de vulnérabilités, revue indépendante sécurité/conformité/non-egress,
qualification runtime sur exact-head, merge signé et replay post-merge sur
`main`. Aucun merge de `main`, promotion canonique ou projection RAGLite n'est
autorisé à ce stade.
