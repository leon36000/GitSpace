---
task_id: P00-TASK-012
evidence_type: CODE_QUALITY_AND_EXACT_HEAD
status: PARTIALLY_VERIFIED
repository_head: 4b06fb2
updated: 2026-08-21
---

# P00-TASK-012 — preuve de qualité au head de correction

Cette preuve couvre le commit `4b06fb2`, qui corrige les cinq annotations
Sonar résiduelles dans la fixture normalisée sans modifier le code de
production Harbor.

## Corrections liées à la provenance

- `tests/test.sh` utilise désormais les tests Bash `[[ ... ]]` équivalents.
- Le Dockerfile conserve le même digest OCI mais retire le tag redondant de
  `FROM` et exécute la fixture avec l’utilisateur non-root `gitspace`.
- `source-manifest.json`, `TERMINAL_BENCH_RUNTIME_FILE_DIGESTS` et la
  qualification ont été recalculés; le digest normalisé est
  `sha256:dd86c081c48cc81b0d472122f791786d86bd6d2c9615948e8b32b3fdfafcf194`.
- L’ancienne qualification runtime est explicitement marquée historique et
  invalidée; aucune preuve Harbor antérieure n’est recyclée.

## Vérifications locales

- Tests adaptateurs : `43` OK.
- Tests Harbor/exécuteur/replay : `81` OK.
- Tests fixture/verifier normalisés : `12` OK.
- Mutations Harbor : `11/11` tuées.
- `uv lock --check`, mypy, Ruff, compileall, shell syntax, JSON et
  `git diff --check` : OK.

## Sonar et garde de merge

Le check Sonar antérieur avait cinq annotations dans la fixture. Le head
`4b06fb2` doit encore recevoir un check Sonar exact-head frais; son absence ne
peut pas être convertie localement en PASS. Les gates formelles Task 012
restent ouvertes : requalification runtime rootless, SBOM SPDX 2.3,
provenance OCI, scanner/base fraîche et dispositions, revue indépendante
sécurité/conformité/non-egress, merge signé et replay post-merge.

Le PR reste donc non fusionné et `PROVEN` est interdit à ce stade.
