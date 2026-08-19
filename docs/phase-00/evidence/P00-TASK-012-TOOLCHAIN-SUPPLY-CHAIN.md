---
evidence_id: P00-TASK-012-TOOLCHAIN-SUPPLY-CHAIN
status: EVIDENCE_BYTES_VERIFIED_NOT_EXECUTED
observed_at_utc: 2026-08-18T02:15:00Z
base_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
scope: exact_python_uv_supply_chain
---
# P00-TASK-012 — Qualification supply-chain du toolchain exact

## Résultat

```yaml
python_3_12_13_source: FACT_OFFICIAL
python_managed_binary_candidate: PILOT_BYTES_VERIFIED_NOT_EXECUTED
uv_0_12_0_binary_candidate: PILOT_BYTES_VERIFIED_NOT_EXECUTED
archive_metadata_safety: VERIFIED_FOR_DOWNLOADED_BYTES
artifact_attestations: NOT_VERIFIED_WITH_EVIDENCE
exact_toolchain_runtime: BLOCKED_NOT_EXECUTED
```

Cette preuve ferme la provenance, les checksums candidats et un re-hash frais des deux archives téléchargées. Elle ne prouve ni installation, ni compatibilité runtime, ni RED Task 12. Aucun binaire téléchargé n'a été extrait ou exécuté pendant cette qualification; les attestations GitHub restent non vérifiées faute d'authentification CLI préexistante.

## Python amont

Python `3.12.13` est la version exacte verrouillée par `toolchains.lock.json`. La release CPython a été publiée le 3 mars 2026 dans la phase security-only de Python 3.12. Python.org ne publie plus d'installateurs binaires pour cette série à ce stade : la release officielle est source-only.

```yaml
cpython:
  version: 3.12.13
  release_date: 2026-03-03
  distribution_policy: source_only
  source_xz:
    filename: Python-3.12.13.tar.xz
    sha256: c08bc65a81971c1dd5783182826503369466c7e67374d1646519adf05207b684
  source_gzip:
    filename: Python-3.12.13.tgz
    sha256: 0816c4761c97ecdb3f50a3924de0a93fd78cb63ee8e6c04201ddfaedca500b0b
  upstream_integrity_metadata:
    sigstore: available
    spdx_sbom: available
```

Conséquence : un exécutable préconstruit utilisé pour le RED n'est pas un binaire CPython publié par python.org et doit être qualifié comme distribution tierce distincte.

## Python managed candidate — Astral python-build-standalone

Le script de métadonnées officiel de `uv` consomme l'index Astral `python-build-standalone.ndjson` et préfère `install_only_stripped`, puis `install_only`. L'index officiel Astral a été interrogé en lecture seule et filtré sur la version, la plateforme et la variante exactes.

```yaml
provider: astral-sh/python-build-standalone
record:
  version: 3.12.13+20260807
  date: 2026-08-07T13:09:20.650324Z
  platform: x86_64-unknown-linux-gnu
preferred_artifact:
  variant: install_only_stripped
  archive_format: tar.gz
  url: https://github.com/astral-sh/python-build-standalone/releases/download/20260807/cpython-3.12.13%2B20260807-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz
  sha256: 506191be3ee7bd190a8834dcdc1b3bc70aab50608deccc711935aa007239cabd
fallback_artifact:
  variant: install_only
  archive_format: tar.gz
  url: https://github.com/astral-sh/python-build-standalone/releases/download/20260807/cpython-3.12.13%2B20260807-x86_64-unknown-linux-gnu-install_only.tar.gz
  sha256: 5bd6f36fd7ef02b909234c94dca9994ef0da06ace3bc3cece4fe27870e9cdbbe
```

Le tag `20260807` est une release GitHub immuable signée; la release suivante du 14 août 2026 passe la ligne 3.12 à Python 3.12.14. Le choix `20260807` évite donc tout `latest` mutable et conserve exactement le pin GitSpace 3.12.13.

### Niveau de preuve

```yaml
evidence_level: PRIMARY_PROVIDER_METADATA_PLUS_IMMUTABLE_RELEASE
reproducibility: HIGH_FOR_BYTES_NOT_RUNTIME
limitations:
  - github_attestation_not_archived_or_verified_yet
  - binary_not_executed_on_target_worker
  - runtime_compatibility_not_proven
status: PILOT_BYTES_VERIFIED_NOT_EXECUTED
```

## uv managed candidate

L'index officiel Astral `uv.ndjson` a été interrogé en lecture seule pour l'artefact exact.

```yaml
provider: astral-sh/uv
record:
  version: 0.12.0
  date: 2026-07-28T18:58:12Z
artifact:
  platform: x86_64-unknown-linux-gnu
  variant: default
  archive_format: tar.gz
  url: https://github.com/astral-sh/uv/releases/download/0.12.0/uv-x86_64-unknown-linux-gnu.tar.gz
  sha256: eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9
```

```yaml
evidence_level: PRIMARY_PROVIDER_METADATA
reproducibility: HIGH_FOR_BYTES_NOT_RUNTIME
limitations:
  - github_attestation_not_archived_or_verified_yet
  - binary_not_executed_on_target_worker
status: PILOT_BYTES_VERIFIED_NOT_EXECUTED
```

Tous les checksums ci-dessus sont exactement 64 caractères hexadécimaux minuscules.

## Byte verification — PC1, sans exécution

Une expérience éphémère a téléchargé exactement les deux archives préférées ci-dessus dans un répertoire `/tmp` privé mode `0700`, sans extraction et sans exécution. Les bytes ont été re-hashés localement puis les métadonnées tar ont été inspectées avant suppression du staging.

```yaml
python_archive:
  http_code: 200
  bytes_received: 34163738
  content_length: 34163738
  sha256_observed: 506191be3ee7bd190a8834dcdc1b3bc70aab50608deccc711935aa007239cabd
  sha256_result: MATCH
  archive_entries:
    regular_files: 3485
    directories: 0
    symlinks: 1048
    hardlinks: 0
    unsafe_entries: 0
  archive_safety: SAFE
uv_archive:
  http_code: 200
  bytes_received: 21373358
  content_length: 21373358
  sha256_observed: eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9
  sha256_result: MATCH
  archive_entries:
    regular_files: 2
    directories: 1
    symlinks: 0
    hardlinks: 0
    unsafe_entries: 0
  archive_safety: SAFE
execution:
  archives_extracted: false
  downloaded_binaries_invoked: false
cleanup:
  staging_removed: true
  exists_after_cleanup: false
```

Le contrôle `SAFE` signifie seulement qu'aucun path absolu, traversal `..`, device, FIFO, socket ou lien sortant du root d'extraction n'a été détecté dans les métadonnées inspectées. Il ne constitue pas une preuve d'innocuité du code exécutable.

### Attestation

`gh 2.96.0` était disponible, mais `gh attestation verify` a refusé la vérification sans authentification GitHub. Conformément au contrat, aucune connexion, aucun token et aucune configuration utilisateur n'ont été ajoutés.

```yaml
python_attestation: NOT_VERIFIED_WITH_REASON_GH_AUTH_REQUIRED
uv_attestation: NOT_VERIFIED_WITH_REASON_GH_AUTH_REQUIRED
fallback_or_verification_weakening: false
```

Cette absence d'attestation vérifiée reste une gate distincte : les hashes correspondent, mais aucun binaire ne doit être exécuté sur cette seule base.

## GitSpace experiment required before adoption

Le toolchain ne devient pas `QUALIFIED` par recherche seule. La prochaine expérience doit :

1. réutiliser uniquement les URLs et SHA-256 verrouillés; re-hasher à nouveau les bytes sur le worker cible avant extraction;
2. vérifier et conserver les attestations GitHub des deux artefacts avec une identité autorisée, sans affaiblir la vérification;
3. extraire sous un préfixe Task 12 isolé, non global et supprimable, avec contrôles de paths/liens au moment de l'extraction;
4. exécuter uniquement après acceptation du risque d'exécution de binaires tiers sur le worker cible;
5. prouver `Python 3.12.13` et `uv 0.12.0`, puis les contrats projet concernés;
6. lancer le RED Task 12 avec uv offline/frozen et une politique réseau effectivement fermée ou une preuve équivalente explicitement acceptée;
7. supprimer le toolchain isolé si une gate échoue et conserver l'évidence négative.

## Counterexamples / fail-closed

- `python.org latest` ou `python-build-standalone latest` : rejeté, car le pin GitSpace est 3.12.13.
- `3.12.14` : rejeté même si plus récent; ce serait une modification de décision/toolchain, pas une requalification.
- Python hôte `3.12.3` : rejeté pour RED qualifiant.
- uv hôte `0.11.26` : rejeté pour RED qualifiant.
- artifact dont le digest diffère : `INFRA/BLOCKED`, jamais installation permissive.
- exécution d'un artefact non attesté/non re-hashé : interdite.

## Prochaine gate

`BLOCKED_WITH_EVIDENCE` : les bytes ont été téléchargés et re-hashés une première fois avec correspondance exacte, mais les attestations GitHub ne sont pas vérifiées et aucun binaire n'a été exécuté. La gate se ferme seulement après re-hash sur le worker cible, attestations vérifiées, extraction isolée contrôlée, exécution explicitement acceptée et observation des versions exactes. Cette gate est indépendante de la gate Docker/Harbor, qui reste elle aussi bloquée.
