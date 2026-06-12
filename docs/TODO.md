# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧪 Suite de Tests & Régressions
- [x] **Nettoyage et Normalisation Textuelle du Dataset SFT** :
  - Mettre en place un nettoyage regex rigoureux dans `finetuning_dataset.py` pour éliminer le balisage HTML (`<br>`, `<i>`), les entités HTML et les caractères spéciaux parasites des descriptions brutes.

### 🗺️ Améliorations Lore World Map (UI/UX & Data Science)
- [X] **Visualisation Interactive du Graphe** :
  - Remplacer la vue "grille de cartes" actuelle par un vrai composant de graphe interactif (ex: `react-force-graph-2d` ou `3d`) pour visualiser la topologie des clusters Neo4j.
- [x] **Timeline de Généalogie des Studios** : 
  - Développer une vue chronologique des productions et influences entre studios/créateurs en utilisant les relations du graphe.
- [X] **Interactivité des Éléments** :
  - Câbler le bouton "Explorer la zone" sur chaque carte de cluster pour ouvrir un panneau latéral ou une vue détaillée du cluster.
  - Rendre les badges d'entités cliquables pour lancer une recherche rapide contextuelle.
- [x] **Légende et Couleurs Dynamiques** :
  - Appliquer dynamiquement les couleurs de la "Légende Dynamique" en fonction des métriques réelles (score de densité, modularité).
- [x] **Recherche et Filtrage** :
  - Ajouter une barre de recherche en texte libre pour trouver rapidement un cluster par thématique ou entité.
  - Ajouter des filtres de tri (par taille de communauté, par score de pertinence, etc.).
- [x] **Enrichissement des Métriques MLOps** :
  - Remplacer les textes statiques du panneau "État du Graphe" par les vraies métriques de clustering.

---

## 🎨 Qualité de Code & Accessibilité Frontend

### 🧹 Nettoyage des erreurs ESLint
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats.
  - Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](frontend/src/pages/utils/CustomConfigPage.tsx).
  - Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](frontend/src/types/api.d.ts).

### 🔒 Sécurité & Robustesse
- [ ] **Audit de Sécurité SQL (NL Query)** : 
  - Réviser rigoureusement `backend/adapters/persistence/django_repository_adapter.py` et `core/utils/sql_guard.py`.
  - S'assurer que les guardrails contre l'injection SQL sont infranchissables pour la fonctionnalité de requête en langage naturel.
- [ ] **Alignement de la Documentation** :
  - Synchroniser `docs/ROADMAP.md` avec la réalité opérationnelle du `TODO.md`.
  - Mettre à jour les dates et le statut des phases IA (certaines marquées `:done` alors qu'elles sont en cours d'optimisation).

### 🏗️ Finalisation des pages "Squelettes"
- [x] **VideoRagPage** : Implémenter l'interface d'exploration temporelle profonde et de navigation narrative. (Fait : Timeline interactive et inspecteur sémantique opérationnels).
- [x] **ApiHubPage** : Documenter interactivement les endpoints API v1 pour les développeurs tiers. (Fait : Explorateur d'API dynamique avec exemples de payloads/réponses).
- [x] **ObservabilityConsolePage** : Intégrer les graphiques de latence RAG, de consommation de tokens et de dérive sémantique. (Fait : Dashboard télémétrique temps réel avec traces d'agents simulées).

### ♿ Accessibilité (a11y)
- [ ] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA on les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## 📈 Suivi & Performance (Ops)

- [x] **Mise en place de métriques de performance granulaires** :
  - Collecter en temps réel le temps d'exécution des requêtes de base de données vectorielles (pgvector) et sémantiques (Neo4j).
  - Enregistrer les temps de réponse de l'API RAG. (Fait : Instrumentation des adaptateurs persistence et des services RAG avec logging vers W&B).
- [x] **Alertes de dégradation de performance** :
  - Configurer un système de notifications/alertes en cas de pic de latence d'inférence ou de dérive sémantique importante des profils d'archetypes utilisateur. (Fait : Implémentation d'AlertService, détection automatique des pics >2s et des dérives majeures d'archétypes avec notifications via WebSockets/DB).

---

### 🧠 Améliorations de l'IA & MLOps Futures
- [x] **Système de Cache Persistant pour l'Augmentation Gemini :**
  - Implémenter un cache local persistant (ex: fichier JSON) pour stocker les paraphrases générées par Gemini, évitant les requêtes API répétitives lors des régénérations de dataset.
- [x] **Diversification des Genres et Ratios Configurables :**
  - Diversifier la base d'entraînement avec des genres plus larges (Shojo, Josei, Tranche de vie) et rendre les ratios de composition (Spécialisé, Méta, Général) configurables par variables d'environnement.
- [x] **Résilience des Scénarios d'Appels d'Outils (MCP) :**
  - Simuler des réponses d'erreur ou d'indisponibilité d'outils (`<tool_response>` en statut d'erreur/timeout) dans les exemples d'entraînement pour apprendre au modèle expert à réagir poliment et intelligemment en cas de panne.
- [x] **Améliorations SOTA 2026 de la Base d'Entraînement SFT :**
  - [x] **Dialogues Multi-Tours (Multi-turn)** : Intégrer ~15-20% de scénarios de dialogues à plusieurs tours pour apprendre au modèle à suivre le contexte sur plusieurs messages consécutifs.
  - [x] **Persona & Refus (Negative Examples)** : Ajouter des exemples de requêtes hors-sujet avec refus poli pour cadrer l'expertise exclusive du modèle sur l'univers anime/manga.
  - [x] **Rééquilibrage Thématique** : Assurer une proportion minimale de genres sous-représentés (Shojo, Josei, Tranche de vie) pour atténuer le biais actuel Shonen/Seinen.
  - [x] **Validation factuelle via "LLM-as-a-Judge"** : Mettre en place un validateur automatique pour vérifier que les paraphrases et traductions générées par l'API ne contiennent pas d'hallucinations factuelles par rapport aux fiches d'œuvres locales.
  - [x] **Complexification sémantique multi-tours** : Simuler des flux de dialogues plus variés incluant des débats comparatifs, des requêtes de clarification et des auto-corrections après retour utilisateur fictif.
  - [x] **Query Noise (Robustesse aux fautes de saisie)** : Injecter du bruit (fautes de frappe, abréviations, argot, absence de ponctuation) dans 10-15% des instructions utilisateur pour accroître la robustesse de l'expert en conditions réelles.
- [x] **Construction d'un dataset de préférence DPO / RLHF** :
  - Compiler des exemples appariés (Réponse correcte vs Réponse rejetée/hallucinée) pour aligner finement le ton et le formatage du modèle via DPO.

### 🏗️ Pipeline RAG 2.0 (Next)
- [x] **Implement RAG Processors**: Implement `SpeculateProcessor`, `VlmRerankProcessor`, `SynthesizeProcessor`, `JudgeProcessor`, `FallbackRagProcessor`, and `RAGOrchestrator`. Update DI container and refactor/remove `RAGWorkflowManager`. (Fait : Toutes les classes de processeurs RAG et l'orchestrateur sont implémentés sous `backend/core/domain/services/rag/processors/`, configurés dans le conteneur DI `AgenticContainer`, et vérifiés avec une couverture de tests unitaires complète).

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
- [x] **Renforcer les cas de refus hors-domaine** :
  - [x] Ajouter des exemples de questions complètement hors sujet (cuisine, programmation hors MCP, questions générales sans lien avec la culture otaku) pour apprendre au modèle à refuser poliment d'y répondre.

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
