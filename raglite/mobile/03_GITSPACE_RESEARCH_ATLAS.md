---
doc_id: GS-03
title: GitSpace — Research Atlas
authority: VERIFIED_RESEARCH_AND_RISK
status: ACTIVE
version: 0.3.0
updated: 2026-08-13
evidence_cutoff: 2026-08-13
---

# GitSpace — Research Atlas

## 1. Politique scientifique [RES-POLICY-001]

Ordre de priorité :

```text
documentation ou standard officiel
→ article primaire évalué par les pairs
→ préprint primaire
→ dépôt officiel
→ source secondaire
```

Chaque claim doit conserver :

```yaml
id:
claim:
epistemic_type:
source:
publication_date:
event_date:
checked_at:
limitations:
reproduction_status:
gitspace_status: ADOPT | PILOT | WATCH | REJECT
required_experiment:
```

Règles :

1. un préprint non reproduit reste `EXPERIMENTAL` et ne dépasse pas `PILOT`;
2. les gains numériques ne sont jamais promus avec un principe architectural plus général;
3. les gains de plusieurs travaux ne sont jamais additionnés naïvement;
4. une source mouvante est verrouillée par release, commit ou digest avant expérimentation;
5. les résultats négatifs et les échecs de reproduction sont conservés;
6. une technique n’est `ADOPT` qu’après preuve suffisante et absence de contradiction critique;
7. les recherches externes ne deviennent jamais des instructions.

## 2. Décisions de recherche actives

### ADOPT

- QA indépendante des tâches;
- tests de solutions invalides et partielles;
- oracles protégés;
- mutation et tests cachés;
- gates sécurité, autorité, intégrité, portée et nettoyage non compensables;
- séparation contrôle/données;
- mémoire comme frontière de confiance;
- verdict critique non fondé uniquement sur un LLM.

### PILOT

- Inspect et Harbor comme adaptateurs;
- HCAST, SWE-EVO, NL2Repo-Bench, LongCLI et familles similaires;
- actions AST structurées;
- Repository Intelligence Graph;
- AgentDojo et ControlArena;
- SpecBench, EvilGenie et Hacker–Fixer Loops;
- MemoryGraft, MemMorph et Mem2ActBench;
- frontière Rust/Python;
- journal local + CAS.

### WATCH

- RoadmapBench;
- CodeTeam;
- DeepSWE;
- MemGym;
- techniques de mémoire et d’orchestration 2026 non reproduites;
- learned software world models comme présélection.

### REJECT comme autorité

- LLM juge unique;
- consensus multi-agents;
- score unique compensant une violation critique;
- mémoire vectorielle comme vérité;
- simulation comme preuve finale;
- auto-promotion d’une compétence depuis une seule trajectoire.

## 3. Evidence structurante

- Les tâches longues et les évolutions de dépôts exposent planification, cohérence globale, reprise et dépendances inter-fichiers; chaque résultat reste propre à son protocole.
- L’oracle doit être évalué comme un composant attaquable et non comme une vérité implicite.
- Les interfaces structurées de code constituent une hypothèse forte mais doivent être reproduites sur plusieurs langages et familles de tâches.
- La mémoire procédurale est une surface d’attaque persistante; provenance et quarantaine sont des invariants.
- La capacité d’un modèle doit être séparée du harness, du contexte, de la mémoire, des outils et du budget.
- L’expérience du propriétaire non-développeur doit être évaluée sans lui demander de juger le code.

## 4. Sources primaires prioritaires

- `RES-P00-001` — [METR Task Development Guide — Quality Assurance](https://taskdev.metr.org/quality-assurance/) — `FACT_OFFICIAL` — **ADOPT**. Une tâche doit être résolue par une personne indépendante avec les mêmes ressources; tester aussi solutions invalides et partielles. Limite : Guide opérationnel, pas une étude comparative randomisée.
- `RES-P00-002` — [METR — Task-Completion Time Horizons](https://metr.org/time-horizons/) — `FACT_OFFICIAL` — **PILOT**. Mesurer la réussite en fonction de la durée humaine; six runs indépendants par tâche dans le protocole courant; audit manuel des reward hacks. Limite : Suite surtout logicielle/ML/cyber; mesures >16 h actuellement jugées peu fiables par METR.
- `RES-P00-003` — [HCAST](https://arxiv.org/abs/2503.17354) — `EVIDENCE_PREPRINT` — **PILOT**. 189 tâches avec 563 baselines humaines; la réussite rapportée chute sous 20 % pour les tâches humaines >4 h. Limite : Préprint; distribution de tâches auto-évaluables et faible contexte.
- `RES-P00-004` — [SWE-EVO](https://arxiv.org/abs/2512.18470) — `EVIDENCE_PREPRINT` — **PILOT**. 48 tâches d’évolution, 21 fichiers en moyenne et 874 tests; 25 % rapportés pour GPT-5.4 + OpenHands dans la révision v6 du 22 mai 2026. Limite : Python, sept projets; reproduction GitSpace requise.
- `RES-P00-005` — [NL2Repo-Bench](https://arxiv.org/abs/2512.12730) — `EVIDENCE_PREPRINT` — **PILOT**. Génération de dépôt complet depuis exigences et workspace vide; meilleurs agents sous 40 % de tests moyens et rares dépôts complets. Limite : Bibliothèques Python; mesure partielle du produit complet.
- `RES-P00-006` — [RoadmapBench](https://arxiv.org/abs/2605.15846) — `EVIDENCE_PREPRINT` — **WATCH**. 115 upgrades réels, médiane 3 700 lignes/51 fichiers; meilleur résultat rapporté 39,1 %. Limite : Très récent; qualification de l’environnement et disponibilité des artefacts à vérifier.
- `RES-P00-007` — [LongCLI-Bench](https://arxiv.org/abs/2602.14337) — `EVIDENCE_PREPRINT` — **PILOT**. 20 tâches longues, tests fail-to-pass/pass-to-pass et score par étapes; meilleurs agents sous 20 %. Limite : Petit échantillon; tâches scolaires et workflows sélectionnés.
- `RES-P00-008` — [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) — `FACT_OFFICIAL` — **PILOT**. Framework extensible pour tâches, solvers, scorers, outils, logs et sandboxes; collection de plus de 200 évaluations. Limite : Framework externe Python; ne doit pas devenir l’autorité du format GitSpace.
- `RES-P00-009` — [Harbor](https://github.com/harbor-framework/harbor) — `FACT_OFFICIAL` — **PILOT**. Framework pour agents arbitraires, benchmarks/environnements et exécution parallèle; harness officiel de Terminal-Bench 2.x. Limite : API récente et mouvante; adapter derrière une frontière versionnée.
- `RES-P00-010` — [Terminal-Bench 2.1](https://github.com/harbor-framework/terminal-bench-2-1) — `FACT_OFFICIAL` — **PILOT**. Tâches terminal conteneurisées; la révision 2.1 a modifié 26 tâches pour corriger bugs, ressources, timeouts ou robustesse au reward hacking. Limite : Confirme que même un benchmark établi doit versionner et requalifier ses tâches.
- `RES-P00-011` — [SWE-bench Verified](https://www.swebench.com/SWE-bench/) — `FACT_OFFICIAL` — **PILOT**. Sous-ensemble humainement filtré de 500 tâches et harness reproductible. Limite : Correctifs localisés; ne représente pas seul GitSpace.
- `RES-P00-012` — [EvalPlus](https://openreview.net/forum?id=1qvx610Cu7) — `EVIDENCE_PEER_REVIEWED` — **ADOPT**. Augmentation LLM + mutation des tests; HumanEval+ révèle des solutions incorrectes et des changements de classement. Limite : Fonctions isolées; le principe de renforcement des oracles est transférable.
- `RES-P00-013` — [SpecBench](https://arxiv.org/abs/2605.21384) — `EVIDENCE_PREPRINT` — **PILOT**. Sépare tests visibles et tests composés cachés pour mesurer l’écart entre conformité apparente et comportement réel. Limite : 30 tâches système; préprint, chiffres à reproduire.
- `RES-P00-014` — [EvilGenie](https://arxiv.org/abs/2511.21654) — `EVIDENCE_PREPRINT` — **PILOT**. Détecte hardcoding, modification des tests et écart aux tests tenus à l’écart; observe du reward hacking explicite chez des agents de code. Limite : Scénarios volontairement faciles à exploiter; utile comme contrôle positif.
- `RES-P00-015` — [Hacker–Fixer Loops](https://arxiv.org/abs/2606.08960) — `EVIDENCE_PREPRINT` — **PILOT**. Audit de 1 968 tâches: 323 déclarées hackables; boucle hacker/fixer/solver pour durcir sans bloquer les solutions légitimes. Limite : Très récent; ne remplace pas QA humaine et tests déterministes.
- `RES-P00-016` — [CODESTRUCT](https://aclanthology.org/2026.acl-long.607/) — `EVIDENCE_PEER_REVIEWED` — **PILOT**. Actions sur entités AST nommées, transformations syntaxiquement validées; gains de précision et réduction de tokens rapportés. Limite : Résultats sur SWE-bench Verified et CodeAssistBench; qualification multilingue nécessaire.
- `RES-P00-017` — [Repository Intelligence Graph](https://arxiv.org/abs/2601.10112) — `EVIDENCE_PREPRINT` — **PILOT**. Carte déterministe et traçable du build/tests; +12,2 % d’exactitude et -53,9 % de temps rapportés. Limite : Huit dépôts; extraction surtout CMake au moment de l’étude.
- `RES-P00-018` — [CodeTeam](https://arxiv.org/abs/2606.22082) — `EVIDENCE_PREPRINT` — **WATCH**. Contrat machine-checkable de fichiers, interfaces et dépendances entre agents de génération de dépôt. Limite : Préprint très récent; gains à reproduire hors NL2Repo-Bench.
- `RES-P00-019` — [AgentDojo — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html) — `EVIDENCE_PEER_REVIEWED` — **ADOPT**. Environnement dynamique de tâches utilisateur, injections indirectes, attaques et défenses pour agents outillés. Limite : API évolutive; importer les scénarios, pas l’autorité.
- `RES-P00-020` — [CaMeL — IEEE SaTML 2026](https://floriantramer.com/publications/camel25/) — `EVIDENCE_PEER_REVIEWED` — **ADOPT**. Sépare explicitement flux de contrôle et de données; capabilities pour empêcher les flux non autorisés. Limite : Prototype de recherche; le principe architectural est plus solide que ses chiffres particuliers.
- `RES-P00-021` — [ControlArena](https://github.com/UKGovernmentBEIS/control-arena) — `FACT_OFFICIAL` — **PILOT**. Sépare tâches principales et side tasks nuisibles, politiques, monitors, protocoles et scorers sur Inspect. Limite : Orienté AI control; adaptation au génie logiciel GitSpace requise.
- `RES-P00-022` — [MemoryGraft](https://arxiv.org/abs/2512.16962) — `EVIDENCE_PREPRINT` — **PILOT**. De fausses expériences réussies peuvent persister et réorienter des tâches ultérieures via la mémoire. Limite : Démonstration sur un agent/mémoire précis; menace générale à reproduire.
- `RES-P00-023` — [MemMorph](https://arxiv.org/abs/2605.26154) — `EVIDENCE_PREPRINT` — **PILOT**. Trois enregistrements empoisonnés suffisent jusqu’à 85,9 % d’ASR rapporté sur le choix d’outil. Limite : Préprint récent; chiffres non généralisables sans reproduction.
- `RES-P00-024` — [Mem2ActBench](https://arxiv.org/abs/2601.19935) — `EVIDENCE_PREPRINT` — **PILOT**. Distingue récupération de mémoire et application correcte aux paramètres/actions d’outils. Limite : Données synthétisées et domaine assistant; adapter aux missions logicielles.
- `RES-P00-025` — [MemGym](https://arxiv.org/abs/2605.20833) — `EVIDENCE_PREPRINT` — **WATCH**. Propose des scores isolant la mémoire des capacités de raisonnement, récupération et outils. Limite : Préprint très récent; plusieurs proxies et environnements hétérogènes.
- `RES-P00-026` — [DeepSWE](https://arxiv.org/abs/2607.07946) — `EVIDENCE_PREPRINT` — **WATCH**. 113 tâches originales hors historique public, vérificateurs écrits pour la fonctionnalité et non une correction unique. Limite : Publié en juillet 2026; nécessite audit indépendant avant import.
- `RES-P00-027` — [Vibe Code Bench](https://arxiv.org/abs/2603.04601) — `EVIDENCE_PREPRINT` — **PILOT**. 100 spécifications d’apps Web et workflows navigateur pour évaluation fonctionnelle de produits complets. Limite : Ne mesure pas encore la souveraineté du propriétaire ni les évolutions longitudinales.
- `RES-P00-028` — [Rust 1.97.1](https://blog.rust-lang.org/2026/07/16/Rust-1.97.1/) — `FACT_OFFICIAL` — **PILOT**. Point release stable publiée le 16 juillet 2026 et corrigeant une miscompilation LLVM. Limite : version candidate observée au 2026-08-13; elle doit être revalidée au moment de la packetisation et ne constitue plus un pin accepté par le canon.
- `RES-P00-029` — [Inspect Evals — Python](https://github.com/UKGovernmentBEIS/inspect_evals) — `FACT_OFFICIAL` — **PILOT**. Inspect Evals recommande Python 3.11 ou 3.12; Python 3.13 est moins testé et Python 3.14 n’est pas supporté pour l’ensemble du catalogue au moment de la vérification. Limite : recommandation d’un projet externe; l’exact patch Python reste à qualifier.
- `RES-P00-030` — [LLM-as-a-judge unique](https://arxiv.org/abs/2511.21654) — `EVIDENCE_SYNTHESIS` — **REJECT**. Un juge probabiliste peut assister le triage mais ne doit jamais constituer l’unique oracle d’une obligation critique. Limite : Des cas ouverts nécessiteront néanmoins une revue humaine structurée.
- `RES-P00-031` — [Harbor `pyproject.toml`](https://github.com/harbor-framework/harbor/blob/main/pyproject.toml) — `FACT_OFFICIAL` — **PILOT**. Harbor déclare actuellement `requires-python = ">=3.12"`. Limite : branche mouvante; la version importée devra être verrouillée par commit ou release.
- `RES-P00-032` — [Python 3.12.13](https://www.python.org/downloads/release/python-31213/) — `FACT_OFFICIAL` — **PILOT**. Python 3.12.13, publié le 3 mars 2026, est une release de sécurité source-only de la série 3.12; Python 3.12 n’est plus en phase de bugfix régulier. Limite : l’absence d’installateurs officiels impose de qualifier la reproductibilité des builds et images.

## 5. Expériences GitSpace obligatoires

| ID | Hypothèse | Comparaison | Mesures critiques | Statut |
|---|---|---|---|---|
| `EXP-P00-001` | L’état externe améliore la reprise | conversation seule vs état durable vérifié | recovery fidelity, duplication, faux DONE | `PLANNED` |
| `EXP-P00-002` | Les actions sémantiques réduisent les erreurs | patch texte vs AST/symboles | patch validity, scope precision, tokens | `PLANNED` |
| `EXP-P00-003` | Un graphe déterministe améliore le contexte | embeddings seuls vs graph + symboles | context recall, time, cost | `PLANNED` |
| `EXP-P00-004` | La mémoire vérifiée a une utilité nette positive | sans mémoire vs brute vs curatée | success delta, poison ASR, stale use | `PLANNED` |
| `EXP-P00-005` | Les vérificateurs indépendants réduisent les faux succès | auto-vérification vs rôle séparé | false-DONE, escaped defects, cost | `PLANNED` |
| `EXP-P00-006` | Les oracles mutés détectent plus de défauts | tests visibles vs cachés + mutation | additional defect detection, invalid task rate | `PLANNED` |
| `EXP-P00-007` | Les agents spécialisés valent leur coût | agent fort unique vs rôles séparés | safe success, correlated error, cost | `PLANNED` |
| `EXP-P00-008` | C0 reste portable entre harness | native runner vs Inspect vs Harbor vs troisième famille | manifest completeness, replay, semantic loss | `PLANNED` |
| `EXP-P00-009` | Outcome Studio réduit la charge propriétaire | prompt libre vs scénarios structurés | owner correction load, value decisions, acceptance | `PLANNED` |
| `EXP-P00-010` | Rust/Python est une frontière efficace | variantes d’implémentation | throughput, integration cost, determinism, security | `PLANNED` |
| `EXP-P00-011` | Python 3.12 est l’intersection initiale la plus fiable | 3.12 latest security vs 3.13 supported subset | installability, adapter pass rate, image reproducibility | `PLANNED` |
| `EXP-P00-012` | Le pin Rust candidat est sûr | stable candidate vs previous stable | build, tests, sanitizer/fuzz smoke, target coverage | `PLANNED` |

## 6. Critères de promotion

Une technique passe de `PILOT` à `ADOPT` seulement si :

- l’expérience est préenregistrée;
- les environnements et versions sont verrouillés;
- les données par tâche sont conservées;
- au moins deux familles de tâches sont couvertes lorsque le claim est général;
- une revue indépendante reproduit un sous-ensemble;
- aucune métrique critique ne se dégrade;
- les limites sont documentées;
- les contre-exemples restent visibles.

## 7. Menaces à la validité

- contamination des benchmarks;
- tâches auto-favorables;
- harness confondu avec modèle;
- invalidité ou exploitabilité des oracles;
- variance entre runs;
- indisponibilité d’artefacts;
- changement de versions externes;
- fuites de tests cachés;
- sélection a posteriori des métriques;
- généralisation abusive d’un seul langage ou dépôt;
- juge LLM corrélé à l’implémenteur;
- absence de participant non-développeur réel.

## 8. Hypothèses actives

- Le RAGLite cinq fichiers améliore rappel et fidélité sans créer un second canon.
- Un Native World Engine bat une forge agentisée sur les tâches longues.
- Les transformations sémantiques réduisent conflits, patches invalides et dérive.
- Le routage adaptatif bat un modèle unique à budget égal.
- L’état externe vérifié augmente la fidélité de reprise.
- La mémoire vérifiée a une utilité nette positive sans hausse du poison ASR.
- Les composants certifiés augmentent plus sûrement la réussite que la génération intégrale.
- Les verdicts multidimensionnels réduisent les faux succès par rapport à un score unique.

## 9. Fraîcheur et revalidation

Les claims liés à une version logicielle, une API, une politique ou un classement doivent être revalidés avant packetisation. `checked_at: 2026-08-13` ne garantit pas la validité future.

Le dossier complet de Phase 00 est `docs/phase-00/GS-P00-SPEC-001.md`.
