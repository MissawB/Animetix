# Design Spec: Training Database Improvements (SFT Dataset)

Cette spécification détaille les améliorations à apporter à la pipeline de génération du jeu de données de fine-tuning (`finetuning_dataset.py`) pour augmenter sa qualité, sa performance, et sa résilience.

## 1. Objectifs
- **Performance & Économie :** Éviter les appels d'API redondants à Gemini en mettant en place un système de cache local persistant.
- **Qualité des Textes :** Éliminer le bruit textuel (balises HTML, entités HTML, espaces doubles) des descriptions brutes.
- **Flexibilité :** Permettre le paramétrage dynamique des ratios de composition du jeu de données (Spécialisé, Méta, Général).
- **Résilience MCP :** Entraîner le modèle expert à réagir intelligemment en cas de panne ou d'erreur des outils MCP.

## 2. Conception Détaillée

### A. Système de Cache Persistant pour Gemini
- **Fichier de cache :** `data/mlops/datasets/gemini_paraphrase_cache.json`
- **Structure :**
  ```json
  {
    "paraphrases": {
      "hash_du_texte_original_et_style": "texte_paraphrase"
    }
  }
  ```
- **Clé de cache unique :** `f"{text_brut}||{style_type}"` ou son hash MD5.
- **Fonctionnement :**
  1. Charger le cache au démarrage de `finetuning_dataset.py`.
  2. Avant d'appeler l'API Gemini, vérifier si la clé existe dans le cache.
  3. Si présente, retourner immédiatement la valeur mise en cache.
  4. Si absente, faire l'appel API, stocker le résultat dans le cache, et appliquer un petit délai.
  5. Enregistrer le cache sur disque à la fin de l'exécution (bloc `finally`).

### B. Nettoyage et Normalisation Textuelle
- **Module `html` :** Utiliser `html.unescape()` pour convertir les entités HTML (ex: `&quot;` -> `"`, `&amp;` -> `&`, `&#039;` -> `'`).
- **Expressions Régulières (Regex) :**
  - Supprimer les balises HTML : `<br\s*/?>`, `</?[a-zA-Z]+(?:\s+[^>]*)?>` (ce qui couvre les balises comme `<i>`, `</i>`, `<b>`, `</p>`, etc.).
  - Nettoyer les espaces doubles ou multiples : `re.sub(r'\s+', ' ', text)`.
- **Intégration :** Encapsuler ce nettoyage dans une fonction utilitaire `clean_description(text)` appelée sur toutes les descriptions brutes lues depuis les fichiers JSON (`clean_root_animes.json`, `clean_root_mangas.json`, etc.).

### C. Diversification et Ratios Configurables
- **Lecture d'environnement :**
  ```python
  RATIO_SPECIALIZED = float(os.getenv("ANIMETIX_RATIO_SPECIALIZED", "80.0"))
  RATIO_META = float(os.getenv("ANIMETIX_RATIO_META", "5.0"))
  RATIO_GENERAL = float(os.getenv("ANIMETIX_RATIO_GENERAL", "15.0"))
  ```
- **Calcul dynamique :**
  - La somme des ratios doit être validée (normalisée à 100%).
  - Calculer la taille des sous-jeux de données en fonction du nombre total généré pour la partie spécialisée.

### D. Résilience des Scénarios d'Appels d'Outils (MCP)
- **Extension de `generate_mcp_tool_instructions()` :**
  - Ajouter des exemples d'appels d'outils Jikan/Spotify retournant des erreurs structurées :
    ```json
    {
      "status": "error",
      "code": 429,
      "message": "Rate limit exceeded"
    }
    ```
    ou
    ```json
    {
      "status": "error",
      "code": 503,
      "message": "Service Unavailable"
    }
    ```
  - **Comportement attendu du modèle expert (output) :**
    Le modèle doit s'excuser poliment de l'indisponibilité technique, expliquer l'erreur de façon claire, puis fournir une réponse alternative basée sur ses connaissances internes pré-entraînées.

## 3. Plan de Vérification
- **Tests unitaires de compilation :** Valider que les modifications ne cassent pas la syntaxe.
- **Test unitaire de nettoyage :** Vérifier que les balises HTML et entités sont correctement converties/supprimées.
- **Test du cache :** Vérifier que le cache est chargé, lu, écrit et que les appels réseau ne sont pas déclenchés si le cache contient la clé.
