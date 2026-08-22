task_id: P00-TASK-012
evidence_type: SUPPLY_CHAIN_SBOM_PROVENANCE_SCANNER
status: OPEN_PENDING_INDEPENDENT_REVIEW_AND_OWNER_ACCEPTANCE
observed_at: 2026-08-22
---

# P00-TASK-012 — supply-chain et dispositions

Les rapports ci-dessous sont frais, liés aux digests OCI exacts et conservés
avec leurs entrées SPDX/provenance. Les findings ne sont pas masqués par des
filtres `ignore`, et aucun owner acceptance n’est inventé.

## Outils et bases

| Outil | Version | SHA-256 binaire |
|---|---:|---|
| Syft | 1.50.0 | `22f2b95baf524d45ad16b0ad5cdeb200c4b8a816493768cec50e4682b1f24b0e` |
| Trivy | 0.73.0 | `5b3ebab0f98d95196c85efc3a9d31a01520c96fa342e4e611f56db64c516df1d` |
| Grype | 0.116.1 | `a8fff88f37a08af6a536e162f37f9902ec94af03df9928ee6295dffe7044dc43` |
| ORAS | 1.3.3 | `a9c7694677a72251c89c176331d41b2198d8e85cbaece038bcbc8da0679e1139` |
| cosign | 2.4.1 | `8b24b946dd5809c6bd93de08033bcf6bc0ed7d336b7785787c080f574b89249b` |
| uv | 0.12.0 | `b6e3cb5b4858d920c63e1d88e31a7a4d8f567073ee4e5e4a1889f93984dc28ea` |

Trivy DB : metadata `e48fd03a0081ca508785a05517d0d2df87abdc6c11af0d6043871aefae4188e6`,
`trivy.db` `ba3b0c5c8093d4b5df1c351646b9739dd788323dba951c94452d7fbf27cc0e79`,
mise à jour `2026-08-22T07:04:53Z`, prochaine mise à jour
`2026-08-23T07:04:53Z`. Grype DB : schéma `v6.1.9`, build
`2026-08-22T06:14:16Z`, `vulnerability.db`
`bc53242e0261ea0fbc4f6c89b25c3828f7bebea5dfcb560b32eb6aba5f867eac`,
`import.json` `e94212c1d1251491b6dfff69ae9399527cda23c9cbc46c72b817c65049228284`;
état `valid`.

Le hook global gitleaks a signalé neuf occurrences `generic-api-key` dans les
rapports bruts. La revue ligne par ligne les attribue aux métadonnées publiques
`GPG_KEY` de l’image Python et non à une credential ou à une valeur d’accès.
Les empreintes exactes ont été allowlistées uniquement dans une configuration
locale temporaire pour permettre l’archivage de ces rapports ; aucune
allowlist n’est ajoutée au dépôt, et le hook reste bloquant pour toute nouvelle
valeur réellement secrète.

## Artefacts liés

| Artefact | Image/dépendance | SPDX SHA-256 | Trivy SHA-256 | Grype SHA-256 | Provenance SHA-256 |
|---|---|---|---|---|---|
| environnement | `gitspace-p00/regex-log@sha256:2cc553dba23e6c42d58b264ac2409a9bd76ad509c0117db61c4ec0312795ec85` | `ebd3a1a51ac174a23788952be0d6155b533477a3085815577439bfe0a6248837` | `f5021a854ae3547e5a00360bf8719b4a6767236a74944493ff16ad1d9f28d34d` | `445f3820d67b6e2d67f67571185454313cb82f7d053d261b574866e7a6e77fbc` | `abee476ed589269b035bcbb97ce20c22ecdf4b8c14c7ae4f7749e64110a0f444` |
| sidecar | `gitspace-p00/harbor-egress-latest@sha256:2a1c1b598be3512db201bb03f50ac66d8a794c3fd834752aae99138f3fda37a0` | `97b91b79fb8214ba698b8e29e5820ba8987d406dca88b88ee20b7f0f9e7d48fe` | `57c574773db522df892857442c7de65cec293fb2abba68ab76589bb0f1750724` | `6bd8c5c5548b167b47d97253e92c964d4759c2f2344b42e189ea8c2e141bb26a` | `0ba30ce17707ec1df5a091eaa223dbdbe86b60ac858ec6229f644157fd92f21f` |
| base | `python@sha256:0f16c5d35fe6464ee471792ab3bb9116f911b65b3fbf10120c98d2bdc6332f48` | `db244211e941df94259a118d9aaf385bce6e70ec413c4f4beb57263512554124` | `e51da0da3fe2b63504484e1d1f908c887c522bbb700ccb356f537d349cc0fbb7` | `d0dc302c5d750af34baea9a14b26ac070008618accaa07c00953510e19cb0ae7` | résolue comme dépendance dans la provenance environnement |

Les trois SBOM sont `SPDX-2.3`. Les attestations de provenance sont de type
`https://slsa.dev/provenance/v1`; la provenance environnement lie le VCS
revision `51064f8397b5480b6f81bf0924a18ed2b6f9cc94` et la base Python exacte.

## Résultats bruts et union des findings

- Environnement : Trivy `5 CRITICAL / 31 HIGH`; Grype `8 Critical / 22 High`.
- Sidecar : Trivy `0 CRITICAL / 0 HIGH`; Grype `0 Critical / 2 High`.
- La base Python reproduit les findings de l’environnement.

L’union CRITICAL de l’environnement contient notamment
`CVE-2023-45853`, `CVE-2025-7458`, `CVE-2026-12087`, `CVE-2026-13221`,
`CVE-2026-42496`, `CVE-2026-5450`, `CVE-2026-57433` et `CVE-2026-8376`.
L’union HIGH comprend notamment les findings Perl, SQLite, ncurses, gzip,
util-linux, acl, libc, OpenSSL/QUIC, ainsi que les composants Python vendus
par pip (`msgpack` et `setuptools`). Le sidecar conserve deux matches Grype
pour `CVE-2026-14456` sur `libcrypto3` et `libssl3`.

## Dispositions proposées, non encore acceptées

Les éléments suivants sont des hypothèses de reachability à vérifier par un
reviewer indépendant; ils ne ferment donc aucune gate :

- le verifier verrouillé n’importe ni Perl, ni SQLite, ni ncurses, ni gzip,
  ni util-linux, et le run Harbor impose `no-network`;
- le sidecar GOST est statiquement lié (`/bin/gost` n’est pas un programme
  dynamique), sa configuration est un proxy TCP `red` sans listener QUIC, et
  l’exécution qualifiée n’autorise aucun egress;
- les états `wont-fix`, `not-fixed` et `fix_deferred` des bases scanner sont
  conservés tels quels et ne sont pas assimilés à une correction.

Le [détail NVD de CVE-2026-14456](https://nvd.nist.gov/vuln/detail/CVE-2026-14456)
décrit un déni de service du serveur QUIC OpenSSL; cette description soutient
la question de reachability mais ne constitue pas une acceptation propriétaire.
Les CRITICAL restent donc non résolus pour le gate Task 12, et chaque HIGH
requiert une correction ou une acceptation propriétaire datée avant toute
promotion.
