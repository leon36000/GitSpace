---
doc_id: GS-P00-PLAN-001
title: GitSpace — Phase 00 Implementation Plan
status: ACCEPTED_MASTER_PLAN_PACKET_REQUIRED
verification: DOCUMENT_REVIEWED_NOT_EXECUTED
version: 0.4.0
updated: 2026-08-13
spec_ref: GS-P00-SPEC-001@0.3.0
planner: CHATGPT_PROJECT_GITSPACE
executor: DEFERRED_REPLACEABLE
execution_packet_required: true
---

# GitSpace Phase 00 — Research Atlas + Benchmark Foundry Implementation Plan

> **Contrat :** ce document est un plan maître. Il fixe l’ordre, les interfaces, les gates et les preuves. Il n’autorise aucune écriture produit sans un paquet d’exécution frais contenant le commit de base, les chemins exacts, le test RED, les commandes, le rollback et les reviewers.

## 1. Résultat recherché

Construire une Foundry d’évaluation souveraine capable de :

1. valider une tâche GitSpace versionnée;
2. préparer un monde de test reproductible;
3. exécuter un agent remplaçable dans une capability limitée;
4. collecter un journal append-only et des artefacts adressés par contenu;
5. évaluer des oracles hors du workspace agent;
6. produire un verdict multidimensionnel non compensable;
7. rejouer et rescoring sans rappeler le modèle;
8. comparer plusieurs harness sans perdre la sémantique GitSpace;
9. qualifier 32 tâches natives;
10. produire des décisions expérimentales pour la Phase 01.

Le produit GitSpace n’est pas le livrable de la Phase 00. La Foundry est l’instrument scientifique qui déterminera quelles hypothèses produit méritent d’être adoptées.

## 2. Architecture d’implémentation

```text
Evaluation IR GitSpace
        │
        ├── Validator + Canonical JSON
        ├── CAS + Event Journal
        ├── Foundry Core + Verdict Engine
        ├── Native Runner + Oracle Boundary
        ├── CLI + Replay
        └── Adapter Protocol
              ├── Inspect
              ├── Harbor / Terminal-Bench
              ├── SWE-bench
              └── AgentDojo
```

### Frontière de langage

- **Rust :** contrats d’autorité, types IR, canonicalisation, digests, CAS, journal, état, verdicts, runner natif et CLI.
- **Python :** adaptateurs externes et analyses scientifiques lorsque l’écosystème le justifie.
- **Échange :** JSON canonique versionné et événements JSONL; aucune structure Python interne ne devient canonique.

### Structure cible indicative

```text
Cargo.toml
rust-toolchain.toml
pyproject.toml
toolchains.lock.json
crates/
  gs-canonical-json/
  gs-eval-ir/
  gs-cas/
  gs-foundry-core/
  gs-verdict/
  gs-foundry-cli/
python/gs_eval_adapters/
schemas/v1/
research/atlas/
evals/seed/
evals/fixtures/
evals/oracles/
experiments/
analysis/
tests/contracts/
tests/integration/
tests/replay/
```

Cette arborescence reste indicative jusqu’à la packetisation de Task 1. L’exécuteur ne crée pas de dossier uniquement parce qu’il apparaît ici.

## 3. Invariants globaux

- Architecture C et ADR-0009 sont canoniques.
- Faux `DONE = 0`.
- Aucun harness externe n’est source de vérité.
- Aucun verdict critique ne dépend uniquement d’un LLM.
- Sécurité, autorité, intégrité, portée et nettoyage sont non compensables.
- Les oracles protégés vivent hors du workspace agent.
- Toute version externe utilisée est verrouillée par version, commit ou digest.
- Toute nouvelle fonction comportementale suit RED → GREEN → REFACTOR → VERIFY.
- L’implémenteur ne ferme pas seul sa tâche.
- Un Evidence Bundle lie le commit, l’environnement, les commandes et les résultats.
- Une tâche invalide devient `TASK_INVALID`, pas un échec artificiel de l’agent.
- La prochaine tâche dépendante n’est packetisée qu’après verdict frais.

## 4. Interfaces M0 à préserver

```rust
pub fn validate_task_json(value: &serde_json::Value) -> Result<(), ValidationReport>;
pub fn canonical_bytes(value: &serde_json::Value) -> Result<Vec<u8>, CanonicalJsonError>;
pub fn sha256_digest(bytes: &[u8]) -> Digest;

pub trait Cas {
    fn put(&self, bytes: &[u8]) -> Result<Digest, CasError>;
    fn get(&self, digest: &Digest) -> Result<Vec<u8>, CasError>;
}

pub trait EventSink {
    fn append(&self, event: &RunEvent) -> Result<EventOffset, EventError>;
}

pub trait OracleRunner {
    fn evaluate(&self, run: &PreparedRun) -> Result<OracleResult, OracleError>;
}

pub fn issue_verdict(input: VerdictInput) -> Result<EvalVerdict, VerdictError>;
```

Les noms pourront changer uniquement par révision du plan et migration explicite des consommateurs.

## 5. Packetisation obligatoire

Chaque unité reçoit un paquet conforme à `GS-EXEC-PACKET-001` :

```yaml
task_id:
packet_version:
base_repository:
base_commit:
goal:
non_scope:
applicable_decisions:
risk_tier:
allowed_paths:
forbidden_paths:
read_only_paths:
required_interfaces:
produced_interfaces:
preconditions:
test_first:
  command:
  expected_failure:
implementation_constraints:
verification_commands:
expected_results:
evidence_bundle:
rollback:
review_sequence:
termination_conditions:
```

Aucune des 22 unités ci-dessous n’est exécutable à partir de ce document seul.

---

# Milestone M0 — Vertical slice natif

## Task 1 — Qualifier les toolchains et bootstrapper le monorepo

**But :** établir un workspace vide et reproductible, sans code produit ni adaptateur.

**Produit :**

- lock exact Rust/Python;
- manifests cohérents avec ce lock;
- dossier de qualification officiel;
- contrat automatique empêchant les plages flottantes;
- ignore rules empêchant caches, bytecode et artefacts de build.

**Dépend de :** ADR-0002, TDR-P00-001-AMENDED, RES-P00-028/029/031/032.

**Test RED minimal :** le contrat échoue parce que `toolchains.lock.json` et les manifests exacts n’existent pas.

**Gate :**

- sources officielles revalidées le jour du paquet;
- compatibilité Inspect/Harbor vérifiée;
- `cargo metadata` passe;
- aucun package applicatif;
- workspace propre;
- revue indépendante du dossier de qualification.

**Non-scope :** Eval IR, CAS, runner, adaptateur, benchmark.

## Task 2 — Définir les schémas Evaluation IR v1

**But :** rendre les contrats machine-checkable avant les types d’implémentation.

**Produit :** huit schémas Draft 2020-12 : `EvalTaskSpec`, `WorldFixture`, `OracleBundle`, `AgentConfiguration`, `EvalRunManifest`, `RunEvent`, `EvidenceBundle`, `EvalVerdict`.

**Tests :** exemples valides et contrôles négatifs pour ID, version, digest, propriété inconnue et verdict contradictoire.

**Gate :**

- `additionalProperties: false` dans le noyau;
- extensions uniquement namespacées;
- digests `sha256:` stricts;
- un contrôle négatif échoue pour chaque invariant;
- revue de cohérence avec GS-P00-SPEC-001.

## Task 3 — Canonical JSON et digests

**But :** obtenir des octets et identités stables indépendamment de l’ordre des clés.

**Produit :** canonicalisation conforme à RFC 8785 ou équivalent qualifié, type `Digest`, SHA-256 et tests de conformité.

**Tests :** clés réordonnées, nombres, Unicode, NaN/Infinity, round-trip et vecteurs officiels.

**Gate :** deux représentations sémantiquement identiques ont les mêmes octets et digest; aucune simple sérialisation `serde_json` n’est acceptée comme canonicalisation.

## Task 4 — Validation Rust de l’IR

**But :** fournir types v1 et validation structurée dans la couche d’autorité.

**Produit :** types Rust, `validate_task_json`, `ValidationReport`, parité avec les exemples des schémas.

**Tests :** corpus commun Python/Rust; mêmes acceptations et rejets; erreurs portant chemin, code et message stable.

**Gate :** zéro divergence inexpliquée entre schéma et types.

## Task 5 — CAS local immuable

**But :** stocker tout artefact par contenu avant d’introduire une base distribuée.

**Produit :** `Cas` filesystem, écriture atomique, vérification à lecture, collision/refus d’altération et layout documenté.

**Tests :** put/get, déduplication, corruption injectée, concurrence, interruption d’écriture et permissions.

**Gate :** une corruption produit une erreur déterministe; aucun overwrite silencieux.

## Task 6 — Journal append-only et projections

**But :** séparer l’historique autoritaire des vues reconstruisibles.

**Produit :** `RunEvent`, `EventSink`, offsets monotones, snapshots optionnels et rebuild d’une projection de run.

**Tests :** append, crash entre écritures, événement tronqué, ordre, replay et reconstruction depuis zéro.

**Gate :** suppression de toutes les projections puis reconstruction identique depuis journal + CAS.

## Task 7 — Verdict engine non compensable

**But :** empêcher qu’une moyenne masque une violation critique.

**Produit :** `VerdictInput`, `EvalVerdict`, règles `false_done`, `safe_success`, obligation coverage et gates critiques.

**Tests :** matrice exhaustive des contradictions : succès fonctionnel avec violation de portée, autorité, sécurité, intégrité ou nettoyage.

**Gate :** aucune combinaison interdite n’émet `safe_success=true`.

## Task 8 — Runner local et isolation d’oracle

**But :** exécuter une fixture locale avec séparation entre workspace agent et oracle protégé.

**Produit :** préparation de run, capability locale minimale, dossier agent, dossier oracle hors portée et collecte d’effets.

**Tests :** lecture/écriture autorisée, accès oracle refusé, tentative de modification de tests, timeout et nettoyage.

**Gate :** l’agent évalué ne peut ni lire ni modifier l’oracle protégé.

## Task 9 — Vertical slice CLI et replay

**But :** fermer le premier chemin `validate → prepare → run → oracle → verdict → replay`.

**Produit :** CLI minimale et fixture native déterministe.

**Tests :** scénario PASS, FAIL, TIMEOUT, POLICY et INFRA; rescoring depuis artefacts sans modèle.

**Gate M0 :**

- un run propre produit journal, CAS, verdict et Evidence Bundle;
- le replay recalcule le même verdict;
- le second replay est bit-stable lorsque les timestamps sont exclus du noyau canonique;
- une revue indépendante reproduit le chemin.

---

# Milestone M1 — Adaptateurs, Atlas et oracles

## Task 10 — SDK Python d’adaptateur

**But :** empêcher chaque framework externe de contaminer l’IR.

**Produit :** protocole Python, conversion entrée/sortie, extensions namespacées, erreurs normalisées et fixtures contractuelles.

**Tests :** adaptateur factice PASS/FAIL/TIMEOUT/POLICY/INFRA, champs inconnus et perte sémantique détectée.

**Gate :** aucune classe Python externe ne traverse la frontière canonique.

## Task 11 — Adaptateur Inspect

**But :** importer et exécuter un sous-ensemble Inspect derrière le SDK.

**Produit :** mapping task/solver/scorer/log vers IR GitSpace et dossier de qualification par version verrouillée.

**Tests :** fixture sans modèle, un run contrôlé, événements, artefacts et rescore.

**Gate :** mêmes obligations et verdicts après replay hors Inspect.

## Task 12 — Adaptateur Harbor / Terminal-Bench

**But :** qualifier une famille de tâches terminal conteneurisées.

**Produit :** mapping Harbor, environnement, timeout, artefacts, test oracle et classification infra.

**Tests :** fixture minimale pour cinq statuts et une tâche Terminal-Bench verrouillée.

**Gate :** les erreurs d’infrastructure ne sont jamais comptées comme échec agent.

## Task 13 — Adaptateurs SWE-bench et AgentDojo

**But :** couvrir à la fois réparation de dépôt et sécurité d’agent outillé.

**Produit :** deux adaptateurs séparés partageant seulement le SDK.

**Tests :** un cas local de patch/repository et un cas d’injection/capability, sans téléchargement implicite pendant le test.

**Gate :** les dimensions sécurité et fonctionnelles restent distinctes et non compensables.

## Task 14 — Research Atlas exécutable

**But :** transformer l’Atlas Markdown en registre versionné et validable.

**Produit :** schéma `ResearchClaim`, registre JSON/YAML, validation des statuts, fraîcheur et références d’expérience.

**Tests :** préprint marqué `ADOPT`, source sans date, claim sans limites, ID dupliqué et source mouvante non verrouillée.

**Gate :** tout préprint non reproduit est plafonné à `PILOT`; chaque technique possède une expérience GitSpace.

## Task 15 — Générateur et durcisseur d’oracles

**But :** traiter les vérificateurs comme une surface attaquable.

**Produit :** template de tâche, contrôles `valid`, `invalid`, `partial`, `exploit`, mutation et procédure Hacker/Fixer/LegitimateSolver.

**Tests :** un oracle volontairement faible doit être exploité puis durci sans rejeter la solution légitime.

**Gate M1 :** trois familles externes mappées, Atlas validé et protocole d’oracle démontré.

---

# Milestone M2 — Seed Suite native

## Task 16 — Repair/Evolution et Creation (`GS-SEED-0001..0008`)

**But :** huit tâches couvrant réparation, évolution multi-fichiers et création de dépôt.

**Produit par tâche :** `task.yaml`, public fixture, oracle protégé, contrôles, solution de référence et dossier QA.

**Gate :** 8 solutions de référence PASS; tous les contrôles invalides/partiels/exploits non PASS; QA par reviewer n’ayant pas vu la solution.

## Task 17 — Intent/Abstention et Proof Integrity (`GS-SEED-0009..0016`)

**But :** mesurer non-action correcte, clarification, portée et faux succès.

**Contrôles :** action bias, modification inutile, hardcoding, test visible trompeur, oracle modifié et déclaration de succès prématurée.

**Gate :** les verdicts attendus `ABSTAINED` ou `BLOCKED` sont distingués d’un échec; tout succès sans obligation cachée produit `false_done=true`.

## Task 18 — Recovery et Memory (`GS-SEED-0017..0024`)

**But :** mesurer reprise, contexte frais, mémoire utile, mémoire périmée, révocation et poison.

**Produit :** interruption schedules liés à des événements, matrices ingestion→retrieval→utilization→action→outcome et contrôles MemoryGraft/MemMorph adaptés.

**Gate :** six replays déterministes sans modèle; aucune mémoire `STALE` ou `REVOKED` ne justifie une action sensible.

## Task 19 — Security et Owner Outcome (`GS-SEED-0025..0032`)

**But :** mesurer injection, exfiltration, capability escalation, side tasks et expérience du propriétaire.

**Produit :** quatre tâches sécurité et quatre scénarios Outcome Studio, protocole de consentement/privacité et mesures de charge de correction.

**Gate :**

- effets malveillants observés extérieurement;
- agents honnêtes conservent une utilité mesurée;
- aucune question de framework au propriétaire;
- absence de participant réel produit `BLOCKED_WITH_EVIDENCE`, jamais une simulation présentée comme preuve.

**Gate M2 :** 32 tâches versionnées, QA indépendantes, contrôles positifs/négatifs et absence de fuite d’oracle.

---

# Milestone M3 — Baselines et portabilité

## Task 20 — Baseline Matrix et analyse statistique

**But :** séparer modèle, harness, outils, contexte, mémoire, politique et budget.

**Produit :** plan factoriel préenregistré, analyse appariée, intervalles, rapports par tâche et coût par obligation prouvée.

**Tests :** jeux synthétiques à effet connu, infra failures, données manquantes et impossibilité d’agréger les gates critiques.

**Gate :** hypothèses et seuils hashés avant les runs de qualification.

## Task 21 — Qualification des harness externes

**But :** comparer au moins trois familles à travers le même IR.

**Produit :** matrice PASS/FAIL/TIMEOUT/POLICY/INFRA, manifeste complet, limitations et verdict `QUALIFIED`, `PARTIALLY_VERIFIED` ou `REJECTED`.

**Gate M3 :** verdict recalculable depuis artefacts sans rappeler le modèle; aucune perte d’un champ central de l’IR.

---

# Milestone M4 — Campagne scientifique

## Task 22 — Campagne Phase 00 et rapport final

**But :** exécuter la campagne préenregistrée, rechercher les contre-exemples et produire les décisions de Phase 01.

**Séquence :**

1. smoke de toutes les tâches et contrôles;
2. pilots à trois runs par cellule sélectionnée;
3. qualification à six runs par cellule principale;
4. campagnes sécurité avec répétitions adaptées au calcul d’ASR;
5. analyse des faux DONE, violations, divergences de replay et tâches invalides;
6. revue indépendante d’un sous-ensemble de chaque famille;
7. mise à jour du Research Atlas, des ADR/TDR, des risques et du RAGLite.

**Gate M4 :** les quinze critères de sortie de GS-P00-SPEC-001 sont tous fermés par preuve fraîche. Sinon la Phase 00 reste `PARTIALLY_VERIFIED`, `RESEARCH_MODE` ou `BLOCKED_WITH_EVIDENCE`.

---

## 6. Graphe de dépendances

```text
Task 1
  └─ Task 2
      ├─ Task 3
      │   ├─ Task 4
      │   ├─ Task 5
      │   └─ Task 6
      └──────────┬─ Task 7
                 └─ Task 8
                      └─ Task 9  [M0]
                           ├─ Task 10
                           │   ├─ Task 11
                           │   ├─ Task 12
                           │   └─ Task 13
                           ├─ Task 14
                           └─ Task 15  [M1]
                                ├─ Task 16
                                ├─ Task 17
                                ├─ Task 18
                                └─ Task 19  [M2]
                                     └─ Task 20
                                          └─ Task 21  [M3]
                                               └─ Task 22  [M4]
```

Une tâche peut commencer en parallèle uniquement lorsque ses interfaces consommées sont acceptées et que les surfaces d’écriture ne se chevauchent pas.

## 7. Evidence Bundle commun

```text
.gitspace/evidence/P00-TASK-NNN/
├── task.json
├── environment.json
├── commands.jsonl
├── stdout.log
├── stderr.log
├── test-results/
├── artifacts.sha256
├── diff-summary.json
├── commit.json
├── post-commit-verification.json
├── reviews/
└── terminal-result.json
```

Le bundle brut n’est pas inclus dans le commit qu’il atteste. Son mécanisme de conservation est fixé par le paquet jusqu’à disponibilité du CAS.

## 8. Séquence de revue

1. **Conformité :** contrat, canon, portée et interfaces.
2. **Technique :** comportement, tests, erreurs, qualité et maintenabilité.
3. **Sécurité/autorité :** pour toute frontière de confiance.
4. **Preuve :** provenance, hashes, commandes, replay et circularité.

Un reviewer n’est pas exposé d’abord à la conclusion de l’implémenteur.

## 9. Critères de rejet d’une unité

Une unité est `TASK_INVALID` lorsque :

- la spécification est contradictoire;
- le test RED ne peut pas échouer pour la raison attendue;
- l’oracle accepte une solution invalide;
- les chemins permis sont insuffisants ou excessifs;
- une dépendance indispensable n’est pas déclarée;
- le résultat attendu ne peut pas être observé;
- le rollback est impossible malgré un risque non accepté.

Elle est `BLOCKED_WITH_EVIDENCE` lorsque la tâche est valide mais l’environnement ou une décision externe manque.

## 10. Handoff de départ

Après merge du bootstrap documentaire :

1. ChatGPT lit le commit canonique accepté;
2. revalide les sources officielles de toolchain;
3. produit `P00-TASK-001` avec `base_commit` exact;
4. un exécuteur remplaçable réalise uniquement Task 1 dans un workspace isolé;
5. les reviewers contrôlent le commit et l’Evidence Bundle;
6. Task 2 est packetisée seulement depuis l’état accepté.

Aucun adaptateur, schéma produit ou benchmark ne doit être créé avant ce handoff.

## 11. Auto-revue

- **Couverture :** IR, canonicalisation, CAS, journal, verdict, isolation, replay, adaptateurs, Atlas, oracles, 32 tâches, statistiques et closeout sont couverts.
- **Neutralité :** aucun fournisseur d’agent n’est imposé.
- **Granularité :** chaque unité possède un résultat rejetable indépendamment.
- **Type consistency :** les interfaces M0 correspondent à la spécification.
- **Preuve :** chaque milestone possède un gate observable.
- **Limite actuelle :** aucun code ou test runtime n’a encore été exécuté; statut `DOCUMENT_REVIEWED_NOT_EXECUTED`.
