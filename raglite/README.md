# GitSpace RAGLite

RAGLite est la projection cinq fichiers du canon GitSpace destinée au Projet ChatGPT mobile. Il ne constitue jamais un second canon.

## Principe

La projection est une **copie byte-for-byte** des cinq documents routés :

```text
00_GITSPACE_START_HERE.md
01_GITSPACE_MASTER_CANON.md
02_GITSPACE_NOW_DECISIONS_ROADMAP.md
03_GITSPACE_RESEARCH_ATLAS.md
04_GITSPACE_AGENT_PROTOCOL.md
```

La génération préfère la réutilisation directe du blob Git source. Elle ne résume, ne reformule et ne corrige aucun contenu.

## Paire canon/projection

```text
commit canonique X
→ commit projection Y
manifest.source_commit = X
```

Le bootstrap initial utilise :

- A : corpus initial;
- B : projection de A;
- C : clôture d’état après ouverture de la PR;
- D : projection finale de C.

Cette deuxième paire évite que le RAGLite final conserve l’ancien état « transport bloqué » après une publication réussie.

## Vérification déterministe

Pour chaque entrée de `projection_map` :

1. lire le blob source dans `source_commit`;
2. vérifier le SHA Git annoncé;
3. placer le même blob sous `raglite/mobile/`;
4. vérifier la taille et le SHA-256;
5. comparer le tree distant;
6. confirmer que le commit projection a `source_commit` pour parent.

Aucune synthèse LLM n’est utilisée.

## Remplacement dans le Projet ChatGPT

Après merge accepté seulement :

- supprimer les cinq anciennes sources;
- importer les cinq fichiers de `raglite/mobile/`;
- ne conserver qu’une version active;
- vérifier `source_commit` et les digests;
- lancer l’examen mémoire rapide;
- confirmer architecture C, Phase 00 et prochaine action.

Une PR ouverte ou un commit de branche ne suffit pas à promouvoir la projection vers le Projet ChatGPT.
