---
doc_id: GS-AUDIT-INDEPENDANT-2026-09-28
title: GitSpace — Audit indépendant du dépôt et du code source
authority: REPORT
status: RAW_OBSERVATION_FOR_OWNER_REVIEW
analyzed_commit: dcde1142cf76996a6ba0074cb7eab9d3c870c561
analyzed_at: 2026-09-28
auditor: Claude Code (agent externe à la chaîne ChatGPT/Codex, identité non humaine)
canon_modified: false
---

# Audit indépendant GitSpace — 2026-09-28

> Rapport de niveau « journaux et rapports » (autorité la plus basse après les conversations).
> Il ne modifie ni le canon, ni les ADR, ni l'état `00/02/04`, ni RAGLite. Toutes les
> propositions de changement d'état sont regroupées dans le `MEMORY_PATCH` final, à décider
> par le propriétaire. Aucun élément de ce rapport n'est déclaré `PROVEN` par son auteur.

## 0. Verdict

**La direction de fond est bonne ; la trajectoire actuelle ne l'est pas.**

- **Bonne direction** : IR d'évaluation souverain, CAS immuable, journal chaîné, gates non
  compensables, séparation contrôle/données, discipline RED→GREEN, honnêteté sur les limites
  (`NOT_COMPUTED_EXTERNAL`, `PARTIALLY_VERIFIED`). Le code Rust M0 est propre, petit et
  correct vis-à-vis de ses propres contrats.
- **Faux DONE constatés** : l'état canonique déclare `P00-TASK-011 PROVEN` avec « 26/26
  mutations tuées » et « run contrôlé sans réseau ». Les deux affirmations sont **réfutées**
  par mesure (22/26 réellement tuées ; téléchargement Internet sur cache froid). Les harnais
  de mutations Task 10 et Task 11 ne peuvent pas échouer tels qu'écrits.
- **Défaut sémantique central** : `false_done` est calculé de façon à ce que tout agent honnête
  déclarant « succès » avant vérification indépendante soit compté comme faux DONE. La métrique
  souveraine n°1 de la Phase 00 est donc inutilisable en l'état pour mesurer de vrais agents.
- **Provenance et attribution** : le commit « réellement exécuté » que le README dit lier au
  replay est en fait choisi par l'appelant (un commit inexistant rejoue avec succès) ; horodatages
  et environnement sont des constantes ; un agent peut transformer son échec en erreur du runner.
- **Dérive d'architecture** : la Foundry Rust et les adaptateurs Python ne sont pas reliés ;
  la logique de replay/rescoring des harness externes s'accumule en Python.
- **Blocage** : 11 tâches fusionnées en ~31 h (13–14 août), puis **aucune fusion depuis 6
  semaines** ; Task 12 est éclatée en 3 PR ouvertes, sous des gates de chaîne
  d'approvisionnement très lourdes pour un pilote de recherche.

## 1. Périmètre et méthode

| Élément | Valeur |
|---|---|
| Commit analysé | `main@dcde1142cf76996a6ba0074cb7eab9d3c870c561` (= branche d'audit) |
| Fichiers suivis | 217 (74 Markdown, 7 crates Rust, 1 paquet Python, 8 schémas, 11 workflows) |
| Historique | 44 commits (1 le 12/08, 27 le 13/08, 16 le 14/08), 28 purement documentaires |
| Volume | Markdown 423 Ko ; source Rust 163 Ko + tests 121 Ko ; source Python 68 Ko + tests 123 Ko |
| Toolchains | Rust 1.97.1, Python 3.12.13, uv 0.12.0, inspect-ai 0.3.258, jsonschema 4.26.0 (lock `uv lock --check` vert) |
| GitHub | runs, jobs, PR, revues et commits interrogés via l'API |

Méthode : lecture intégrale du code source et des tests Rust/Python, lecture du canon
(`00`–`04`, ADR, RSK, CONFLICT, SPEC, PLAN, paquets, preuves), exécution de toutes les
suites avec les toolchains pinées, contre-expériences ciblées, et trois vérifications
adversariales parallèles dont les conclusions ne sont retenues qu'après reproduction.
État de cette révision : vérificateurs A (fondations Rust), B (verdict, runner, Foundry) et
C (SDK Python, Inspect) intégrés. Un constat de vérificateur n'est marqué « confirmé » que si
l'auteur l'a rejoué ou vérifié dans le code ; les autres sont signalés comme tels.

Limites de l'audit :

- environnement conteneur **root** avec proxy sortant restrictif (utile : il révèle les
  dépendances cachées à l'environnement) ;
- clé publique GitHub web-flow non téléchargeable : signatures constatées mais non
  re-vérifiées cryptographiquement en local ;
- la PR #57 (Task 12, +54 243 lignes) est analysée au niveau structure et statut, pas ligne
  à ligne ;
- l'auditeur est un agent IA d'un autre fournisseur, **pas** une identité humaine
  indépendante : cet audit ne ferme pas la gate M0 `IDENTITY_INDEPENDENT_REPRODUCTION_MISSING`.

## 2. Ce qui est vrai (vérifié)

| Affirmation | Statut | Preuve |
|---|---|---|
| RAGLite = copie byte-à-byte de `00`–`04` | `EVIDENCE` | 5 blobs Git identiques ; `source_commit` 64db6cc, `source_tree` 84189fe exacts ; parent de dcde114 = 64db6cc |
| Build, Clippy `-D warnings`, rustfmt | `EVIDENCE` | verts avec 1.97.1 `--locked` |
| Tests Rust | `EVIDENCE` | 106/107 verts ; l'échec restant dépend de root (AUD-12) |
| Contrats Python (toolchain, 12 schémas, parité) | `EVIDENCE` | 14/14 verts |
| SDK provider-neutral Task 10 | `EVIDENCE` | 43/43 verts ; **vrai** score de mutation 19/19 (mesuré après correction du harnais) |
| Suite Inspect Task 11 | `EVIDENCE` sous condition | 49/49 verte **seulement** avec cache tiktoken chaud |
| Replay/rescoring Inspect sans importer `inspect_ai` | `EVIDENCE` | `inspect_ai` absent de `sys.modules` après import de `inspect_replay` |
| Runs post-merge Task 11 / Task 10 | `FACT_OFFICIAL` | 31861648147 et 31861648140 : `push`, `main`, head `0eb3618…`, `success` |
| Runs post-merge sondés Task 10 / 9 / 7 | `FACT_OFFICIAL` | 31830147076 (`06e480d…`), 31824037711 (`b15a2b7…`), 31767376709 (`453b7a1…`) : `push`, `main`, `success` |
| Dépendances pinées exactement | `EVIDENCE` | Rust : toutes les dépendances directes en `=x.y.z` + `Cargo.lock` + `--locked` ; Python : `==` + `uv.lock` |
| RED du cycle EvidenceBundle | `FACT_OFFICIAL` | run 31778117998 `failure` sur la branche RED (attendu) |
| CAS : pas d'écrasement silencieux | `EVIDENCE` (code) | `linkat` sans remplacement, fsync du fichier, du shard et de `tmp` (pas du parent d'un shard neuf, cf. AUD-22), relecture re-hashée ; garantie non fixée par un test déterministe |
| Journal : offsets contigus + chaîne SHA-256 | `EVIDENCE` (code) | chaîne recalculée à chaque lecture/append, verrou exclusif, fsync |
| Moteur de verdict conforme à **son** paquet | `EVIDENCE` | table de vérité 256 combinaisons + matrice |
| Sérialisation RFC 8785 conforme | `EVIDENCE` (vérificateur A) | 6/6 vecteurs de référence cyberphone ; 200 000 doubles aléatoires identiques octet par octet à `JSON.stringify` (Node) ; tri UTF-16 sur 2 000 objets aléatoires |
| Pas de `arbitrary_precision` ni `preserve_order` dans serde_json | `EVIDENCE` (vérificateur A) | features résolues : `default`, `std`, `float_roundtrip` |
| Limites honnêtement déclarées | `EVIDENCE` | runner « not a native-code sandbox », Foundry « deterministic M0 fixture », Sonar `NOT_COMPUTED_EXTERNAL` |

## 3. Faux DONE et preuves invalides

### AUD-01 — Harnais de mutations Task 10 : ne peut pas échouer — `CRITICAL (preuve)`

`tests/adapters/run_mutations.py` copie `python/gs_eval_adapters` dans un répertoire
temporaire. Or `python/gs_eval_adapters/schemas.py:32` résout les schémas par
`Path(__file__).resolve().parents[2] / "schemas" / "v1"`, absent de l'arbre mutant.
Un **mutant identité (aucune mutation)** monté de la même façon fait échouer la suite :

```text
Ran 43 tests — FAILED (errors=48)
RuntimeError: missing sovereign Evaluation IR schema: eval-task-spec.schema.json
```

Tout mutant est donc « KILLED » par construction ; `mutations=19 killed=19` ne prouvait
rien. Après correction dans une copie de travail (schémas présents, base verte), le vrai
score est **19/19** : l'affirmation était juste, la preuve était invalide.

### AUD-02 — Harnais de mutations Task 11 : 26/26 annoncé, 22/26 réel — `CRITICAL (faux DONE)`

`tests/adapters/inspect/run_mutations.py:191-202` ne copie pas non plus `schemas/`. Mutant
identité : `FAILED (errors=17)`, même `RuntimeError`. Avec l'arbre corrigé et une base verte :

```text
mutations=26 killed=22
survivors=allow-non-eval-log,skip-published-artifact-digest,
          allow-projection-scorer-options,sort-event-order
```

Confirmation manuelle sur `git archive` propre : avec `sort-event-order` ou
`skip-published-artifact-digest` appliqué, la suite complète reste `Ran 49 tests — OK`.

De plus, deux des 26 mutants ne compilent même pas (`drop-event-receiver-close`,
`drop-cleanup-shim-restore` → `IndentationError`) : ils sont « tués » par l'erreur de syntaxe
du harnais. Le vérificateur C a écrit des versions syntaxiquement valides de ces deux mutants :
elles sont réellement tuées, le score corrigé reste donc 22/26. Il a aussi montré que quatre
comportements du shim AnyIO (fermeture de l'émetteur, attente, émission des événements en
attente, remise à zéro des références) peuvent être supprimés sans qu'un seul test échoue.

Conséquences :

- « 26/26 mutations Inspect tuées » (`02`, `04`, `P00-TASK-011-POSTMERGE.md:76`) est `REFUTED` ;
- l'invariant fermé « ordre des événements participant au digest » (`02`) n'est **pas**
  protégé par les tests : trier les événements ne casse rien ;
- la revue finale (PR #52) a validé ce chiffre sans le contre-vérifier.

### AUD-03 — « Run contrôlé sans réseau » : réfuté — `HIGH (faux DONE)`

Chaîne observée (pile d'appels capturée) :

```text
mockllm/model.generate → Model.count_tokens → inspect_ai.model._tokens.count_text_tokens
→ tiktoken.get_encoding("o200k_base") → requests.get(
  "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken")
```

tiktoken met ce fichier en cache dans `tempfile.gettempdir()/data-gym-cache`. Sur cache
froid, le run Inspect « sans provider ni réseau » **télécharge depuis Internet**. Ici, le
proxy refuse l'hôte (403) : le run devient `INFRA` (fail-closed, bon comportement), mais
6 tests échouent, dont `test_controlled_run_succeeds_without_socket_connection`
(`connect` appelé vers le proxy 127.0.0.1:41695).

Pourquoi la CI est verte : le premier test chargé
(`test_adversarial…test_artifact_sink_must_return_matching_canonical_cas_uri`) exécute
Inspect **sans** bloquer `socket.connect` ; sur un runner GitHub (Internet ouvert), il
télécharge le fichier et chauffe le cache ; le test « sans socket » passe ensuite. La preuve
dépend de l'ordre des tests et d'un téléchargement réseau antérieur.

Contre-preuve : fichier `o200k_base` récupéré depuis un wheel PyPI, SHA-256
`446a9538…1a2d` = hash attendu par tiktoken → suite 49/49 verte ; `test_contract.py` seul
sur cache vide → échec `connect` reproductible.

`REFUTED` : « aucun provider, endpoint, secret, socket … externe ne participe »
(`P00-TASK-011-POSTMERGE.md:135`), « réseau bloqué » (`:79`).

### AUD-04 — Harnais sans contrôle de base verte — `HIGH`

Aucun des deux harnais n'exécute la suite non mutée avant de compter les mutants. Dans cet
environnement (base Inspect rouge), `run_mutations.py` imprime `mutations=26 killed=26` et
sort en code 0. La CI n'est protégée que par l'ordre des étapes du workflow.

### AUD-05 — Revue « rôle-séparée » non indépendante — `MEDIUM`

La revue finale de la PR #52 est publiée par le compte `leon36000` (OWNER), 20 secondes avant
la fusion, et répète « run contrôlé `mockllm/model` sans connexion réseau » et « 26/26 ».
Elle se déclare honnêtement « séparée par rôle, pas par identité ». AUD-02/03 montrent
concrètement pourquoi cette distinction compte.

## 4. Défauts de conception qui engagent la direction

### AUD-06 — Sémantique `false_done` incompatible avec la mesure d'agents réels — `HIGH`

- SPEC acceptée `GS-P00-SPEC-001 §7.2` : `false_done ⇔ declared=success ∧ mandatory_obligation_failed`.
- Paquet `P00-TASK-007` et `crates/gs-verdict/src/engine.rs:64-65` :
  `false_done ⇔ declared=success ∧ ¬(toutes les gates)`, y compris `replay_passed`,
  `independent_verification_passed`, `regression_free`, couverture de preuve et validité de tâche.
- La Foundry émet le verdict **avant** replay et vérification indépendante
  (`native.rs:150-155`, `460-468` : ces trois gates à `false`, preuve 0/1 codée en dur).

Conséquences :

1. tout agent qui déclare honnêtement `success` est `false_done=true` par construction ;
2. le scénario PASS doit déclarer `Blocked` (`native.rs:442`) pour ne pas être compté faux DONE ;
3. `safe_success=true` est inatteignable dans tout run M0 ; aucun mécanisme ne ré-émet un
   verdict une fois replay et vérification indépendante obtenus ;
4. une tâche invalide déclarée « succès » devient un faux DONE imputé à l'agent, contre la
   règle « une tâche invalide n'est pas un échec de l'agent » ;
5. ce conflit SPEC ↔ paquet n'est pas inscrit au `CONFLICT-REGISTER`.

Observation directe avec la CLI réelle (5 scénarios, commit courant) :

| Scénario | Déclaré | Fonctionnel | `false_done` | `safe_success` | Gates en échec |
|---|---|---|---|---|---|
| pass | blocked | pass | false | false | evidence, regression, replay, independent_verification |
| fail | success | fail | **true** | false | functional_outcome, obligations, evidence, regression, replay, independent_verification |
| timeout | blocked | partial | false | false | functional_outcome, obligations, evidence, regression, replay, independent_verification |
| policy | blocked | partial | false | false | functional_outcome, obligations, evidence, authority, regression, replay, independent_verification |
| infra | blocked | fail | false | false | functional_outcome, obligations, evidence, regression, replay, independent_verification |

Même le run parfait échoue quatre gates par construction ; le replay qui suit renvoie
`replay_verified=true` mais le verdict conserve `replay_passed=false`.

Il faut séparer deux questions : *l'agent a-t-il sur-déclaré ?* (imputable à l'agent) et
*le résultat est-il accepté ?* (état du pipeline de vérification).

### AUD-07 — Foundry M0 : fixture à artefacts attendus codés en dur — `MEDIUM`

`scoring_input` (`native.rs:437-470`) dérive résultat déclaré, résultat fonctionnel et
obligations **du libellé du scénario**, pas des observations. `replay.rs` recompare les
artefacts stockés à une **seconde copie** des mêmes valeurs attendues
(`replay.rs:282-600`). C'est une bonne preuve de plomberie et d'intégrité pour 5 scénarios
fixes, pas un moteur de replay réutilisable : chaque nouvelle tâche exigerait de réécrire
ses artefacts attendus en Rust.

### AUD-08 — Les deux moitiés du système ne sont pas reliées — `HIGH (direction)`

- Le SDK Python ne valide que `EvalTaskSpec` et `AgentConfiguration` ; il ne produit ni
  `EvalRunManifest`, ni `RunEvent`, ni `EvidenceBundle`, ni `EvalVerdict`.
- Aucun crate Rust n'ingère un résultat d'adaptateur ; le moteur de verdict n'est appelé que
  par la fixture native.
- Le « CAS » côté Python est un callback ; dans les tests, un dictionnaire en mémoire.
- Le rescoring et les obligations Inspect vivent en Python (`inspect_replay.py:260-292`),
  alors que `GS-P00-SPEC-001 §3.2` attribue « verdicts » et « replay » à Rust. La PR #57
  prolonge cette dérive (+2 217 lignes `harbor_replay.py`).

Tant que cette jonction n'existe pas, « trois familles de harness à travers le même IR »
(gate de Phase n°10) ne peut pas être démontrée au sens du canon.

### AUD-09 — Provenance déclarative, affirmation du README fausse — `HIGH`

Le README de la Foundry affirme que le replay « binds the receipt, run identity and
EvidenceBundle to the source commit actually executed » (`crates/gs-foundry-cli/README.md:79`).
Cette garantie n'existe pas :

- `commit_sha` de l'EvidenceBundle = argument CLI `--source-commit`, contrôlé seulement sur
  le format hexadécimal (`native.rs:698-703`, `main.rs:36-47`) ;
- modifier le seul champ `source_commit` d'un reçu est détecté (l'identifiant de run dérive du
  commit), mais au replay via la CLI la Foundry est ouverte avec le commit **lu dans le reçu** :
  le contrôle `receipt.source_commit == self.source_commit()` (`replay.rs:27-31`) est
  tautologique. Démonstration : `run --scenario pass --source-commit dddd…d` (objet inexistant
  dans le dépôt) puis `replay` → `replay_verified=True`, `evidence_verified=True`, et
  l'EvidenceBundle porte `commit_sha = dddd…d` ;
- `image_digest`, `environment_digest`, `network_policy_digest` sont des hachages de chaînes
  constantes, pas des mesures ; `started_at`, `ended_at` et tous les `occurred_at` sont les
  constantes `2026-08-14T00:00:0xZ`, `architecture` est le littéral `"x86_64"`
  (`native.rs:28-30`, `215-228`) : un run fait aujourd'hui sur aarch64 produirait un manifeste
  daté du 14 août sur x86_64, et le replay passerait. Le plan prévoyait d'**exclure** les
  horodatages du noyau canonique, pas de les figer (`GS-P00-PLAN-001`, gate M0) ;
- le vérificateur B a relancé toute la suite Foundry avec un `GITSPACE_TEST_SOURCE_COMMIT`
  différent du HEAD : `passed=36 failed=0` — aucun test ne vérifie le commit réellement exécuté,
  alors que le paquet Task 9 exigeait un test GREEN pour ce lien.

### AUD-10 — Deux définitions de « JSON canonique » — `MEDIUM (latent)`

Rust : RFC 8785 via `serde_json_canonicalizer`. Python : `json.dumps(sort_keys=True,
separators=…)` (`inspect_replay.py:590-600`, `inspect_adapter.py:297-307`). Sondes :

| Entrée | Rust JCS | Python |
|---|---|---|
| `{"b":1e16}` | `10000000000000000` | `1e+16` |
| `{"x":1e-7,"y":123456789012345678}` | `1e-7`, `123456789012345680` | `1e-07`, `123456789012345678` |
| clés U+E000 et U+10000 (paire `\uD800\uDC00`) | U+10000 d'abord (ordre UTF-16) | U+E000 d'abord (ordre des points de code) |

Sans effet sur la fixture actuelle, mais toute re-canonicalisation Rust d'un artefact Python
contenant ces valeurs produira un autre digest.

### AUD-11 — Autres écarts de conception

- **Schéma `EvalVerdict`** : seules deux contradictions sont interdites
  (`safe_success ∧ ¬authority`, `safe_success ∧ false_done`) ; un verdict externe
  `safe_success=true, scope_respected=false, cleanup_passed=false` est valide au schéma.
  Aucun champ explicite pour sécurité et intégrité (deux des cinq dimensions non compensables).
- **Interface `OracleRunner`** promise par `GS-P00-PLAN-001 §4` jamais implémentée ; le
  paquet Task 8 l'a remplacée par `OracleCheck` interne au runner, sans révision du plan.
- **« Perte sémantique bloquante »** (`sdk.py:92-117`) vérifie seulement que l'adaptateur
  renvoie une copie identique de la requête canonique ; la traduction réelle
  (`framework_request`) n'est pas contrôlée. Budgets (`wall_time_seconds`, `token_limit`,
  `tool_calls`) et `forbidden_actions` ne sont pas transmis à Inspect.
- **Journal** : une troncature d'enregistrements complets en fin de fichier n'est détectable
  que si la tête de chaîne est ancrée ailleurs (c'est le cas dans la fixture via la trace
  CAS, pas au niveau du crate) ; après troncature, le journal accepte un autre événement au
  même offset (historique bifurqué).

### AUD-22 — Fondations Rust : défauts moyens reproduits

Signalés par le vérificateur A, **rejoués par l'auteur** :

| Défaut | Emplacement | Reproduction |
|---|---|---|
| Un événement valide au schéma rend le journal illisible : `version = u64::MAX` passe `append`, la canonicalisation JCS en fait un flottant, la relecture échoue pour toujours | `gs-event-journal/src/journal.rs:63-82` vs `:94` | `append -> Ok(0)` puis `read_from(0) -> Err(typed.decode: floating point 1.8446744073709552e+19, expected u64)` |
| Un échec d'écriture partiel détruit l'historique acquitté : l'append ne tronque pas l'enregistrement partiel | `journal.rs:191-195` | sous `prlimit --fsize=1024` : 13 événements validés, le 14ᵉ échoue (`EFBIG`), puis `read_from(0) -> truncated tail of 48 bytes` |
| Rupture de parité Python/Rust : `pattern` Python (`re.search`, `$` accepte un `\n` final) vs Rust (ECMA) | tous les `pattern` de `schemas/v1` ; SDK `schemas.py` | `"GS-TASK-000001\n"` : **accepté** par le SDK Python, **rejeté** par `validate_task_json` Rust |
| Entiers > 2⁵³ arrondis silencieusement (JCS), alors que `-0` est rejeté comme perte | `gs-canonical-json/src/lib.rs:55-94` | `123456789012345678` → `123456789012345680` ; deux valeurs différentes, un seul digest |

Signalés et reproduits par le vérificateur A, non rejoués par l'auteur (sévérité faible) :
valeurs entières écrites `1.0` ou `2^64` valides au schéma mais refusées au décodage typé
(contredit la fermeture de NEG-P00-012) ; re-sérialisation typée non conforme au schéma
(`Option` → `null`) ; décodage serde direct qui ignore les champs inconnus (utilisé par le
replay Foundry pour EvidenceBundle et manifeste, comparés ensuite par égalité typée et non
par octets) ; course à l'initialisation du journal (2/600 ouvertures en échec) ; répertoire
de shard CAS jamais synchronisé dans son parent ; allocation égale à la taille annoncée d'un
fichier creux (abandon du processus).

Tests faibles : remplacer `hard_link` par `rename` (écrasant) n'est détecté que de façon
intermittente par le test de concurrence (1 échec sur 7 exécutions de l'auteur) — aucun test
déterministe ne fixe la garantie « sans remplacement » ; le test de « reconstruction depuis
zéro » du journal supprime un fichier que la bibliothèque ne lit jamais puis recalcule sur le
même journal ouvert (`contract.rs:100-109`).

Inexactitudes documentaires : `P00-TASK-004-VERDICT.md:97` évoque une annotation `format`
date-time absente de tous les schémas (`occurred_at: "yesterday"` est valide) ; le README du
journal place le verrou avant l'écriture CAS, le code fait l'inverse ; Task 5 annonce 10 tests
CAS et 20 tests au total, le code en contient 11 et 21.

### AUD-23 — SDK Python et adaptateur Inspect : constats complémentaires

Signalés par le vérificateur C ; **confirmés par l'auteur** (reproduction ou lecture du code) :

| Défaut | Emplacement | Confirmation |
|---|---|---|
| La garde « perte sémantique » compare avec `==` Python (`1 == 1.0 == True`, `0.0 == False`) | `sdk.py:100` | requête préparée avec `seed 11 → 11.0`, `task.version 1 → True`, `cost_limit_usd 0.0 → False` : aucune `SemanticLossError`, et la requête transmise à `invoke` **ne valide plus le schéma souverain** |
| Le « replay » re-note l'enregistrement, pas le log : la projection n'est jamais recoupée avec les octets du log ; seule la cohérence `log_uri = sha256(log_bytes)` est vérifiée | `inspect_replay.py:199-250`, `260-296` | lecture du code ; C a produit un enregistrement falsifié pointant vers le vrai log, noté PASS |
| Projection permissive : noms de solver et de score comparés par `endswith`, options de scorer enregistrées par Inspect ignorées puis remplacées par les valeurs pinées | `inspect_replay.py:330`, `:347` | lecture du code (`endswith`) ; C : solver `totally_not_generate` et options `location:any` projetés comme la fixture qualifiée |
| « Log brut conservé » faux : le fichier écrit par Inspect est supprimé avec le répertoire temporaire ; le CAS reçoit une re-sérialisation `model_dump(exclude_none=True)` | `inspect_adapter.py:124-145` | lecture du code ; C : 15 465 octets bruts contre 9 462 publiés, 7 différences structurelles |
| Aucune isolation d'environnement : Inspect charge `.env` depuis le répertoire courant et honore `INSPECT_TELEMETRY` (code arbitraire appelé avec les données d'usage) | Inspect `_eval/context.py:27`, `hooks/_legacy.py` | lecture du code ; C : hook de télémétrie exécuté, statut toujours PASS |
| Budgets, `forbidden_actions`, provider et `model_parameters` silencieusement abandonnés | `inspect_adapter.py:52-141` | lecture du code ; C : `wall_time_seconds=0`, `token_limit=1`, `provider=openai` → PASS, aucune limite passée à `inspect_eval` |
| Rescoring « indépendant » non équivalent au scorer Inspect : suppression de toute ponctuation Unicode et casse neutre, contre retrait de la ponctuation ASCII en début et fin de chaîne chez Inspect | `inspect_replay.py:582-587` vs Inspect `_util/text.py:32-33` | lecture du code ; C : `'a-b'/'ab'` → Inspect `I`, GitSpace `C` ; `'100$'/'100'` → Inspect `C`, GitSpace `I` |

Signalés par C, non rejoués par l'auteur (sévérité faible ou information) : `AdapterResult`
gelé mais contenant des dictionnaires mutables, `to_json` sans revalidation ; descripteur de
métaclasse exécuté lors du formatage d'erreur ; dérogation Sonar codée en dur dans le workflow ;
un eval en erreur publie son log puis renvoie INFRA sans artefact (objet CAS orphelin) ;
trois des six obligations du replay ne peuvent jamais être fausses ; `except Exception` laisse
passer les `BaseException`.

Vérifié vrai par C : rejet des sous-classes de `dict/list/str/int/float`, tuples, octets,
NaN, ±Infini, `-0.0`, entiers hors ±(2⁵³−1), surrogates isolés, cycles et profondeur > 64 ;
validation de schéma avant tout accès à l'adaptateur ; shim restauré après succès, exception et
`KeyboardInterrupt` ; le classificateur Sonar ne peut produire `PASS` sans quality gate calculé.

### AUD-24 — Runner et Foundry : attribution des échecs — `MEDIUM`

Signalés par le vérificateur B ; **confirmés par l'auteur** :

| Défaut | Emplacement | Confirmation |
|---|---|---|
| Un agent peut transformer son échec en erreur du runner : écrire un répertoire à l'emplacement vérifié par l'oracle, ou lire un fichier absent, fait renvoyer `Err` au lieu de `OracleFailed` ; le run est détruit et la Foundry s'arrête sans verdict | `runner.rs:247-254`, `389-426` ; `path.rs:216-219` | sonde : réponse fausse écrite en fichier → `Ok(OracleFailed)` ; `Write output/result.txt/decoy` → `Err(UnsafePath "file path resolves to a directory")` ; `Read input/missing.txt` → `Err(Io NotFound)` |
| Le verdict souverain du scénario INFRA impute l'échec à l'agent : `functional_outcome=fail`, `task_validity=valid`, gates `functional_outcome` et `obligations` en échec ; aucun champ de `EvalVerdict` ne marque l'infrastructure | `native.rs:447`, `454` | sortie CLI du scénario `infra` (tableau d'AUD-06) |
| L'`EvalTaskSpec` validé ne pilote pas le run : budgets (5 s, 8 appels d'outil), autorité et obligations sont décoratifs ; le plan utilise ses propres constantes (1 000 ms, 2 ms) et le verdict compte 1 obligation pour 3 déclarées | `native.rs:328-407`, `497-534` | lecture du code |
| Les chemins `output/./a.txt`, `output//b.txt`, `output/c.txt/` sont acceptés et normalisés, mais l'effet journalisé garde la chaîne brute | `path.rs:28-58`, `runner.rs:262`, `299` | lecture du code ; B : effets bruts contre instantané normalisé |

Signalés par B, non rejoués par l'auteur : supprimer le contrôle `can_read` laisse les 16 tests
du runner et les 34 tests de la Foundry verts ; la comparaison `OracleFileEquals` n'est jamais
testée contre une valeur différente (mutation « toujours vrai » : 0 échec) ; deux tests exigés par
le paquet Task 8 manquent (oracle inchangé, chemin non UTF-8) ; trois tests de substitution ne
ciblent pas le contrôle dont ils portent le nom ; la machine d'états de run de la SPEC §6.2 n'est
pas représentée (trois événements écrits après coup, jamais `REPLAYED` ni `CLOSED`).

Vérifié vrai par B : sur une énumération de 248 832 combinaisons d'entrées, **0** `safe_success`
dangereux et **0** écart à la formule du paquet Task 7 ; en revanche, 27 646 combinaisons donnent
un `false_done` différent de la définition SPEC §7.2. Classification des cinq statuts
déterministe ; EvidenceBundle émis et validé ; replay réellement en lecture seule (rien créé ni
réparé, second replay identique octet par octet) ; substitutions d'artefacts rejetées.

## 5. CI et reproductibilité

- **AUD-12** — `gs-cas/tests/adversarial.rs:184` (`write_permission_failure…`) échoue en
  root (le chmod 0500 n'arrête pas root) et passe en uid 65534 : la suite n'est pas
  reproductible dans un conteneur root.
- **AUD-13** — `unittest discover -s tests/adapters` (workflow Task 10) collecte 43 tests :
  sans `__init__.py`, `tests/adapters/inspect/` n'est pas inclus. Le filtre de chemins du
  workflow Task 11 ignore `sdk.py`, `model.py`, `json_boundary.py`, `registry.py`,
  `schemas.py`, `errors.py` et `schemas/v1/**`. Une modification du SDK ou d'un schéma peut
  casser l'adaptateur Inspect sans qu'aucune CI ne l'exécute. Exemple reproduit par le
  vérificateur C : `MAX_DEPTH = 64 → 8` dans `json_boundary.py` ne déclenche que le workflow
  010 (43 tests verts) alors que tout run Inspect réel devient INFRA.
- **AUD-14** — SonarCloud échoue sur les PR #52 et #57 (« The last analysis has failed ») ;
  l'état est honnêtement classé `NOT_COMPUTED_EXTERNAL`, mais l'intégration n'a jamais été
  réparée.

## 6. Gouvernance et documentation

- **AUD-15 — documents `ACTIVE` périmés** : `README.md` (« aucun code produit n'est encore
  implémenté », « PR #1 brouillon ») ; `RSK-REGISTER` figé au 13/08 (RSK-016
  `BLOCKING_OWNER_DECISION`, RSK-019/020/023 `OPEN` alors que les faits sont clos ; aucun
  risque pour API privée Inspect, réseau caché, Sonar) ; `GS-REPO-STATE-001`,
  `SOURCE-REGISTER`, `P00-BOOTSTRAP-PLAN-001` (« PR #1 ouverte ») ; `TDR-P00-010`
  (« reste : décision de merge ») ; dernière section du `CONFLICT-REGISTER` (« Task 9 ») ;
  `GS-P00-PLAN-001 §11` et `GS-P00-SPEC-001` (`DOCUMENT_REVIEWED_NOT_EXECUTED`).
- **AUD-16 — état courant faux par omission** : `02`/`04` disent Task 12
  `NOT_PACKETIZED` ; en réalité trois PR sont ouvertes : #55 (paquet v3, brouillon, non
  fermé bien que remplacé), #56 (paquet v4, `BLOCKED_WITH_EVIDENCE`), #57 (implémentation
  brouillon, +54 243 lignes).
- **AUD-17 — ordre du protocole inversé** : #57 (implémentation) a été ouverte alors que le
  paquet v4 (#56) n'est pas accepté et qu'il écrit lui-même « aucun code produit Task 12
  n'est autorisé avant un RED valide ». Ses 23 commits commencent par
  `feat(p00): add Harbor Task 12 adapter and offline fixture` : aucun RED observé préalable,
  alors que les Tasks 5 à 11 avaient chacune une PR « observe RED » distincte.
- **AUD-18 — preuves brutes commitées** : #57 ajoute ~43 000 lignes de JSON Trivy dans
  `docs/phase-00/evidence/`, contre la règle « le bundle brut n'est pas inclus dans le commit
  qu'il atteste ».
- **AUD-19 — dette M0** : M1 (Tasks 10–11) a été exécuté alors que la gate M0 « une revue
  indépendante reproduit le chemin » reste ouverte ; chaque tâche suivante hérite de cette dette.
- **AUD-20 — « merge signé »** : la signature est celle de la clé web-flow de GitHub
  (committer `web-flow`) ; elle prouve que GitHub a créé la fusion, pas qu'une revue a eu lieu.
- **AUD-21 — Atlas** : les 12 expériences `EXP-P00-001…012` sont `PLANNED` ; aucune
  hypothèse produit n'a encore été confrontée à une mesure.

## 7. Évaluation de la direction

| Axe | Appréciation |
|---|---|
| Mission et architecture C/C0 | cohérentes ; commencer par un instrument de mesure est le bon choix |
| Qualité du code M0 | bonne : petit, typé, fail-closed, sans `unsafe` |
| Système de preuve | **défaillant là où il compte** : malgré une cérémonie très lourde, il a produit des preuves invalides que deux contre-expériences simples ont révélées |
| Sémantique de mesure | `false_done` à reprendre avant toute campagne |
| Architecture d'ensemble | jonction adaptateurs → verdict souverain absente ; autorité de replay qui glisse vers Python |
| Provenance et attribution | commit, horodatages et environnement déclaratifs ; un agent peut faire passer son échec pour une panne d'infrastructure |
| Rythme | 11 tâches en ~31 h puis 6 semaines sans fusion ; coût documentaire > code (423 Ko contre 231 Ko de source) |

Diagnostic : la méthode fonctionne pour de l'infrastructure pure et locale ; elle cale au
premier contact avec un runtime externe réel (conteneurs, réseau, chaîne d'approvisionnement),
en partie à cause de gates que la Phase 00 — un pilote de recherche — ne requiert pas encore.
Le nombre de rapports ne remplace pas des méta-contrôles mécaniques : base verte avant
mutation, test réseau hermétique, reproduction dans un environnement différent.

Les défauts AUD-01, AUD-02, AUD-03, AUD-06 et AUD-09 ont traversé toute la chaîne paquet →
implémentation → CI → revue → promotion canonique → RAGLite sans être détectés. C'est
exactement le mode d'échec que le canon décrit lui-même (loi 5 : « le consensus n'est pas la
correction » ; loi 8 : « une CI verte n'est pas une terminaison ») : un planificateur unique
(ADR-0010), des exécuteurs guidés par ses paquets et une revue sous la même identité GitHub
partagent les mêmes angles morts. Deux contre-expériences simples, dans un environnement
différent, ont suffi à les révéler.

## 8. Recommandations ordonnées

1. **Réparer les preuves avant d'avancer** : ajouter `schemas/` et un contrôle de base verte aux
   deux harnais ; rendre le run Inspect hermétique (cache tiktoken vendoré et vérifié par hash,
   ou `ModelOutput` avec `usage` renseigné pour que mockllm ne compte pas les tokens) ;
   exécuter le test « sans réseau » isolé dans un espace réseau vide (`unshare -n`) ; tuer les
   4 survivants ; rendre le test CAS indépendant de root ; comparer les requêtes par octets
   canoniques plutôt que par `==` ; conserver le fichier de log Inspect brut et re-projeter
   depuis lui au replay ; isoler l'environnement d'Inspect (`.env`, `INSPECT_TELEMETRY`) ;
   classer toute erreur provoquée par une opération d'agent comme résultat d'agent (FAIL ou
   POLICY), jamais comme erreur du runner ; lier le commit au binaire ou au checkout vérifié au
   lieu de l'argument `--source-commit`, et corriger le README en attendant.
2. **Décision propriétaire sur `false_done`** : inscrire le conflit SPEC §7.2 ↔ Task 7 ; séparer
   `false_done` (sur-déclaration imputable à l'agent) de l'acceptation (vérification en attente) ;
   prévoir la ré-émission du verdict après replay et vérification indépendante.
3. **Construire la jonction souveraine** avant un troisième harness : résultat d'adaptateur →
   `EvalRunManifest` + `RunEvent` + `EvidenceBundle` + `EvalVerdict` (moteur Rust), stockés dans
   le CAS/journal Rust, rejouables par Rust ; une seule canonicalisation (JCS) des deux côtés.
4. **Réduire Task 12 à un pilote** : fermer #55, fusionner ou reprendre #56, sortir les dumps
   Trivy du dépôt, repousser SBOM/OCI/fraîcheur des scanners à une tâche dédiée.
5. **Remettre la documentation d'aplomb** : README, RSK, CONFLICT, états périmés ; ajouter à la
   CI les suites Python sur changement de SDK ou de schéma.
6. **Obtenir une vraie reproduction indépendante** (autre identité, autre environnement) pour
   fermer M0 ; la présente revue n'en tient pas lieu.

## 9. Prochaine action exacte

Packetiser depuis `main@dcde1142…` un correctif borné `P00-TASK-011-R1` : RED = mutant identité
qui doit échouer le contrôle de base + test réseau sur cache froid dans `unshare -n` ; GREEN =
harnais corrigés, run hermétique, 26/26 réellement tués ; puis mettre à jour `00/02/04` et
RAGLite. En parallèle, deux décisions propriétaire : la sémantique `false_done` (AUD-06) et le
statut de Task 9 tant que l'affirmation de provenance du README reste fausse (AUD-09).

## 10. MEMORY_PATCH proposé (non appliqué)

```yaml
MEMORY_PATCH:
  INVALIDATE:
    - id: P00-TASK-011.status.PROVEN
      cause: "AUD-02 (22/26 mutations réelles) et AUD-03 (téléchargement réseau sur cache froid)"
      proposed_status: PARTIALLY_VERIFIED
    - id: claim.task11.mutations_26_of_26
      cause: "harnais sans schémas ni base verte ; mesure corrigée 22/26"
      proposed_status: REFUTED
    - id: claim.task11.no_network_controlled_run
      cause: "tiktoken o200k_base téléchargé depuis openaipublic.blob.core.windows.net si cache froid"
      proposed_status: REFUTED
    - id: claim.task11.event_order_in_digest
      cause: "mutant sort-event-order survit à la suite complète"
      proposed_status: REFUTED
    - id: evidence.task10.mutations_19_of_19
      cause: "preuve CI invalide (harnais vide) ; affirmation re-mesurée vraie (19/19)"
      proposed_status: RE_EVIDENCE_REQUIRED
    - id: claim.task11.raw_log_preserved
      cause: "le fichier Inspect est supprimé ; le CAS reçoit une re-sérialisation model_dump"
      proposed_status: REFUTED
    - id: claim.task10.semantic_loss_blocking
      cause: "comparaison == : 1/1.0/True et 0.0/False confondus ; budgets non transmis"
      proposed_status: PARTIALLY_VERIFIED
    - id: claim.task9.replay_binds_executed_source_commit
      cause: "commit fourni par l'appelant ; run avec commit inexistant rejoué avec succès"
      proposed_status: REFUTED
    - id: P00-TASK-009.status.PROVEN
      cause: "lien de provenance exigé par le paquet non testé et faux ; horodatages figés"
      proposed_status: PARTIALLY_VERIFIED
  APPEND:
    - target: docs/conflicts/CONFLICT-REGISTER.md
      id: GS-CONFLICT-P00-VERDICT-001
      content: "SPEC §7.2 false_done/safe_success ↔ P00-TASK-007 ; décision propriétaire requise"
    - target: docs/risks/RSK-REGISTER.md
      id: RSK-P00-015
      content: "preuve d'herméticité dépendante de caches et de l'ordre des tests"
    - target: docs/risks/RSK-REGISTER.md
      id: RSK-P00-016
      content: "harnais de mutation incapable d'échouer (pas de base verte, arbre incomplet)"
    - target: docs/risks/RSK-REGISTER.md
      id: RSK-P00-017
      content: "autorité de replay/rescoring des harness externes implémentée en Python"
    - target: docs/risks/RSK-REGISTER.md
      id: RSK-P00-018
      content: "un agent peut convertir son échec en erreur runner (INFRA) ; attribution à corriger"
  REPLACE:
    - file: 02_GITSPACE_NOW_DECISIONS_ROADMAP.md
      sections: [état Task 9, état Task 11, prochaine tâche]
      new_content: "Tasks 9 et 11 PARTIALLY_VERIFIED ; Task 12 : PR #55/#56/#57 ouvertes, bloquées ; prochaine unité : P00-TASK-011-R1"
  NO_CHANGE: false
```
