# GitSpace

> **Statut : bootstrap canonique en pull request brouillon — aucun code produit GitSpace n’est encore implémenté.**

GitSpace est un **Native Software World Engine** conçu nativement pour des contributeurs IA. Son but est de permettre à un propriétaire non-développeur de créer et faire évoluer des logiciels ambitieux en gouvernant l’intention, les valeurs, le budget et le risque, tandis que des agents techniques prennent en charge les choix réversibles, l’implémentation, le débogage et la preuve.

## Ce qui rend GitSpace différent

GitSpace ne traite pas le dépôt Git comme le projet. Le projet est un monde logiciel typé composé d’intentions, d’exigences, d’obligations, de décisions, de transformations sémantiques, de preuves, d’exécutions et d’observations. Git et les forges restent des périphéries de compatibilité, d’import, d’export et de publication.

Invariants :

- une conversation n’est pas un état durable;
- une mémoire n’est pas une vérité;
- la confiance et le consensus ne sont pas des preuves;
- un agent ne s’autorise pas et ne se déclare pas lui-même terminé;
- toute action, hypothèse et preuve est typée, attribuée et révocable;
- le taux cible de faux `DONE` est zéro.

## Architecture acceptée

**Architecture C — Native World Engine**, principalement en Rust, avec Outcome Studio, Intent Compiler, World Engine, AgentKernel, Context Fabric, Memory Vault, Semantic Change Engine, Shadow Worlds, Proof Mesh, Causal Lab et Release Observatory.

La Phase 00 adopte **C0 — Native Evaluation Foundry hybride** : un IR d’évaluation GitSpace souverain, des adaptateurs externes remplaçables et une Seed Suite native initiale de 32 tâches.

## Bootstrap en cours

La pull request brouillon **#1** propose le corpus canonique initial :

```text
main@f69b22d...
  └─ A 488fd399... : 19 documents canoniques
       └─ B 08a38c43... : manifeste + 5 projections RAGLite
```

- la PR est ouverte et mergeable;
- `main` n’a pas été modifiée directement;
- `hermesclaw-ci` est préservée;
- aucun code produit, dépendance, licence ou CI produit n’est inclus;
- le statut reste `PARTIALLY_VERIFIED` jusqu’aux revues et à la décision propriétaire.

## Ordre de lecture

1. [`00_GITSPACE_START_HERE.md`](00_GITSPACE_START_HERE.md)
2. [`02_GITSPACE_NOW_DECISIONS_ROADMAP.md`](02_GITSPACE_NOW_DECISIONS_ROADMAP.md)
3. [`01_GITSPACE_MASTER_CANON.md`](01_GITSPACE_MASTER_CANON.md)
4. [`03_GITSPACE_RESEARCH_ATLAS.md`](03_GITSPACE_RESEARCH_ATLAS.md)
5. [`04_GITSPACE_AGENT_PROTOCOL.md`](04_GITSPACE_AGENT_PROTOCOL.md)
6. [`docs/phase-00/GS-P00-SPEC-001.md`](docs/phase-00/GS-P00-SPEC-001.md)
7. [`docs/phase-00/GS-P00-PLAN-001.md`](docs/phase-00/GS-P00-PLAN-001.md)

Tout agent doit aussi lire [`AGENTS.md`](AGENTS.md).

## Autorité

```text
Instructions du projet
> canon accepté
> ADR acceptées
> état courant
> recherche vérifiée
> hypothèses et risques
> journaux de session
> conversations
```

## Dépôt et RAGLite

Le dépôt devient la mémoire canonique éditable seulement après merge accepté. Le RAGLite mobile est une projection byte-identical générée depuis un commit canonique identifié. Voir [`raglite/README.md`](raglite/README.md).

## Licence

`UNKNOWN` — aucune licence n’est choisie implicitement.
