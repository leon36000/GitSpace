task_id: P00-TASK-012
evidence_type: EXACT_HEAD_ROOTLESS_RUNTIME_QUALIFICATION
status: PARTIALLY_VERIFIED_RUNTIME_POSITIVE_PATH
implementation_commit: 51064f8397b5480b6f81bf0924a18ed2b6f9cc94
observed_at: 2026-08-22
---

# P00-TASK-012 — qualification rootless au head exact

Cette preuve remplace les traces runtime historiques invalidées par le
changement du verifier. Elle couvre le head exact
`51064f8397b5480b6f81bf0924a18ed2b6f9cc94`, le fixture courant et deux images
reconstruites sur le worker dédié. Elle ne déclare pas `PROVEN`: l’acceptation
propriétaire des vulnérabilités, la revue indépendante sécurité/conformité,
le merge signé et le replay post-merge restent des gates externes.

## Pins et provenance

- Worker : Docker rootless dédié `linux/amd64`, Docker `29.6.1`, `overlayfs`,
  sécurité `rootless,cgroupns`; DockerRootDir sous
  `/run/.ro3495812743/user/1000/gitspace-p00-worker/data`.
- Environnement :
  `gitspace-p00/regex-log@sha256:2cc553dba23e6c42d58b264ac2409a9bd76ad509c0117db61c4ec0312795ec85`.
  Manifest OCI linux/amd64 :
  `sha256:afc78c3d4e2292cdde4853798b7a79ddcdba16d16710c42c0e897588604f18e3`.
  Provenance SLSA/OCI : `sha256:abee476ed589269b035bcbb97ce20c22ecdf4b8c14c7ae4f7749e64110a0f444`.
  BuildKit a enregistré le VCS revision exact et `force-network-mode=none`.
- Base environnement :
  `python:3.13.15-slim-bookworm@sha256:0f16c5d35fe6464ee471792ab3bb9116f911b65b3fbf10120c98d2bdc6332f48`.
- Sidecar :
  `gitspace-p00/harbor-egress-latest@sha256:2a1c1b598be3512db201bb03f50ac66d8a794c3fd834752aae99138f3fda37a0`.
  Manifest OCI linux/amd64 :
  `sha256:bebac85d320aa947c5d917ad49846af3a59a091c0acd0881e551e9d9c39ba711`.
  Provenance SLSA/OCI : `sha256:0ba30ce17707ec1df5a091eaa223dbdbe86b60ac858ec6229f644157fd92f21f`.
  Sa base GOST est liée à
  `gogost/gost@sha256:6ed277d799bb6adae168155cacf986145a0ab490444a6cf1bad1825a016a3241`.
- Fixture : source manifest `sha256:afd4eeceb4d93fa384e4767d921e956b77a41802793a708204e677f951e1899e`;
  verifier `sha256:7b36ee16f297fb0187a5eed5829bc1855ed3bfc03414e17f5dc204342cdbf7af`;
  test amont `sha256:345c3bd09ab6f6fe8c8361a58c0a47bf0a13b3fcb38a5ac7824e44ff855e8f72`.

Les fichiers SPDX, rapports scanner et attestations brutes sont versionnés
dans `P00-TASK-012-supply-chain-2026-08-22/`. Le même répertoire conserve le
résultat adaptateur, le manifeste CAS, les manifests de ressources
before/after, les configurations Harbor/Trial, les résultats bruts et les
artefacts reward/result du verifier.

## Oracle Harbor réel

- Harbor `0.21.0`, commit `64afbbcb62165950301e1a6407c729aa26d844ff`, wheel
  `sha256:c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21`.
- Job `8dc78258-261f-47f0-aac7-a513ad3e3831`; une trial
  `4c04c48a-0e35-496e-9d10-8d7c45b29337`, nom
  `terminal-bench-2.1-regex-log__U4n2ZqE`.
- Trial checksum :
  `7d144b17234c7386e0f10d311fbb2139ee69f1f06be76b11bf53753afca74f22`;
  reward `1`; retries `0`; code Harbor `0`.
- Record CAS :
  `sha256:23a4922599fb49aaffd0315713a949cb99eb380557ea5ecae4fce62fc06c9c05`.
  Le replay CAS a réussi et `artifact_integrity`, `qualification_pinned`,
  `network_closed`, `infra_clear`, `cleanup_complete` et les cardinalités
  fermées sont vrais.
- Les artefacts `reward.json` et `gitspace-result.json` ont été collectés en
  `0644`, lisibles par le collecteur host rootless.

Le manifeste CAS brut versionné est
`runtime-cas-manifest.json`; il lie notamment le record Harbor
`sha256:23a4922599fb49aaffd0315713a949cb99eb380557ea5ecae4fce62fc06c9c05`,
les manifests de ressources before/after et les hashes du verifier. Le
résultat adaptateur brut est `runtime-adapter-result.json`.

## Isolation et cleanup observés

L’observateur indépendant a relevé 20 entrées avant (18 étrangères, plus le
process group et le temp root GitSpace) et 18 entrées étrangères après. Il n’y
avait aucun conteneur avant/après; les trois réseaux par défaut sont restés
identiques; les 15 images étrangères sont restées identiques; aucune ressource
GitSpace n’est restée. L’état étranger est comparé sur toutes les lignes de
tags par digest, sans écraser les tags multiples d’une même image.

## Gates encore ouvertes

Le runtime positif est maintenant frais et exact-head. Restent ouverts :

- dispositions owner-approved pour l’union Trivy/Grype;
- revue indépendante sécurité, conformité et non-egress;
- merge signé autorisé par le propriétaire;
- replay frais après merge sur `main`.

Le statut doit donc rester `PARTIALLY_VERIFIED_RUNTIME_POSITIVE_PATH`.
