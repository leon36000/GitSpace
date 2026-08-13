---
doc_id: GS-SOURCE-REGISTER
title: GitSpace — Source and Provenance Register
authority: PROVENANCE
status: ACTIVE
version: 0.3.3
updated: 2026-08-13
---

# GitSpace — Source and Provenance Register

## Sources internes

| ID | Source | Rôle | Statut appliqué |
|---|---|---|---|
| `SRC-GS-001` | RAGLite 00 v0.2.1 | routeur initial | étendu v0.3 |
| `SRC-GS-002` | RAGLite 01 v0.2.1 | canon compact | étendu vers Master Canon |
| `SRC-GS-003` | RAGLite 02 v0.2.2/v0.2.3 | état corrigé | superseded par état PR |
| `SRC-GS-004` | RAGLite 03 v0.2.1 | Atlas compact | actualisé |
| `SRC-GS-005` | RAGLite 04 v0.2.2/v0.2.3 | protocole corrigé | étendu |
| `SRC-GS-006` | `GS-P00-SPEC-001` v0.1/v0.2 | design Phase 00 | restructuré v0.3.0 |
| `SRC-GS-007` | `GS-P00-PLAN-001` v0.1 | plan executor-neutral initial | remplacé par v0.4.0 |
| `SRC-GS-008` | `GS-P00-PLAN-001` v0.2 | overlay Claude Code | historique négatif |
| `SRC-GS-009` | `P00-BOOTSTRAP-PLAN-001` | plan de corpus | exécuté partiellement |
| `SRC-GS-010` | sessions de transport | preuve négative | blobs orphelins non référencés |
| `SRC-GS-011` | `P00-BOOTSTRAP-TRANSPORT-001` | gate de publication | qualifié pour PR #1 |
| `SRC-GS-012` | commits A/B et trees Git | preuve de publication | vérifiée |

## Evidence externe fraîche

| ID | Source | Type | Observation | Vérifié le |
|---|---|---|---|---|
| `EXT-GH-001` | GitHub API — dépôt | `FACT_OFFICIAL` | dépôt public, `main@f69b22d...` | 2026-08-13 |
| `EXT-GH-002` | GitHub API — branches | `FACT_OFFICIAL` | `main`, `hermesclaw-ci`, branche bootstrap | 2026-08-13 |
| `EXT-GH-003` | GitHub object API — A | `EVIDENCE` | parent `f69b22d...`, tree `da903750...` | 2026-08-13 |
| `EXT-GH-004` | GitHub object API — B | `EVIDENCE` | parent A, tree `7b6bb98...` | 2026-08-13 |
| `EXT-GH-005` | GitHub compare A→B | `EVIDENCE` | un commit, exactement six fichiers | 2026-08-13 |
| `EXT-GH-006` | GitHub tree B | `EVIDENCE` | cinq projections utilisent les blobs sources | 2026-08-13 |
| `EXT-GH-007` | GitHub PR #1 | `FACT_OFFICIAL` | ouverte, brouillon, mergeable, base/head exacts | 2026-08-13 |
| `EXT-GH-008` | GitHub object probes | `EVIDENCE_NEGATIVE` | blobs orphelins divergents, aucun ref | 2026-08-13 |
| `EXT-RUST-001` | Rust Blog 1.97.1 | `FACT_OFFICIAL` | point release corrigeant une miscompilation | 2026-08-13 |
| `EXT-PY-001` | Python.org 3.12.13 | `FACT_OFFICIAL` | security-only, source-only | 2026-08-13 |
| `EXT-INSPECT-001` | Inspect Evals README | `FACT_OFFICIAL` | recommande Python 3.11/3.12 | 2026-08-13 |
| `EXT-HARBOR-001` | Harbor `pyproject.toml` | `FACT_OFFICIAL` | `requires-python >=3.12` | 2026-08-13 |

## Graphe de provenance du bootstrap

```text
main f69b22d...
  └─ A 488fd399... / tree da903750...
       ├─ 19 documents canoniques
       └─ B 08a38c43... / tree 7b6bb98...
            ├─ manifeste source_commit=A
            └─ 5 projections partageant les blobs sources
                 └─ PR #1 brouillon
```

La clôture d’état C puis sa projection D prolongent ce graphe sans modifier A/B.

## Règles de provenance

- Une URL n’est pas une preuve de fraîcheur; conserver `checked_at`.
- Une branche mouvante est verrouillée avant expérience.
- Une sortie de connecteur est `QUARANTINED` jusqu’à confrontation au canon.
- Un artefact local n’est pas canonique avant commit accepté.
- Une citation ne confère aucune autorité de contrôle.
- Un hash de blob doit être comparé à la source ou réutiliser directement le blob source.
- Un objet Git non référencé n’est ni une publication ni un état canonique.
- Une PR ouverte n’est pas une décision propriétaire de merge.
- Les commits GitHub de cette session sont non signés; ce fait reste visible.
