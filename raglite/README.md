# GitSpace RAGLite

RAGLite est la projection cinq fichiers du canon GitSpace destinée au Projet ChatGPT mobile. Il ne constitue jamais un second canon.

## Principe v0.3

La projection n’est plus un résumé réécrit par un modèle. Elle est une **copie byte-for-byte** des cinq documents routés du dépôt :

```text
00_GITSPACE_START_HERE.md
01_GITSPACE_MASTER_CANON.md
02_GITSPACE_NOW_DECISIONS_ROADMAP.md
03_GITSPACE_RESEARCH_ATLAS.md
04_GITSPACE_AGENT_PROTOCOL.md
```

Le nombre de fichiers reste faible, tandis que le contenu autoritaire reste identique. Cette règle supprime une classe entière de dérive entre résumé mobile et canon.

## Publication sans auto-référence

Un commit ne peut pas contenir son propre SHA stable. La publication utilise :

```text
commit A : documents canoniques complets
commit B : copies RAGLite + manifeste
manifest.source_commit = A
```

## Génération déterministe

Pour chaque entrée de `projection_map` :

1. checkout propre de `source_commit`;
2. copier les octets du fichier source vers `raglite/mobile/<même_nom>`;
3. vérifier que les SHA-256 source et projection sont identiques;
4. écrire le manifeste;
5. répéter dans un second répertoire;
6. comparer bit-à-bit.

Aucune synthèse LLM n’est utilisée dans cette étape.

## Remplacement dans le Projet ChatGPT

- supprimer les cinq anciennes sources;
- importer les cinq fichiers de `raglite/mobile/`;
- ne conserver qu’une version active;
- vérifier `source_commit` et les digests;
- lancer l’examen mémoire rapide.

## Statut du pack local

Le manifeste local est `PRECOMMIT_PREVIEW`. Après création du commit A réel, les copies et le manifeste doivent être régénérés avant le commit B.
