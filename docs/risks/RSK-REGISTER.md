---
doc_id: GS-RSK-REGISTER
title: GitSpace — Risk Register
authority: RISK_REGISTER
status: ACTIVE
version: 0.3.1
updated: 2026-08-13
---

# GitSpace — Risk Register

## Statuts

- `OPEN` : risque actif.
- `CONTROLLED` : contrôles présents, preuve encore requise.
- `BLOCKING` : empêche une transition.
- `ACCEPTED_OWNER` : risque explicitement accepté par le propriétaire.
- `CLOSED_WITH_EVIDENCE` : preuve reproductible de fermeture.
- `STALE` : formulation remplacée.

## Risques produit

| ID | Risque | Signal | Contrôle | Preuve de fermeture | Statut |
|---|---|---|---|---|---|
| `RSK-001` | Faux `DONE` | agent annonce succès avec obligations ouvertes | obligations, verdicts non compensables, vérification indépendante | campagnes avec défauts injectés sans faux succès | `OPEN` |
| `RSK-002` | Dérive d’intention | diff hors objectif ou non-scope | intent checksum, Drift Radar, scope machine | taux de dérive et blocage correct | `OPEN` |
| `RSK-003` | Mémoire empoisonnée | choix influencé par donnée non vérifiée | quarantaine, provenance, ACL, action gates | poison ASR sous seuil préenregistré | `OPEN` |
| `RSK-004` | Prompt injection | données externes modifient contrôle ou outils | séparation contrôle/données, capabilities | campagne AgentDojo/CaMeL adaptée | `OPEN` |
| `RSK-005` | Erreur corrélée multi-agents | consensus incorrect | diversité de méthodes, oracle déterministe | comparaison multi-agents contrôlée | `OPEN` |
| `RSK-006` | Permissions excessives | écriture ou réseau hors mission | capabilities éphémères, deny-by-default | tests d’élévation et d’exfiltration | `OPEN` |
| `RSK-007` | Preuve périmée | preuve utilisée après changement affectant | graphe d’impact et invalidation | test de modification dépendante | `OPEN` |
| `RSK-008` | Non-reproductibilité | replay divergent | environnements verrouillés, CAS, manifests | replay indépendant | `OPEN` |
| `RSK-009` | Propriétaire forcé de vérifier le code | décision technique ou audit imposé | Outcome Studio, preuve comportementale | étude propriétaire | `OPEN` |
| `RSK-010` | Auto-évolution dangereuse | skill promu depuis une seule trajectoire | laboratoire isolé, validation hors échantillon | campagne de non-régression | `OPEN` |
| `RSK-011` | Secret exposé au modèle | valeur secrète dans contexte ou trace | handles, broker, redaction | scan et test d’exfiltration | `OPEN` |
| `RSK-012` | Simulation confondue avec preuve | world model utilisé comme oracle final | confirmation environnement réel ou formelle | audit de provenance | `OPEN` |
| `RSK-013` | Composants non composables | garanties locales incompatibles | contrats, SBOM, tests de composition | qualification multi-composants | `OPEN` |
| `RSK-014` | Versions documentaires concurrentes | plusieurs `02` actifs | remplacement atomique, manifestes | audit sources projet | `CONTROLLED` |
| `RSK-015` | Auto-référence du manifeste Git | manifeste prétend référencer son propre commit | publication en deux commits | régénération depuis commit A = projection B | `CONTROLLED` |
| `RSK-016` | Collision d’identité du dépôt | README GitSpace décrit HermesClaw staging | quarantaine, branche dédiée, PR, préservation | PR revue et historique intact | `BLOCKING` |
| `RSK-017` | Dérive dépôt ↔ RAGLite | sources mobiles ne reflètent plus le canon | commit source, digests, régénération | comparaison bit-à-bit | `OPEN` |
| `RSK-018` | Plan couplé à un exécuteur | commandes ou métadonnées fournisseur dans plan maître | plan v0.3 executor-neutral, packetisation | scan de termes interdits | `CONTROLLED` |
| `RSK-019` | Pin toolchain prématuré | version acceptée sans compatibilité | qualification fraîche et lock | matrice Rust/Python/adaptateurs | `OPEN` |
| `RSK-020` | Canon publié sans autorité | branche/commit pris pour décision acceptée | PR, revue propriétaire, ADR | approbation explicite | `OPEN` |
| `RSK-021` | Corruption de transport canonique | blob distant différent du fichier local | transport byte-preserving, `git hash-object`, comparaison tree | tous les blobs A/B identiques | `BLOCKING` |
| `RSK-022` | Patch B lié au mauvais commit A | manifeste référence un SHA synthétique | régénérer B après le vrai A; patch B local `PROOF_ONLY` | `manifest.source_commit = vrai A` | `CONTROLLED` |

## Risques Phase 00

| ID | Risque | Contrôle | Preuve requise | Statut |
|---|---|---|---|---|
| `RSK-P00-001` | Benchmark auto-favorable | imports externes, tâches privées, reviewers indépendants | résultats sur familles externes | `OPEN` |
| `RSK-P00-002` | Contamination des modèles | tâches rotatives, provenance, dates, variantes | audit de contamination | `OPEN` |
| `RSK-P00-003` | Vérificateur hackable | isolation, mutation, hacker/fixer/solver | attaques documentées | `OPEN` |
| `RSK-P00-004` | Coût expérimental excessif | smoke → pilot → qualification | coût par obligation prouvée | `OPEN` |
| `RSK-P00-005` | Données sensibles dans traces | classification, redaction, ACL, rétention | tests de fuite | `OPEN` |
| `RSK-P00-006` | Préprint traité comme fait | plafond `PILOT`, ReproductionRecord | audit Atlas | `CONTROLLED` |
| `RSK-P00-007` | Harness confondu avec modèle | factorisation des manifests | expérience appariée | `OPEN` |
| `RSK-P00-008` | Résultats incomparables | IR souverain et budgets déclarés | qualification adaptateurs | `OPEN` |
| `RSK-P00-009` | Tâche invalide comptée comme échec agent | état `TASK_INVALID`, QA indépendante | taux et causes des tâches invalides | `OPEN` |
| `RSK-P00-010` | LLM judge corrélé | oracle déterministe prioritaire | comparaison juges/oracles | `OPEN` |
| `RSK-P00-011` | Tests cachés divulgués | Oracle Vault, accès séparé | audit d’accès | `OPEN` |
| `RSK-P00-012` | Score moyen masque une violation | dimensions non compensables | test de verdict contradictoire | `OPEN` |
| `RSK-P00-013` | Faible puissance statistique | répétitions, analyses appariées, CIs | rapport préenregistré | `OPEN` |
| `RSK-P00-014` | Toolchain externe mouvante | version, commit et digest | replay ultérieur | `OPEN` |

## Risque bloquant courant

### RSK-016 — Collision d’identité du dépôt

**EVIDENCE**

- `main` contient le commit `f69b22d2bd09aa5eae96693acf501b2464c3be25`.
- Le README observé décrit un dépôt de staging CI privé et une branche HermesClaw.
- Une branche `hermesclaw-ci` existe séparément.

**Impact**

Publier directement le corpus sur `main` sans revue pourrait écraser une intention externe non documentée dans le canon GitSpace.

**Résolution réversible proposée**

1. ne supprimer aucune branche;
2. créer `bootstrap/canonical-corpus-v0.3` depuis le SHA observé;
3. publier le canon en commit A;
4. publier le RAGLite en commit B;
5. ouvrir une pull request;
6. conserver le README précédent dans l’historique et dans le rapport de conflit;
7. demander l’acceptation propriétaire au moment du merge.

**Statut : `BLOCKING_FOR_DIRECT_MAIN_WRITE`, non bloquant pour la préparation locale et la branche proposée.**

## Politique de fermeture

Un risque n’est jamais fermé par une déclaration. `CLOSED_WITH_EVIDENCE` exige :

- un test ou une observation;
- la provenance;
- une date;
- les conditions de validité;
- une méthode de réouverture.


### RSK-021 — Corruption du transport canonique

**EVIDENCE_NEGATIVE**

- Huit blobs non référencés ont été créés pendant le probe.
- Six correspondaient exactement aux hashes Git locaux.
- Deux ne correspondaient pas aux fichiers visés.
- Aucun ref ne les rend accessibles depuis le dépôt.

**Impact**

Un corpus apparemment publié pourrait contenir des octets différents de ceux qui ont passé les validations locales.

**Contrôle obligatoire**

1. lire les fichiers directement depuis un checkout local;
2. créer les commits avec Git local;
3. vérifier `git hash-object` avant push;
4. pousser sans force sur une branche dédiée;
5. relire l’arbre distant;
6. comparer tous les blobs;
7. arrêter à la première divergence.

**Statut : `BLOCKING_REMOTE_PUBLICATION`.**
