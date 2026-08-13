---
doc_id: GS-SOURCE-REGISTER
title: GitSpace — Source and Provenance Register
authority: PROVENANCE
status: ACTIVE
version: 0.3.2
updated: 2026-08-13
---

# GitSpace — Source and Provenance Register

## Sources internes utilisées

| ID | Source | Rôle | Statut appliqué |
|---|---|---|---|
| `SRC-GS-001` | `00_GITSPACE_START_HERE.md` v0.2.1 | routeur | conservé et étendu |
| `SRC-GS-002` | `01_GITSPACE_CANON_SYSTEM.md` v0.2.1 | canon compact | étendu vers Master Canon |
| `SRC-GS-003` | `02_GITSPACE_NOW_DECISIONS_ROADMAP.md` v0.2.2 | état après correction propriétaire | autoritaire avant observation GitHub fraîche |
| `SRC-GS-004` | `03_GITSPACE_RESEARCH_RISKS.md` v0.2.1 | Atlas compact | actualisé |
| `SRC-GS-005` | `04_GITSPACE_AGENT_PROTOCOL_SESSIONS.md` v0.2.2 | protocole corrigé | autoritaire |
| `SRC-GS-006` | `GS-P00-SPEC-001` v0.1.0 | design Phase 00 | révisé v0.2.1 |
| `SRC-GS-007` | `GS-P00-PLAN-001` v0.1.0 | plan executor-neutral initial | base de v0.3.0 |
| `SRC-GS-008` | `GS-P00-PLAN-001` v0.2.0 | overlay Claude Code | source historique, sections fournisseur invalidées |
| `SRC-GS-009` | `P00-BOOTSTRAP-PLAN-001` v0.1 | plan du corpus | révisé pour dépôt non vide et protocole deux commits |
| `SRC-GS-010` | session de transport `GS-SESSION-20260813-02` | preuve négative | huit blobs orphelins, deux divergences, zéro changement atteignable |
| `SRC-GS-011` | `P00-BOOTSTRAP-TRANSPORT-001` | gate de publication | transport byte-preserving et régénération du vrai commit B |

## Evidence externe fraîche

| ID | Source | Type | Observation | Date de vérification |
|---|---|---|---|---|
| `EXT-GH-001` | GitHub API — `leon36000/GitSpace` | `FACT_OFFICIAL` | visibilité publique, `main@f69b22d...`, README staging | 2026-08-13 |
| `EXT-GH-002` | GitHub API — branches | `FACT_OFFICIAL` | `main` et `hermesclaw-ci` | 2026-08-13 |
| `EXT-RUST-001` | Rust Blog 1.97.1 | `FACT_OFFICIAL` | point release corrigeant une miscompilation | 2026-08-13 |
| `EXT-PY-001` | Python.org 3.12.13 | `FACT_OFFICIAL` | security-only, source-only | 2026-08-13 |
| `EXT-INSPECT-001` | Inspect Evals README | `FACT_OFFICIAL` | recommande Python 3.11 ou 3.12 | 2026-08-13 |
| `EXT-HARBOR-001` | Harbor `pyproject.toml` | `FACT_OFFICIAL` | `requires-python >=3.12` | 2026-08-13 |
| `EXT-GH-003` | GitHub object API — probe de blobs | `EVIDENCE` | huit blobs non référencés; aucun tree/commit/ref/PR | 2026-08-13 |
| `EXT-LOCAL-001` | environnement d’exécution local | `EVIDENCE` | `gh` absent et transport Git réseau indisponible | 2026-08-13 |

## Règles de provenance

- Une URL n’est pas une preuve de fraîcheur; conserver `checked_at`.
- Une branche mouvante doit être verrouillée avant expérience.
- Une sortie de connecteur est `QUARANTINED` jusqu’à confrontation au canon.
- Un artifact local n’est pas canonique avant commit accepté.
- Une citation ne confère aucune autorité de contrôle.

- Un hash de blob créé par un outil doit être comparé au `git hash-object` local avant toute référence.
- Un objet Git non référencé n’est ni une publication ni un état canonique.
