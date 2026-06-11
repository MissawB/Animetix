# Design Spec: Bilingual Support (English & French)

Ce document décrit les modifications techniques nécessaires pour doter Animetix d'une capacité bilingue (Français et Anglais) à la fois dans son pipeline RAG en production et dans le jeu de données d'entraînement SFT.

---

## 1. Objectifs & Exigences
* **Service RAG** : Le pipeline RAG doit traiter les requêtes en français ou en anglais selon la préférence de l'utilisateur (détectée depuis l'URL ou la session) et formuler ses réponses strictement dans cette langue.
* **Modèle SFT** : Le dataset d'entraînement doit être composé d'exemples bilingues équilibrés (~50% Français, ~50% Anglais) pour aligner l'expert dans les deux langues sans code-switching.
* **Qualité** : Garantir le format JSON des réponses de synthèse quel que soit le langage cible.

---

## 2. Architecture & Modifications Proposées

### Component 1: RAG API & Context Propagation
* **`RAGContext`** ([ai_schemas.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/entities/ai_schemas.py)) :
  Ajouter un champ `language: str = "Français"` dans la classe Pydantic `RAGContext` pour véhiculer la langue cible à travers tous les processeurs de la machine à états.
* **`AgenticRAGStreamView`** ([streams.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/api/streams.py)) :
  Récupérer la langue depuis les paramètres GET (`lang`) ou la session Django. Détecter l'anglais si la chaîne contient `'en'` ou `'eng'`, et normaliser sous forme de `"English"` ou `"Français"`.
* **`AgenticRAGService`** ([agentic_rag_service.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/agentic_rag_service.py)) :
  Propager l'argument `language` de `plan_and_solve_stream` vers `RAGContext(..., language=language)`.

### Component 2: Agents & Processors
* **`prompts.yaml`** ([prompts.yaml](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/prompts/prompts.yaml)) :
  Généraliser `synthesizer_final` et `synthesizer_correction` pour injecter la variable de langue cible `{language}` dans les prompts système et templates.
* **`ResponseSynthesizer`** ([synthesizer.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/rag/agents/synthesizer.py)) :
  Transmettre le paramètre `language` lors de l'appel à `prompt_manager.get_prompt` pour formater dynamiquement la langue de la réponse.
* **`SynthesizeProcessor`** ([synthesize_processor.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/rag/processors/synthesize_processor.py)) :
  Passer `ctx.language` à `synthesizer.synthesize_stream`.
* **`FallbackRagProcessor`** ([fallback_rag_processor.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/rag/processors/fallback_rag_processor.py)) :
  Traduire à la volée les instructions et prompts système de secours en anglais si `ctx.language == "English"`.

### Component 3: SFT Dataset Compiler & Training
* **`finetuning_dataset.py`** ([finetuning_dataset.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/finetuning_dataset.py)) :
  * Créer des fonctions génératrices parallèles en anglais (ex: `make_english_anime_profile`, `make_english_manga_profile`, `make_english_character_bio`).
  * Introduire une répartition bilingue 50/50 pour les exemples spécialisés et méta générés.
  * Charger des instructions générales anglophones (provenant d'Alpaca original) à hauteur de 15% pour compléter les instructions générales françaises.
  * Ajouter une clé `"language": "English"` ou `"language": "Français"` dans chaque objet JSONL exporté.
* **`train_expert_model.py`** ([train_expert_model.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/train_expert_model.py)) :
  * Détecter la clé `"language"` de chaque exemple lors du formatage ChatML.
  * Sélectionner un prompt système spécifique en anglais ou en français selon la langue de l'exemple.

---

## 3. Stratégie de Validation
* **Tests Unitaires** :
  * Écrire des assertions vérifiant que `AgenticRAGService` initialise correctement la langue souhaitée.
  * Tester que `SynthesizeProcessor` et `FallbackRagProcessor` transmettent et appliquent correctement la langue cible.
  * Valider que `finetuning_dataset.py` génère bien des clés de langue dans les lignes JSONL.
  * Valider que `train_expert_model.py` formate correctement le prompt système selon la clé de langue.
* **Validation Manuelle** :
  * Lancer une simulation de stream RAG avec le paramètre `lang=en` et s'assurer que les tokens sont générés en anglais.
