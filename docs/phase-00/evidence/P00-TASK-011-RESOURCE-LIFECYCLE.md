---
evidence_id: P00-TASK-011-RESOURCE-LIFECYCLE
status: GREEN_VERIFIED_PRE_REVIEW
recorded_at: 2026-08-14
framework: inspect-ai
framework_version: 0.3.258
framework_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
---
# P00-TASK-011 — Cycle de vie des événements Inspect

## Finding

**EVIDENCE:** un seul run contrôlé Inspect 0.3.258 laissait un `anyio.streams.memory.MemoryObjectReceiveStream` ouvert après suppression des références et trois cycles de garbage collection.

L’état mesuré du canal abandonné était :

```yaml
closed: false
buffered: 0
open_send_streams: 0
open_receive_streams: 1
tasks_waiting_send: 0
tasks_waiting_receive: 0
```

Il ne s’agissait ni d’un log retenu ni de la classe `EvalLogs`. La source officielle pinée, `inspect_ai/hooks/_hooks.py::drain_sample_events`, ferme le sender, attend l’émetteur, vide le receiver, puis met `active.event_receive = None` sans fermer le receiver.

## REDs

### Warning reproductible

```yaml
head: 40331a8c168f37ba0f55facf40f70d5f6f3c03e7
workflow_run: 31842092901
workflow_job: 94900961438
result: expected_failure
finding: one unclosed MemoryObjectReceiveStream after one run
```

### État interne mesuré

```yaml
head: 1a9c7e23d6744e58f72b0adba6c3e9d7182cd849
workflow_run: 31842288104
workflow_job: 94901542755
result: expected_failure
```

### Premier shim invalide

```yaml
head: f27b704fb1e68b412b8263a81bbf876a87644986
workflow_run: 31842865496
workflow_job: 94903273992
result: expected_failure
cause: the shim requested non-exported private names instead of mirroring the pinned source
```

Ce RED a empêché qu’une hypothèse plausible sur l’API AnyIO ou Inspect soit promue comme correctif.

## Correction bornée

Task 11 est pinée à Inspect 0.3.258. Pendant le seul appel `inspect_eval` qualifié, l’adaptateur :

1. acquiert un lock de processus;
2. remplace temporairement `inspect_ai.hooks._hooks.drain_sample_events`;
3. reproduit le comportement officiel : fermeture du sender, attente de `event_done`, vidage `receive_nowait`, émission des événements résiduels;
4. ajoute uniquement `await receive.aclose()` dans `finally`;
5. nettoie `event_send`, `event_receive` et `event_done`;
6. restaure toujours la fonction Inspect originale, après succès ou exception.

La distribution installée n’est pas modifiée. Le shim n’élargit aucune capability et n’est actif que dans le bloc sérialisé du run contrôlé.

## GREEN

```yaml
pre_documentation_head: 134f110f4917b137ef1151ba2ad77345a8d75cb0
workflow_run: 31843227076
workflow_job: 94904335561
conclusion: success
```

Les tests vérifient :

- aucun nouveau receiver AnyIO ouvert après un run réel et GC forcé;
- fonction Inspect originale restaurée après succès;
- fonction Inspect originale restaurée après exception d’eval;
- wrapper runtime exact `EvalLogs` ou list builtin seulement;
- élément exact `EvalLog` et cardinalité 1;
- deux mutations dédiées tuées : `drop-event-receiver-close` et `drop-cleanup-shim-restore`.

La campagne complète pré-documentation a tué 24/24 mutations.

## Limites et contre-exemples

- `LIMIT` — usage d’une API privée, accepté uniquement sous pin release + wheel hash + tests de source/comportement.
- `LIMIT` — un autre code exécutant directement Inspect en concurrence sans utiliser le lock GitSpace reste hors contrat.
- `LIMIT` — chaque future release Inspect doit supprimer ou requalifier ce shim; aucune compatibilité prospective n’est supposée.
- `BLOCKED` — aucune identité externe séparée n’a reproduit ce finding ou son correctif.
- `BLOCKED` — merge signé et replay post-merge manquent encore.

## Décision

Le finding amont est fermé dans la fixture Task 11 uniquement. Il reste conservé comme mémoire négative et comme condition de requalification d’Inspect.
