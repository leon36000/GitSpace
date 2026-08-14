---
evidence_id: GS-EVIDENCE-P00-TASK-009-READ-ONLY-REPLAY
subject: P00-TASK-009
status: GREEN_VERIFIED_PRE_REVIEW
updated: 2026-08-14
---
# P00-TASK-009 — Replay réellement non mutateur

## Finding

**EVIDENCE:** le CLI `replay` utilisait initialement le même constructeur que `run`. Ce constructeur initialisait le root Foundry, le CAS et le runner avant que le replay puisse vérifier la présence et l’intégrité du store.

Un replay annoncé read-only pouvait donc :

- créer un store Foundry absent avant d’échouer;
- recréer un root `runner/` supprimé alors que le replay ne l’utilise pas;
- recréer silencieusement `cas/tmp/` et masquer une disposition CAS incomplète.

Le contenu canonique des artefacts n’était pas modifié, mais le contrat « aucun write ni réparation pendant replay » était faux au niveau du filesystem.

## RED

```text
commit: a86bf88fe14052dc859cf9d2de5975bbb93362d9
workflow run: 31789428502
job: 94732757021
checkout: exact detached head
permissions: contents: read
result: failure attendue
```

Trois contre-exemples échouaient :

```text
replay_does_not_initialize_an_absent_store
replay_does_not_recreate_the_runner_root
replay_does_not_repair_a_missing_cas_layout_directory
```

Les autres contrats Task 9 restaient verts, ce qui isolait la mutation d’ouverture plutôt qu’un défaut général du replay.

## Correction

La frontière d’ouverture est maintenant explicite :

```text
NativeFoundry::open
  → initialise un store exécutable
  → ouvre CAS + runner
  → autorise run

NativeFoundry::open_read_only
  → exige un root existant et réel
  → exige CAS objects/sha256, CAS tmp, journal et journal/runs
  → n’ouvre pas le runner
  → n’autorise jamais run
```

Le replay revalide également la disposition CAS/journal immédiatement avant toute ouverture de `LocalCas`. Une disposition supprimée après construction du handle échoue donc sans être réparée.

Le root `runner/` n’est pas requis pour replay et n’est jamais recréé par celui-ci.

## GREEN

```text
implementation commit: af2ba5c8556b04b5fe4d748816fceaf58a16a27e
Task 9 workflow run: 31790564562
Task 9 job: 94736288943
checkout: exact detached head
permissions: contents: read
Task 9 conclusion: success
all eight Phase 00 workflows at this head: success
```

Les assertions fraîches couvrent :

- store absent : échec sans création;
- root runner absent : replay réussi sans recréation;
- `cas/tmp` absent : échec sans réparation via le CLI;
- `cas/tmp` absent : échec sans réparation via l’API Rust;
- handle read-only : `run` refusé avant tout effet;
- replay valide : mêmes bytes, aucun nouvel objet CAS et aucun changement journal;
- suites de substitutions sémantiques, provenance multi-commit et cinq classifications toujours vertes;
- workspace complet, Clippy `-D warnings`, rustfmt, lock graph et clean-tree verts.

## Limites et risques résiduels

- **LIMIT:** la primitive `LocalEventJournal::open` peut créer `journal/runs`; la validation préalable empêche cette création lorsque le layout est absent, mais Task 9 n’expose pas encore un constructeur read-only souverain dans `gs-event-journal`.
- **LIMIT:** la validation et les lectures ne sont pas atomiques face à un adversaire local concurrent pouvant remplacer les chemins après inspection. Le M0 local n’est pas présenté comme une défense complète contre un processus filesystem hostile concurrent.
- **BLOCKED:** aucune revue indépendante par une identité séparée n’est encore enregistrée.
- **BLOCKED:** aucun merge signé, replay frais sur `main`, promotion canonique ou projection RAGLite n’est encore disponible.

## Status

`P00-TASK-009` reste `PARTIALLY_VERIFIED` / `GREEN_VERIFIED_PRE_REVIEW`. Ce finding est fermé uniquement à la frontière code + exact-head CI.
