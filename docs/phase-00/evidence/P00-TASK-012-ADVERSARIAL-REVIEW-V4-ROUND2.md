---
evidence_id: P00-TASK-012-ADVERSARIAL-REVIEW-V4-ROUND2
status: REVIEW_FINDINGS_REQUIRING_PACKET_AMENDMENT
reviewed_at: 2026-08-18
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
reviewed_packet_commit: 5fdba221cc5c725b8585ae6c98e3e65d809d2fc9
reviewer: CHATGPT_PROJECT_GITSPACE
---
# P00-TASK-012 — Revue adversariale v4, passe 2

## Verdict

Le paquet v4 corrige les findings de v3 mais trois ambiguïtés résiduelles doivent être fermées avant sa proposition finale. Aucun code produit n'est autorisé par cette revue.

```yaml
packet_v4: PARTIALLY_VERIFIED_PROPOSAL
review_result: CHANGES_REQUIRED
canonical_state_changed: false
production_code_authorized: false
```

## R2-F1 — Absence normale d'`agent/exit-code.txt`

Le paquet admet correctement qu'un `OracleAgent` réussi peut ne produire aucun `agent/exit-code.txt`, mais liste ensuite `oracle_exit_code` comme artefact obligatoire avec URI CAS. On ne peut pas adresser par contenu un fichier qui n'existe pas.

### Correction

Produire toujours un artefact canonique `oracle_exit_status` :

```json
{"present":false,"value":null}
```

ou :

```json
{"present":true,"value":0}
```

Le fichier brut `oracle_exit_code` devient conditionnel et n'est CAS-bound que s'il existe. Le replay dérive son champ `oracle_exit_code: int | None` depuis `oracle_exit_status` et vérifie, lorsqu'un raw existe, que les deux concordent.

Toute valeur non-zéro, malformée ou contradiction => `INFRA` + `task_invalid_candidate=true` pour `qualification_oracle`.

## R2-F2 — Politique verifier explicite

Harbor 0.21.0 fait hériter le verifier partagé de la baseline `[environment].network_mode`, donc `no-network` est déjà effectif. Toutefois le modèle `VerifierConfig` accepte aussi un override de phase explicite.

### Correction

La nouvelle fixture doit fixer les deux :

```toml
[environment]
network_mode = "no-network"

[verifier]
environment_mode = "shared"
network_mode = "no-network"
```

Après parsing, GitSpace vérifie baseline agent, phase agent et phase verifier : toutes doivent être `no-network`, sans allowlist.

## R2-F3 — Image préconstruite et sidecar egress Harbor

Harbor Docker choisit une image préconstruite lorsque `[environment].docker_image` est défini et que `force_build=false`; cela permet d'éviter le build de l'image de tâche pendant le run.

Mais une politique `no-network` active le sidecar egress Harbor. Harbor appelle `ensure_docker_image_built` pour ce sidecar au démarrage. Le helper calcule un nom content-addressed et ne rebuild pas si l'image exacte existe déjà localement. Le Dockerfile du sidecar Harbor 0.21.0 part de :

```text
gogost/gost:3.2.7-nightly.20260602@sha256:afc0137758ab4ce399d47a299f9abbacbf522b52a17e59cbb4b4e7a1a66e9196
```

Le compose lui accorde `NET_ADMIN` et `NET_RAW`.

### Correction

La qualification runtime devient en deux phases :

1. **prefetch/qualification autorisée et enregistrée** : charger l'image de tâche exacte par digest; préconstruire le sidecar Harbor content-addressed depuis le commit 0.21.0; enregistrer image ID, contexte/hash, base digest, SBOM et scan; vérifier les capacités `NET_ADMIN/NET_RAW` du worker;
2. **run évalué offline** : bloquer l'egress du daemon Docker hôte, vérifier que l'image de tâche et le sidecar qualifiés sont déjà locaux, puis lancer Harbor. Toute tentative de pull/build qui nécessite le réseau doit échouer et devient `INFRA`.

Le task `task.toml` qualifiant utilise `docker_image` exact par digest et ne doit pas dépendre d'un Dockerfile de build. L'image runtime est choisie seulement après qualification Python 3.13.15 + bash + supply chain.

Le daemon dédié/rootless doit également prouver que le sidecar Harbor peut démarrer avec ses capabilities requises. Un worker rootless qui ne peut pas satisfaire ce contrat est rejeté; un worker rootful n'est admissible que s'il est dédié jetable, sans workloads étrangers et avec egress daemon coupé pendant le run.

## Décision

Après intégration de R2-F1..F3 et auto-revue de cohérence, la v4 peut atteindre `PROPOSED_REVIEW_READY_BLOCKED_WITH_EVIDENCE`. Elle ne devient ni canonique ni exécutable tant que les gates RED/toolchain/runtime ne sont pas fermées.
