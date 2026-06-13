# 📋 Plan d'Amélioration de la Base de Données d'Entraînement

> [!TIP]
> La liste complète des tâches du projet (Dette technique, Features, UI) se trouve dans [docs/TODO.md](docs/TODO.md).

Ce document recense les pistes d'amélioration identifiées pour perfectionner la qualité du modèle expert Animetix et renforcer l'alignement des préférences via DPO.

---

## 🧠 1. Amélioration de la Base SFT (Supervised Fine-Tuning)
Fichier cible : [finetuning_dataset.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/finetuning_dataset.py)

- [x] **Complexifier les dialogues multi-tours** :
  - [x] Intégrer des scénarios de recommandation progressive (l'utilisateur affine ses goûts au fil de la discussion).
  - [x] Ajouter des scénarios de demande de clarification en cas de requêtes trop ambiguës.
- [x] **Simuler des contextes RAG (Retrieval-Augmented Generation)** :
  - [x] Générer des exemples d'entraînement où le modèle doit s'appuyer strictement sur des fragments de contexte fournis (synopsis, fiches d'acteurs) pour répondre, en ignorant les données bruitées.
- [x] **Augmentation ciblée des données** :
  - [x] Renforcer la présence des genres sous-représentés (*Josei*, *Iyashikei*, *Slice of Life*).
  - [x] Diversifier les époques couvertes en ciblant spécifiquement les animes/mangas des années 70, 80 et 90.
- [ ] **Renforcer les cas de refus hors-domaine** :
  - [ ] Ajouter des exemples de questions complètement hors sujet (cuisine, programmation hors MCP, questions générales sans lien avec la culture otaku) pour apprendre au modèle à refuser poliment d'y répondre.

---

## ⚖️ 2. Amélioration de la Base DPO (Direct Preference Optimization)
Fichier cible : [dpo_dataset_compiler.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/dpo_dataset_compiler.py)

- [x] **Rendre les corruptions factuelles insidieuses** :
  - [x] Remplacer des entités par des concepts proches ou reliés plutôt que par des choix purement aléatoires (ex: échanger deux doubleurs du même anime, intervertir des studios de production du même genre d'œuvre).
- [x] **Subtiliser la corruption tonale** :
  - [x] Au lieu de supprimer toute la ponctuation/majuscules, générer des réponses rejetées contenant du *code-switching* excessif (mélange fr/en non naturel), de la redondance excessive ou un ton condescendant.
- [x] **Intégrer le feedback utilisateur réel** :
  - [x] Connecter le compilateur à la base Django via [dpo_feedback_loop.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/dpo_feedback_loop.py) pour collecter et formater les pouces levés/baissés réels de l'application en paires (chosen/rejected).
- [X] **DPO par critique de LLM (LLM-as-a-Judge)** :
  - [X] Utiliser Gemini pour générer des variantes `rejected` contenant de subtiles erreurs de logique ou de raisonnement au lieu d'heuristiques rigides.

---

## ⚙️ 3. MLOps et Qualité des Données
- [x] **Ajouter des validations strictes par schéma (Pydantic)** :
  - [x] Valider chaque échantillon généré au moment de la compilation pour éliminer les résidus HTML, les balises de code mal formées ou les réponses d'API en échec.
- [x] **Suivi des métriques de drift et régression** :
  - [x] Intégrer les analyses de détection de dérive sémantique avant de lancer de nouveaux entraînements majeurs.

---

## 🎯 4. Amélioration du Gold Set (Validation & Évaluation RAG)
Fichiers cibles : [gold_dataset.json](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/data/mlops/gold_dataset.json), [regression_benchmark.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/evaluation/regression_benchmark.py), [synthetic_gold_generator.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/evaluation/synthetic_gold_generator.py)

- [x] **Enrichissement et Diversification des requêtes** :
  - [x] Ajouter des requêtes de test multilingues (localisation FR/JP) pour valider le support bilingue.
  - [x] Développer des cas d'usage multi-hop complexes (3+ relations) dans le graphe Neo4j pour pousser le pipeline hybride dans ses retranchements.
- [x] **Évolution du schéma du Gold Set** :
  - [x] Intégrer un champ `expected_entities` (nœuds de graphe cibles) pour valider la pertinence de la recherche de graphe sans dépendre uniquement d'un LLM Juge.
  - [x] Ajouter `expected_chunks` / `expected_contexts` pour calculer de manière déterministe les métriques de *Context Recall* et *Context Precision*.
  - [x] Structurer le schéma pour supporter les évaluations multi-tours via un champ `multi_turn_history`.
- [x] **Automatisation de la génération par HITL (Human-in-the-loop)** :
  - [x] Extraire des motifs de graphe relationnels aléatoires depuis Neo4j pour générer des couples QA synthétiques complexes via LLM de façon automatisée.
  - [x] Connecter le système de feedback utilisateur de l'application Django pour flagger et stager automatiquement les requêtes utilisateur complexes dans une file de modération HITL avant leur intégration dans le Gold Set.
- [x] **Intégration CI/CD et MLOps** :
  - [x] Exécuter automatiquement `regression_benchmark.py` comme hook de validation dans le pipeline CI/CD (GitHub Actions) pour bloquer les merges en cas de régression de la précision factuelle.
  - [x] Étendre le reporting W&B (Weights & Biases) dans [evaluation_metrics.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/evaluation_metrics.py) pour logguer la latence, le coût (tokens) et faire des analyses d'erreurs par tranches (performance par type de requête et par niveau de difficulté).
- [ ] **Pistes d'amélioration futures du Gold Set** :
  - [x] **Augmentation de la diversité & analyse de couverture** : Analyser le taux de couverture des requêtes sur le graphe Neo4j et la base vectorielle pour combler automatiquement les angles morts sémantiques.
  - [x] **Requêtes adverses & Red-Teaming** : Intégrer des requêtes négatives (ex. entités fictives), des titres ambigus et des cas d'injection de prompt pour tester la robustesse factuelle et sécuritaire.
  - [x] **Interface d'administration interactive HITL** : Développer une vue Django Admin dédiée pour faciliter la révision, l'édition factuelle et la validation humaine des requêtes utilisateur stagées.
  - [x] **Synchronisation automatique de la Vérité Terrain** : Créer un pipeline pour rafraîchir périodiquement les faits des Ground Truths du Gold Set à partir des dernières données réelles de Neo4j.

