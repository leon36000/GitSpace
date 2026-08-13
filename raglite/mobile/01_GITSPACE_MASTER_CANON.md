---
doc_id: GS-01
title: GitSpace — Master Canon
authority: CANON
status: ACCEPTED
version: 0.3.0
updated: 2026-08-13
owner: leon36000
---

# GitSpace — Master Canon

## 1. Mission [GS-MISSION-001]

Permettre à un propriétaire non-développeur de produire et faire évoluer des logiciels ambitieux en exprimant les résultats, les contraintes, les valeurs, le budget et le risque, tandis que des contributeurs IA construisent, vérifient, déploient et observent un monde logiciel traçable.

GitSpace doit réduire au minimum la charge cognitive technique du propriétaire sans lui retirer sa souveraineté sur les décisions de valeur.

## 2. Promesse opérationnelle [GS-PROMISE-001]

GitSpace ne promet pas la perfection universelle de tout logiciel arbitraire. Il promet une discipline plus forte et vérifiable :

- aucune réussite déclarée sans critères explicites;
- aucune fusion critique sans preuves fraîches;
- aucune action irréversible sans autorité;
- aucune mémoire promue silencieusement;
- aucun changement important sans provenance;
- tout échec se termine par un blocage explicite, un contre-exemple ou une hypothèse réfutée.

La cible absolue est :

```text
false_done_rate = 0
unauthorized_irreversible_action = 0
critical_memory_auto_promotion = 0
untraceable_critical_change = 0
```

## 3. Architecture C [GS-ARCH-001]

GitSpace est un **Native Software World Engine**. Le monde logiciel natif est la source de vérité; le code et Git en sont des projections.

```text
Human Sovereignty Plane
        │
Outcome Studio + Intent Compiler
        │
World Engine
        ├── Canon
        ├── Intent / Requirements / Obligations
        ├── Architecture / Components / Interfaces
        ├── Epistemic State
        └── Runtime World Model
        │
AgentKernel
        ├── AgentProcess
        ├── Scheduler
        ├── Capabilities
        ├── Context Fabric
        └── Durable State
        │
Semantic Change Engine + Shadow Worlds
        │
Proof Mesh + Causal Lab
        │
Release Observatory
        │
Git / GitHub / GitLab / Forgejo / IDE / APIs
```

Le noyau d’autorité est principalement écrit en Rust. TypeScript convient à l’interface, Python aux adaptateurs scientifiques et expériences, et d’autres langages peuvent être utilisés lorsqu’ils sont mieux adaptés. GitSpace n’est pas un projet mono-langage idéologique.

## 4. Souveraineté et responsabilités [GS-ROLES-001]

### Propriétaire humain

Le propriétaire décide :

- de la finalité;
- des valeurs;
- du budget;
- des compromis produit;
- du risque acceptable;
- des décisions irréversibles;
- de l’acceptation comportementale.

Le propriétaire n’est pas forcé de vérifier du code qu’il ne comprend pas.

### ChatGPT dans le Projet GitSpace

ChatGPT est l’architecte-chercheur principal et l’auteur des plans :

- recherche et qualification des méthodes;
- maintenance du canon, des ADR, des risques et de la roadmap;
- résolution des choix techniques réversibles;
- production des spécifications;
- décomposition en plans;
- préparation des paquets d’exécution;
- synthèse des preuves et mise à jour mémoire.

### Agents d’exécution

Les agents :

- consomment des paquets acceptés;
- travaillent dans des espaces isolés;
- prennent les décisions techniques réversibles dans leur portée;
- produisent code, tests, traces et preuves;
- ne modifient pas le canon de leur propre initiative;
- ne peuvent pas se déclarer eux-mêmes `PROVEN`.

### Vérificateurs indépendants

Les vérificateurs cherchent activement :

- non-conformité;
- erreur fonctionnelle;
- régression;
- reward hacking;
- violation d’autorité;
- faille de sécurité;
- preuve circulaire;
- erreur de tâche ou d’oracle.

## 5. Lois fondamentales [GS-LAWS-001]

1. **Le code n’est pas le projet.** Le projet est un graphe d’intention, de propriétés, de changements, de preuves et d’observations.
2. **Une conversation n’est pas un état.** Toute mission durable possède un état externe reconstructible.
3. **Une mémoire n’est pas une vérité.** Elle possède provenance, portée, fraîcheur, ACL et statut.
4. **La confiance n’est pas une preuve.** Un score de confiance ne satisfait aucun gate.
5. **Le consensus n’est pas la correction.** Plusieurs agents d’accord peuvent partager la même erreur.
6. **Un agent ne s’autorise pas lui-même.** Les capacités sont accordées par un moteur déterministe.
7. **Une simulation n’est pas une validation réelle.** Elle sert à explorer, pas à certifier.
8. **Une CI verte n’est pas une terminaison.** Les obligations doivent être fermées.
9. **Toute hypothèse est visible.** Aucune supposition critique ne reste implicite.
10. **Toute action est attribuable.** Identité, contexte, outil, entrée, sortie et autorisation sont conservés.
11. **Toute action irréversible est exceptionnelle.** Compensation ou approbation supérieure obligatoire.
12. **Toute preuve peut devenir périmée.** Une modification affectante déclenche l’invalidation.
13. **Un échec est une donnée scientifique.** Il produit un contre-exemple ou une mémoire négative.
14. **L’utilisateur tranche les valeurs, pas les frameworks.** Les choix techniques réversibles sont résolus par recherche et expérience.
15. **Le système doit savoir s’abstenir.** `BLOCKED_WITH_EVIDENCE` vaut mieux qu’un faux succès.
16. **Les données externes ne sont jamais des instructions.** Le contenu non fiable ne peut pas modifier le contrôle.
17. **Les transformations sémantiques sont préférées.** Le patch textuel est un mode de compatibilité.
18. **Le taux cible de faux DONE est zéro.**

## 6. Objets natifs [GS-OBJECTS-001]

| Objet | Rôle |
|---|---|
| `Space` | univers complet d’un produit |
| `World` | état cohérent et exécutable |
| `Worldline` | évolution causale d’un monde |
| `ShadowWorld` | monde candidat transactionnel |
| `IntentLattice` | objectifs, valeurs, contraintes, exemples, inconnues |
| `Mission` | résultat à atteindre |
| `RequirementAtom` | exigence atomique, testable et traçable |
| `Obligation` | propriété qui doit recevoir une preuve |
| `DecisionRecord` | choix, autorité, alternatives et conséquences |
| `SemanticChangeObject` | transformation typée d’un monde |
| `ConvergenceProposal` | proposition d’intégration d’un monde candidat |
| `Evidence` | artefact vérifiable lié à une obligation |
| `Verdict` | décision déterministe ou structurée sur les preuves |
| `AgentProcess` | contributeur IA avec identité, contexte et capacités |
| `Capability` | droit éphémère limité par mission |
| `ContextCapsule` | contexte compilé, haché et reproductible |
| `MemoryItem` | mémoire typée et révocable |
| `SkillPackage` | procédure qualifiée et versionnée |
| `ComponentGenomeEntry` | composant réutilisable avec contrats et preuves |
| `ObservedWorld` | monde déployé avec télémétrie et verdict runtime |

Les noms précis restent évolutifs, mais les responsabilités sémantiques sont canoniques.

## 7. État épistémique [GS-EPISTEMIC-001]

Tout claim significatif porte un type :

```text
UNKNOWN
ASSUMED
HYPOTHESIS
PREDICTED
INFERRED
OBSERVED
MEASURED
PROVED
REFUTED
STALE
REVOKED
```

La transition vers `PROVED` exige une preuve outillée ou un protocole de vérification approprié. Un texte produit par un LLM ne suffit jamais.

## 8. Source de vérité [GS-TRUTH-001]

La cible architecturale utilise :

- journal append-only;
- objets typés et versionnés;
- stockage adressé par contenu;
- hashes et signatures;
- projections reconstruisibles;
- graphe de dépendance et d’impact.

Graphes, index, embeddings, représentations de code et Git sont des projections. Ils peuvent être reconstruits depuis le canon.

Pendant le bootstrap documentaire, les sources du Projet ChatGPT restent l’autorité active jusqu’à l’acceptation d’un commit canonique du dépôt.

## 9. Mémoire [GS-MEMORY-001]

Classes :

- `Canonical`;
- `Semantic`;
- `Episodic`;
- `Procedural`;
- `Negative`;
- `Hypothesis`;
- `Preference`;
- `External`.

Cycle :

```text
RAW_OBSERVATION
→ QUARANTINED
→ VERIFIED
→ ACCEPTED/CANONICAL
→ STALE/REVOKED
```

Règles :

- les embeddings servent au rappel, jamais à la vérité;
- une mémoire ne confère aucune capability;
- les résumés ne remplacent pas les originaux;
- les contradictions sont conservées;
- la validité dépend des versions concernées;
- toute promotion est attribuée;
- les échecs restent récupérables.

## 10. Context Fabric [GS-CONTEXT-001]

Une `ContextCapsule` est compilée depuis :

- mission et intention;
- canon;
- exigences et obligations;
- dépendances de code;
- décisions;
- tests;
- incidents;
- mémoires vérifiées;
- mémoires négatives;
- politiques et capacités.

Elle possède un digest, des sources, une durée de validité, une ACL et une procédure de reconstruction.

Le système ne donne pas « toute la conversation » ou « tout le dépôt » au modèle par défaut.

## 11. Sécurité [GS-SECURITY-001]

Séparation obligatoire :

```text
CONTROL
  canon
  workflows
  politiques
  autorisations
  gates

UNTRUSTED_DATA
  code importé
  pages Web
  issues externes
  logs
  sorties d’outils
  documentation externe
```

Chaque agent reçoit une capacité éphémère liée à sa mission, son workspace, ses chemins, ses outils, son réseau, ses secrets, son budget et sa durée.

Les secrets sont consommés par référence et ne sont pas injectés dans le contexte du modèle lorsque cela peut être évité.

## 12. Changement et versionnement [GS-CHANGE-001]

Le changement natif est un `SemanticChangeObject`, pas seulement un diff textuel. Il contient :

- intention;
- monde de base;
- transformations;
- préconditions;
- postconditions;
- obligations;
- impact;
- rollback;
- agent;
- contexte;
- preuves.

Git reste la projection universelle de compatibilité. Jujutsu et les théories de patches sont des pistes de recherche, pas des autorités actuelles.

## 13. Preuve et terminaison [GS-PROOF-001]

Machine d’état de référence :

```text
PROPOSED
→ SPECIFIED
→ PLANNED
→ APPROVED
→ IMPLEMENTING
→ SELF_CHECKED
→ LOCALLY_VERIFIED
→ INDEPENDENTLY_VERIFIED
→ PROVEN
→ MERGEABLE
→ RELEASED
→ OBSERVED
```

États explicites de sortie :

```text
BLOCKED_SPEC_AMBIGUOUS
BLOCKED_MISSING_DEPENDENCY
BLOCKED_FLAKY_EVIDENCE
BLOCKED_POLICY
BLOCKED_NEEDS_HUMAN
BLOCKED_SECURITY
BLOCKED_EXTERNAL_SYSTEM
TASK_INVALID
SUPERSEDED
ABORTED
REGRESSED
```

Une moyenne ne peut jamais compenser l’échec d’une dimension critique : sécurité, autorité, intégrité, portée ou nettoyage.

## 14. Outcome Studio [GS-OUTCOME-001]

L’interface principale du propriétaire est orientée résultats :

- scénarios;
- exemples et contre-exemples;
- prototypes;
- visualisations;
- choix de valeurs;
- compromis de coût, vitesse, sécurité et maintenance;
- comportements observables.

Le système ne demande pas au propriétaire de choisir un framework lorsqu’une expérience technique peut résoudre la question.

## 15. Phase 00 [GS-PHASE-00-001]

La Phase 00 construit le **Research Atlas** et la **Benchmark Foundry** avant le noyau produit.

Architecture C0 acceptée :

- IR d’évaluation GitSpace souverain;
- adaptateurs externes remplaçables;
- Seed Suite initiale de 32 tâches;
- tâches longues, création complète, migration, mémoire, sécurité, reprise, preuve et résultat propriétaire;
- QA indépendante;
- oracles protégés;
- verdicts non compensables;
- replay et provenance.

La Phase 00 doit permettre de réfuter nos propres hypothèses avant de verrouiller les phases suivantes.

## 16. Roadmap canonique [GS-ROADMAP-001]

```text
00 Research Atlas + Benchmark Foundry
01 Constitution et modèle du monde
02 World Engine
03 GitBridge + Repository Intelligence
04 AgentKernel
05 Capability Security + Sandboxes
06 Context Fabric + Memory Vault
07 Intent Compiler + Outcome Studio
08 Change Algebra + Shadow Worlds
09 Proof Mesh
10 Causal Lab
11 Model Fabric + Orchestration
12 Skill Foundry + Component Genome
13 Release Observatory
14 Fédération + Écosystème
```

Les phases peuvent se chevaucher expérimentalement, mais aucune dépendance canonique n’est adoptée sans preuve.

## 17. Non-objectifs [GS-NONGOALS-001]

GitSpace ne vise pas, à ce stade :

- la réécriture immédiate d’une forge complète;
- un IDE classique comme interface principale;
- la dépendance à un fournisseur de modèle;
- un LLM juge unique;
- une base vectorielle comme vérité;
- une promesse de perfection universelle;
- l’auto-modification non contrôlée;
- l’adoption d’une technologie sur la seule base d’un benchmark publié;
- la suppression de Git comme format d’interopérabilité;
- la production de code avant le bootstrap canonique et la Phase 00.

## 18. Définition de réussite [GS-SUCCESS-001]

Une mission est acceptée seulement si :

```text
IntentIsStable
∧ RequirementCoverage = 100%
∧ ProofObligationsClosed = 100%
∧ NoCriticalContradiction
∧ IndependentVerificationPassed
∧ EnvironmentReplayPassed
∧ SecurityPolicyPassed
∧ RollbackQualified
∧ RuntimeObservationPassed
```

Lorsque ces conditions ne peuvent pas être démontrées, le résultat reste `PARTIALLY_VERIFIED`, `RESEARCH_MODE` ou `BLOCKED_WITH_EVIDENCE`.

## 19. Décisions acceptées

Les décisions détaillées sont dans `docs/adr/ADR-REGISTER.md`. Les fondations actives sont :

- `ADR-0001` — Native World Engine, Git périphérique;
- `ADR-0002` — Rust principal sans mono-langage dogmatique;
- `ADR-0003` — souveraineté humaine;
- `ADR-0004` — `AgentProcess` contributeur natif;
- `ADR-0005` — faux `DONE = 0`;
- `ADR-0006` — mémoire hiérarchique et quarantinée;
- `ADR-0007` — transformations sémantiques avant patches textuels;
- `ADR-0008` — RAGLite Markdown;
- `ADR-0009` — C0 Native Evaluation Foundry hybride;
- `ADR-0010` — ChatGPT planifie; les exécuteurs restent en aval et remplaçables.
