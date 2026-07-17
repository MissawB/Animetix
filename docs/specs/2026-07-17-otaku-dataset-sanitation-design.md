# Assainissement du dataset de fine-tuning otaku

**Date :** 2026-07-17
**Statut :** Design approuvé, prêt pour plan d'implémentation
**Périmètre :** Dataset uniquement (régénération + validation + upload). **Pas** de réentraînement (GPU bloqué : HF Jobs à court de crédits, quota GPU = 0).

## Contexte & problème

L'adaptateur `MissawB/otaku-qwen-7b-adapter`, une fois mergé dans sa vraie base et servi, produit du **texte corrompu** : chiffres injectés au milieu des mots, personnages inventés (« Izanagi Eikichi1 » comme héros de Chainsaw Man). Le modèle **stock** répond « Denji » proprement sur la même chaîne de service — donc la chaîne est saine, **c'est l'adaptateur**, et par extension le dataset `MissawB/otaku-expert-dataset` sur lequel il a été entraîné.

### Diagnostic (3 causes racines confirmées par lecture du code)

1. **Slots numériques non-conditionnés.** Chaque biographie de personnage se termine par la phrase *identique* :
   *« …se plaçant au rang numéro `{rank}` des personnages favoris avec pas moins de `{favs}` votes d'admiration. »*
   `{rank}` et `{favs}` ne sont **jamais dérivables de la question** (« Qui est Denji ? »). Le modèle apprend donc « émettre un nombre ici » sans ancrage → chiffres hallucinés injectés dans le texte.
   Source : [`profile_builders.py:200`](../../backend/pipeline/mlops/ft_dataset/profile_builders.py) (`make_french_character_bio`), et l'équivalent EN `make_english_character_bio:274`.

2. **Mémorisation de forme byte-identique.** Sans `GEMINI_API_KEY`, les 5 « variations » par entité populaire sont le *même texte de sortie* mappé sur 5 questions différentes (`p1 = p2 = p3 = p4 = p5 = profile`). Source : [`finetuning_dataset.py:476`](../../backend/pipeline/mlops/finetuning_dataset.py). Le modèle voit le même squelette des milliers de fois → reproduit « figure incontournable / jouit d'une immense popularité » par réflexe, indépendamment du contenu.

3. **Contenu réel absent.** Les bios/profils sont du remplissage générique (« incarne les valeurs et les conflits majeurs »), vrai de rien. Les vrais faits sont pourtant présents dans le source data et **ignorés** :
   - `data/processed/refined_characters.json` → champ `biography` (ex. Levi : « humanity's strongest soldier… »).
   - `data/processed/clean_root_animes.json` / `clean_root_mangas.json` → champ `description` (ex. Chainsaw Man : Denji, Pochita le chien-tronçonneuse, awards).

La config d'entraînement n'est **pas** en cause (1 époque, LR 2e-4, r=16 — raisonnable). C'est la donnée.

### Décisions de cadrage (validées avec l'utilisateur)

- **Ancrage déterministe, gratuit** : réécrire les générateurs pour utiliser le vrai texte source ; aucun appel LLM pour le volume. La variété vient gratuitement de l'unicité de chaque description.
- **Dataset uniquement** : régénérer + valider + re-upload. Réentraînement reporté (GPU bloqué).
- **FR structuré + EN synopsis complet** : le synopsis réel étant en anglais, les réponses **anglaises** l'intègrent en entier ; les réponses **françaises** rendent les faits *structurés* (titre, genre, studio, année, œuvre, organisation) en français, honnêtes et sans fabrication. Zéro hallucination des deux côtés.
- **Awards conservés** dans le texte EN (vrais faits) ; synopsis tronqués à ~1200 caractères.
- Générateurs annexes : **audit-et-patch-si-malade**, pas de réécriture systématique.

## Objectif

Régénérer `MissawB/otaku-expert-dataset` de sorte qu'un QLoRA SFT produise un adaptateur **factuellement ancré et non-templaté**, en éliminant les 3 causes racines — sans coût API et sans réentraîner dans ce périmètre.

## Non-objectifs

- Réentraînement / re-service de l'adaptateur (périmètre futur, GPU requis).
- Traduction des descriptions (exclut le synopsis FR — assumé).
- Réécriture des générateurs relationnels/méta déjà factuels (audit seulement).
- Modification des hyperparamètres d'entraînement.

## Conception détaillée

### Unité 1 — Constructeurs de profils/bios (`profile_builders.py`)

**Rôle :** transformer un enregistrement source (dict) en texte de réponse ancré.
**Interface :** signatures existantes conservées, plus l'accès au texte source réel.
**Principe :** le corps est dominé par du texte réel unique (EN) ou des faits structurés honnêtes (FR) ; habillage fixe minimal + choisi aléatoirement dans un large pool ; **seule l'année** subsiste comme nombre (ancrée, vérifiable).

- `make_english_anime_profile` / `make_english_manga_profile` :
  - Amorce variée (pool ≥ 8) : nom (+ synonymes) + type + année + genres réels.
  - Corps : `description` nettoyée (voir Unité 3).
  - Suppression des adjectifs-squelette universels (« landmark work », « brilliantly », « impressively », « highly recommended »).
  - Si `description` vide → repli sur réponse structurée-seule (comme le FR).
- `make_english_character_bio` :
  - Amorce : nom (+ synonymes) + œuvre d'origine.
  - Corps : `biography` nettoyée. Organisations depuis `entities.organizations`.
  - **Supprimés** : `rank`, `favs`, `height` (malformé dans la source).
- `make_french_anime_profile` / `make_french_manga_profile` :
  - Faits structurés en FR depuis un pool d'habillages variés : titre (+ synonymes), type, genres, studios (anime), année, tags-clés.
  - **Pas** de synopsis. **Pas** de superlatif universel (« chef-d'œuvre », « palpitant » — bannis ou fortement variés et non-systématiques).
- `make_french_character_bio` :
  - Nom (+ synonymes), œuvre d'origine (+ synonymes), organisations rendues en FR (mapping existant conservé).
  - **Pas** de synopsis, **pas** de rank/favs, **pas** de « figure incontournable ».

**Règle transverse anti-nombre :** aucune fonction ne doit émettre `rank`, `favs`, ni un compteur numérique non dérivable de la question. L'année (`year`) est la seule exception autorisée.

### Unité 2 — Boucle d'émission (`finetuning_dataset.py`)

**Rôle :** parcourir les bases et émettre les paires instruction/réponse.
**Changement :** remplacer le pattern « 5 sorties identiques » par :
- **1 réponse ancrée par (entité, langue)** pour la longue traîne.
- **Jusqu'à 3 pour le Tier-1**, chacune **projetant des faits différents** (bio-focus / genre-thème-focus / rôle-org-focus) — **jamais deux sorties identiques**.
- La variété des *formulations de question* est conservée (elle n'a jamais posé problème) ; c'est l'unicité des *sorties* qui est garantie.
- Le split FR/EN par parité d'index (`idx % 2`) est conservé.
- Les branches d'augmentation Gemini (`if client …`) restent en place mais inertes par défaut ; on ne s'appuie plus dessus pour la variété.
- Les ratios 80/5/15 (`calculate_dataset_counts`) se recalculent dynamiquement — la baisse de volume attendue est acceptée.

### Unité 3 — Nettoyage de texte source (`text_cleaning.py`)

**Rôle :** rendre `description`/`biography` propres et bornées.
**Nouvelle fonction** (ex. `clean_source_prose`) :
- Réparer/retirer le mojibake (`�` et séquences UTF-8 mal décodées).
- Strip HTML AniList (`<br>`, `<i>`, `<b>`, `<spoiler>`) et markup spoiler `~!…!~`.
- **Conserver** les mentions d'awards (vrais faits) en normalisant le formatage.
- Tronquer à ~1200 caractères sur une frontière de phrase.
- Chaîne vide / absente → renvoyer `""` (déclenche le repli structuré).

### Unité 4 — Suite de validation (`tests/mlops/test_finetuning_dataset_sanitation.py`, nouveau)

Sur un échantillon généré (source DBs réduites ou fixtures) :
1. **Phrases bannies absentes** : « jouit d'une immense popularité », « figure incontournable », « se plaçant au rang numéro », « incarne les valeurs et les conflits majeurs », « votes d'admiration », « avec pas moins de », + équivalents EN (« ranking at number », « votes of admiration », « no less than »).
2. **Zéro bruit numérique non-conditionné** : regex interdites `rang num[ée]ro \d+`, `\d+\s+votes`, `number \d+ of favorite`. (Année type « en 2019 » / « in 2019 » autorisée.)
3. **Aucune sortie identique** entre instructions distinctes d'une même entité ; ratio d'unicité global des sorties spécialisées ≥ seuil (ex. 0.95).
4. **Diversité de forme** : le 8-gramme de sortie le plus fréquent couvre < 5 % des sorties spécialisées.
5. **Ancrage** : le nom de l'entité apparaît dans la sortie ; pour l'EN avec `description` non vide, ≥ N tokens de contenu de la source réapparaissent dans la sortie.
6. `tests/mlops/test_finetuning_dataset.py` existant reste vert (attentes ajustées si nécessaire, sans affaiblir la couverture).

### Unité 5 — Audit des générateurs annexes

Vérifier (et patcher **seulement si malade** = slot numérique non-conditionné ou forme identique en masse) :
- `relation_generators.py` (transmedia, awards, songs/seiyuu, marché FR/JP, volumes/épisodes).
- `market_profile_generators.py` (profils doubleurs/éditeurs/diffuseurs).
- `otaku_generators.py` (méta-vocabulaire, créateurs, comparaisons).
- `dialogue_generators.py` (multi-turn), `synthetic_generators.py` (MCP, RAG, refus).

Attendu : la majorité est déjà factuelle ou porte du contenu écrit à la main → aucun changement. Documenter le verdict par générateur.

### Unité 6 — Régénération & upload

1. Exécuter `run_generate_instruction_dataset()` (augmentation OFF) → `data/mlops/datasets/animetix_expert_ft.jsonl`.
2. Contrôles post-génération : nombre de lignes, distribution des ratios, passage de la suite de validation sur le fichier réel.
3. `scripts/deploy/huggingface/hf_upload_dataset.py` → push vers `MissawB/otaku-expert-dataset`, vérif nombre de lignes + schéma.

## Plan de test

- Unitaire : Unités 1 & 3 (constructeurs et nettoyeur) via fixtures d'entrée réalistes (dont mojibake, HTML, description vide).
- Intégration : Unité 4 exécutée sur un mini-échantillon des vraies DBs.
- Bout-en-bout manuel : générer le JSONL complet, faire tourner la validation dessus, inspecter à l'œil ~20 exemples FR et EN (personnages + œuvres) avant upload.
- Régression : suite `tests/mlops/` existante verte.

## Risques & mitigations

- **Baisse de volume** (moins d'exemples par entité) → acceptée ; qualité > quantité. Ratios recalculés dynamiquement.
- **Nouveau squelette introduit par les amorces variées** → garde-fou n°4 (diversité 8-gramme) le détecte.
- **Descriptions bruitées non couvertes par le nettoyeur** → repli structuré-seul + inspection manuelle avant upload.
- **Non-vérifiable sans réentraînement** → hors périmètre assumé ; la validation prouve l'absence des motifs corrupteurs, pas la qualité du modèle final.

## Livrables

- `profile_builders.py`, `finetuning_dataset.py`, `text_cleaning.py` modifiés.
- `tests/mlops/test_finetuning_dataset_sanitation.py` nouveau.
- Verdict d'audit des générateurs annexes (dans le PR / commit).
- `animetix_expert_ft.jsonl` régénéré + poussé sur `MissawB/otaku-expert-dataset`.
