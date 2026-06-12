# 📋 Plan d'Amélioration de la Base de Données d'Entraînement

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
- [ ] **Intégrer le feedback utilisateur réel** :
  - [ ] Connecter le compilateur à la base Django via [dpo_feedback_loop.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/dpo_feedback_loop.py) pour collecter et formater les pouces levés/baissés réels de l'application en paires (chosen/rejected).
- [ ] **DPO par critique de LLM (LLM-as-a-Judge)** :
  - [ ] Utiliser Gemini pour générer des variantes `rejected` contenant de subtiles erreurs de logique ou de raisonnement au lieu d'heuristiques rigides.

---

## ⚙️ 3. MLOps et Qualité des Données
- [ ] **Ajouter des validations strictes par schéma (Pydantic)** :
  - [ ] Valider chaque échantillon généré au moment de la compilation pour éliminer les résidus HTML, les balises de code mal formées ou les réponses d'API en échec.
- [ ] **Suivi des métriques de drift et régression** :
  - [ ] Intégrer les analyses de détection de dérive sémantique avant de lancer de nouveaux entraînements majeurs.
