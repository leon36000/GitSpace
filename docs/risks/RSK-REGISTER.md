---
doc_id: GS-RSK-REGISTER
title: GitSpace — Risk Register
authority: RISK_REGISTER
status: ACTIVE
version: 0.3.2
updated: 2026-08-13
---

# GitSpace — Risk Register

## Statuts

`OPEN`, `CONTROLLED`, `BLOCKING`, `ACCEPTED_OWNER`, `CLOSED_WITH_EVIDENCE`, `STALE`.

## Risques produit

| ID | Risque | Contrôle | Preuve de fermeture | Statut |
|---|---|---|---|---|
| `RSK-001` | Faux `DONE` | obligations, verdicts non compensables, vérification indépendante | campagne avec défauts injectés | `OPEN` |
| `RSK-002` | Dérive d’intention | intent checksum, scope machine, Drift Radar | taux de dérive/blocage | `OPEN` |
| `RSK-003` | Mémoire empoisonnée | quarantaine, provenance, ACL | poison ASR sous seuil | `OPEN` |
| `RSK-004` | Prompt injection | séparation contrôle/données, capabilities | campagne adaptée | `OPEN` |
| `RSK-005` | Erreur corrélée multi-agents | diversité de méthodes, oracle déterministe | comparaison contrôlée | `OPEN` |
| `RSK-006` | Permissions excessives | deny-by-default, capabilities éphémères | tests d’élévation | `OPEN` |
| `RSK-007` | Preuve périmée | graphe d’impact et invalidation | modification dépendante | `OPEN` |
| `RSK-008` | Non-reproductibilité | locks, CAS, manifests | replay indépendant | `OPEN` |
| `RSK-009` | Propriétaire forcé de vérifier le code | Outcome Studio, preuve comportementale | étude propriétaire | `OPEN` |
| `RSK-010` | Auto-évolution dangereuse | laboratoire isolé, validation hors échantillon | non-régression | `OPEN` |
| `RSK-011` | Secret exposé au modèle | handles, broker, redaction | test d’exfiltration | `OPEN` |
| `RSK-012` | Simulation confondue avec preuve | confirmation réelle/formelle | audit de provenance | `OPEN` |
| `RSK-013` | Garanties non composables | contrats, SBOM, tests de composition | qualification | `OPEN` |
| `RSK-014` | Versions documentaires concurrentes | remplacement atomique, manifeste | audit Projet ChatGPT | `CONTROLLED` |
| `RSK-015` | Auto-référence Git | paire canon/projection | B référence A; D référence C | `CLOSED_WITH_EVIDENCE` |
| `RSK-016` | Collision d’identité du dépôt | branche dédiée, PR, historique préservé | décision propriétaire | `BLOCKING_OWNER_DECISION` |
| `RSK-017` | Dérive dépôt ↔ RAGLite | même blob source/projection | comparaison tree | `CONTROLLED` |
| `RSK-018` | Plan couplé à un exécuteur | plan v0.4 executor-neutral | scan et revue | `CONTROLLED` |
| `RSK-019` | Pin toolchain prématuré | qualification fraîche | matrice Task 1 | `OPEN` |
| `RSK-020` | Canon publié sans autorité | PR brouillon + merge propriétaire | approbation explicite | `OPEN` |
| `RSK-021` | Corruption de transport | UTF-8 direct, trees/blobs, comparaison | A/B et projections identiques | `CONTROLLED_WITH_EVIDENCE` |
| `RSK-022` | Projection liée au mauvais parent | régénération depuis vrai parent | B `source_commit=A`, D `source_commit=C` | `CLOSED_WITH_EVIDENCE` |
| `RSK-023` | Merge prématuré | PR brouillon, reviews requises | propriétaire accepte | `OPEN` |

## Risques Phase 00

| ID | Risque | Contrôle | Statut |
|---|---|---|---|
| `RSK-P00-001` | Benchmark auto-favorable | imports externes, tâches privées, reviewers indépendants | `OPEN` |
| `RSK-P00-002` | Contamination | tâches rotatives, provenance, variantes | `OPEN` |
| `RSK-P00-003` | Vérificateur hackable | isolation, mutation, hacker/fixer/solver | `OPEN` |
| `RSK-P00-004` | Coût excessif | smoke → pilot → qualification | `OPEN` |
| `RSK-P00-005` | Données sensibles dans traces | classification, redaction, ACL | `OPEN` |
| `RSK-P00-006` | Préprint traité comme fait | plafond `PILOT`, reproduction | `CONTROLLED` |
| `RSK-P00-007` | Harness confondu avec modèle | manifests factorisés | `OPEN` |
| `RSK-P00-008` | Résultats incomparables | IR souverain et budgets | `OPEN` |
| `RSK-P00-009` | Tâche invalide comptée comme échec | `TASK_INVALID` | `OPEN` |
| `RSK-P00-010` | LLM judge corrélé | oracle déterministe prioritaire | `OPEN` |
| `RSK-P00-011` | Tests cachés divulgués | Oracle Vault | `OPEN` |
| `RSK-P00-012` | Score masque une violation | dimensions non compensables | `OPEN` |
| `RSK-P00-013` | Faible puissance statistique | répétitions, analyses appariées | `OPEN` |
| `RSK-P00-014` | Toolchain mouvante | version/commit/digest | `OPEN` |

## RSK-016 — Collision d’identité du dépôt

**EVIDENCE**

- `main@f69b22d...` contient le README de staging HermesClaw;
- `hermesclaw-ci` reste séparée;
- PR #1 propose GitSpace sans réécriture de l’historique.

**Contrôle exécuté**

- branche dédiée;
- A parent direct de `main`;
- aucun effet sur `main` ou `hermesclaw-ci`;
- PR brouillon et mergeable.

**Reste à fermer**

Le propriétaire accepte ou refuse que `main` devienne le canon GitSpace.

## RSK-021 — Corruption du transport

**EVIDENCE_NEGATIVE**

Des blobs orphelins divergents ont démontré que la transcription manuelle d’un payload encodé n’est pas fiable.

**EVIDENCE_POSITIVE**

- contenus UTF-8 directs vérifiés;
- tree A inventorié;
- commit A parent vérifié;
- tree B construit par réutilisation des blobs sources;
- diff A→B exactement six fichiers;
- cinq couples source/projection avec SHA Git identique.

La classe de risque reste active pour les publications futures, mais le bootstrap courant est contrôlé.

## Politique de fermeture

`CLOSED_WITH_EVIDENCE` exige test ou observation, provenance, date, conditions de validité et méthode de réouverture. Une déclaration seule ne ferme jamais un risque.
