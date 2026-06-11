# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧪 Suite de Tests & Régressions
- [ ] **Réparer l'import et l'initialisation d'AgenticRAGService** :
  - Mettre à jour les tests unitaires et d'intégration ([test_cognitive_rag.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_cognitive_rag.py), [test_chronicler_theories.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_chronicler_theories.py), [test_agent_observability_gateway.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_agent_observability_gateway.py)) suite à la suppression de `RAGWorkflowManager`.
  - Remplacer l'injection du paramètre obsolète `workflow_manager` par `workflow_orchestrator`.
  - Adapter les appels directs aux méthodes privées (ex: `_handle_research`) devenues des processeurs indépendants.
- [ ] **Corriger les Mocks & Contrats dans les Tests** :
  - **CoVe Oracle** : Ajuster [test_cove_oracle_service.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/core/test_cove_oracle_service.py) pour renvoyer des instances de type `InferenceResponse` avec un attribut `.text` plutôt que des chaînes brutes (`AttributeError: 'str' object has no attribute 'text'`).
  - **Local Guardrail** : Mettre à jour [test_semantic_guardrail.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/adapters/test_semantic_guardrail.py) pour mocker la méthode `moderate_content` de l'engine d'inférence plutôt que `generate_structured`.
  - **Spatial Inference** : Mettre à jour [test_spatial_inference.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/adapters/test_spatial_inference.py) afin de ne pas appeler `estimate_depth` sur `DiffusersAdapter` (qui n'est plus supporté).
- [ ] **Mettre à jour le test d'API Voice Cloning** :
  - Modifier [test_voice_cloning_api.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/api/test_voice_cloning_api.py) pour injecter une entête audio WAV valide (magic numbers binaire `RIFF/WAVE`) afin de passer la validation de sécurité MIME type.
- [ ] **Résoudre les conflits de noms de modules dans Pytest** :
  - Supprimer ou renommer les fichiers de tests dupliqués (`test_local_text_adapter.py` et `test_explore.py`) ou ajouter des `__init__.py` manquants pour éviter les erreurs `import file mismatch` lors de la collecte globale de Pytest.

### 🔌 Intégration Fonctionnelle
- [ ] **Brancher la boucle cognitive en production** :
  - Connecter l'appel à `update_cognitive_state` de [AdvancedRAGService](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/advanced_rag_service.py) dans les vues de recherche ou de gameplay afin que les retours (plasticité synaptique et état quantique de l'utilisateur) soient appliqués et persistés en temps réel.

---

## 🎨 Qualité de Code & Accessibilité Frontend

### 🧹 Nettoyage des erreurs ESLint
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats.
  - Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/utils/CustomConfigPage.tsx) pour éviter les rendus en cascade.
  - Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/types/api.d.ts).

### ♿ Accessibilité (a11y)
- [ ] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA sur les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## 📈 Suivi & Performance (Ops)

- [ ] **Mise en place de métriques de performance granulaires** :
  - Collecter en temps réel le temps d'exécution des requêtes de base de données vectorielles (pgvector) et sémantiques (Neo4j).
  - Enregistrer les temps de réponse de l'API RAG.
- [ ] **Alertes de dégradation de performance** :
  - Configurer un système de notifications/alertes en cas de pic de latence d'inférence ou de dérive sémantique importante des profils d'archetypes utilisateur.

---

### 📚 Mises à jour de la documentation requises

#### 📄 Root README.md
- [ ] **Audit des ancres du Table des Matières** : Vérifier que toutes les ancres (ex: `#-gcp-infrastructure`) sont compatibles avec le rendu GitHub (les emojis peuvent casser les liens).
- [ ] **Ajouter des directives de contribution** : Soit créer un `CONTRIBUTING.md`, soit ajouter une section simplifiée dans le `README.md`.
- [ ] **Vérifier l'accessibilité des Ghost Labs** : S'assurer que les liens vers les différents Labs (Vision, Spatial, etc.) dans la documentation pointent vers des sections ou des pages existantes et fonctionnelles.

#### 🏛️ Architecture (ARCHITECTURE.md)
- [ ] Clarifier le rôle de Django dans le diagramme Hexagonal (note explicite "Port API" ou adaptateurs de pilotage).
- [ ] Expliquer l'omission de `MlopsPort` dans le diagramme architectural principal.
- [ ] Ajouter une brève explication sur la raison d'utilisation de Dependency-Injector.

### 📖 Guide Complet (FULL_GUIDE.md)
- [ ] Ajouter un guide de configuration de l'environnement de développement local.
- [ ] Inclure des exemples d'utilisation de l'API.
- [ ] Ajouter des directives de contribution.
- [ ] Créer un glossaire des termes.
- [ ] Ajouter une section de dépannage (Troubleshooting).
- [ ] Ajouter des recommandations sur les exigences matérielles.
- [ ] Définir explicitement "SLM" (Small Language Model).
- [ ] Clarifier ou développer le concept de "Anime Archetype Engine".

#### 📄 Feuille de Route (ROADMAP.md)
- [ ] Corriger la chronologie du diagramme de Gantt (actuellement tous marqués `:done` malgré des dates futures).
- [ ] Synchroniser les initiatives de `ROADMAP.md` avec celles listées dans `TODO.md`.
- [ ] Ajouter une section "Prochaines Étapes" (Next Steps) pour séparer le travail fondamental d'IA terminé des futures mises à jour.

#### 📄 backend/GEMINI.md
- [ ] **Mettre à jour les standards de validation API** : Remplacer la mention de Django `Forms` par les `DRF Serializers` pour les vues critiques.
- [ ] **Documenter les nouvelles protections IA** : Ajouter des sections sur le "Universal HITL Gate" et la protection contre le "Model Collapse".
- [ ] **Mettre à jour la liste des services AI** : Refléter la fusion de `UncertaintyService` dans `XaiDiagnosticService`.
- [ ] **Documenter les Ghost Labs** : Ajouter les directives et endpoints pour les modules réactivés (Manga, Video, Spatial, Audio).
- [ ] **Intégration MLOps** : Documenter le rôle de `StarMLOpsDomainService` et la connexion des outils Admin MLOps.

#### 📄 frontend/GEMINI.md
- [x] **Mettre à jour les mandats frontend** : Intégrer la structure FDD, le typage strict (anti-any), l'accessibilité détaillée (ARIA, tracks) et l'observabilité (Sentry/PostHog).
- [ ] **Refactoriser les typages API** : Supprimer les déclarations manuelles de modèles API dans `src/api.ts` et `src/types/index.ts` au profit des types générés dans `src/types/api.d.ts`.

---

## 🧠 IA, Alignement & MLOps (Améliorations SOTA 2026)


### 🚀 Modèles de Base & Alignement
- [x] **Évaluation et Migration vers Qwen3 / DeepSeek-R1** :
  - Migrer le modèle de base `Qwen2.5-7B-Instruct` vers `Qwen3-8B-Instruct` ou `DeepSeek-R1-Distill-Qwen-8B` pour des capacités linguistiques, culturelles et de raisonnement accrues. (Configuré dynamiquement via la variable d'environnement `BASE_MODEL_NAME`, avec `unsloth/DeepSeek-R1-Distill-Qwen-8B` par défaut).
- [x] **Mise en œuvre de l'alignement par préférences SimPO / ORPO** :
  - Implémenter un script d'alignement de préférences `train_preference.py` exploitant les retours utilisateurs loggés en production sous forme de paires `(Chosen, Rejected)`. (Fait : Nouveau script [train_preference.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/train_preference.py) opérationnel avec support dynamique de SimPO/ORPO/DPO, Unsloth et génération de données synthétiques de secours).
- [x] **Intégration d'Unsloth Studio & Triton Kernels** :
  - Activer le *Sequence Packing* dans le `SFTTrainer` pour éliminer le padding des séquences courtes et diviser le temps d'entraînement par 2. (Fait : Géré dynamiquement via `ANIMETIX_PACKING=True` dans [train_expert_model.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/train_expert_model.py)).
  - Exploiter les nouveaux noyaux d'accélération d'embeddings d'Unsloth pour accélérer le fine-tuning contrastif dans [train_embeddings.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/train_embeddings.py). (Fait : `FastSentenceTransformer` utilisé de manière transparente en présence d'Unsloth).

### 📊 Base de Données & Data Engineering
- [x] **Augmentation de Données Synthétiques par LLM** :
  - Remplacer les gabarits de texte figés dans [finetuning_dataset.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/finetuning_dataset.py) par des reformulations et paraphrases dynamiques générées par LLM (via l'API Gemini 1.5/2.5/3) pour diversifier les styles de conversation. (Fait : Intégration de l'API Gemini avec gestion de quota/unavailability via backoff sleep progressif et tri par popularité (Top-N) pour optimiser les appels d'API).
- [x] **Cadrage d'outils via le protocole MCP (Model Context Protocol)** :
  - Entraîner le modèle expert à interagir nativement avec des serveurs MCP pour interroger de manière dynamique les API tierces (MAL/Jikan, Spotify) sans dépendre de scripts rigides en Django. (Fait : Génération de 213 paires SFT structurées sous forme d'appels d'outils XML/JSON `<tool_call>` et de traitements de réponses XML/JSON `<tool_response>`).

### 🧠 Améliorations de l'IA & MLOps Futures
- [x] **Automatisation de la boucle de feedback DPO via Modèle Oracle (Gemini) :**
  - Mettre à jour `dpo_feedback_loop.py` pour qu'il appelle l'API Gemini afin de générer automatiquement les réponses d'expert (chosen) corrigées lors du traitement des retours utilisateurs négatifs (rejected), éliminant ainsi les placeholders. (Fait : Nouveau client Oracle Gemini intégré avec gestion de quota via pauses progressives et fallback sécurisé).
- [x] **Alignement du Modèle Draft pour le Décodage Spéculatif :**
  - Modifier `continuous_pretraining.py` pour pré-entraîner et distiller le modèle de draft `SmolLM-135M` directement sur les dialogues et instructions du dataset d'entraînement expert, maximisant ainsi le taux d'acceptation des tokens et la vitesse d'inférence. (Fait : Support du mode distillation ChatML avec injection de tokens spéciaux et resize d'embeddings).
- [x] **Résilience du Juge RAG (LLM Judge Fallback) :**
  - Implémenter un mécanisme de repli sémantique dans `evaluation_metrics.py` utilisant l'API distante Gemini si le moteur d'inférence local de l'application est indisponible ou saturé lors des évaluations sémantiques Ragas. (Fait : Fallback sémantique structuré natif via l'API Gemini et scores de secours par défaut intégrés).
- [ ] **Support Multi-GPU et Distributed Training :**
  - Adapter `train_preference.py` et `train_expert_model.py` pour supporter nativement DeepSpeed Zero-3 ou FSDP afin de répartir efficacement la charge d'entraînement sur plusieurs GPU lors de l'utilisation de modèles 8B+.