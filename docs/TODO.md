# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧪 Suite de Tests & Régressions
- [x] **Nettoyage et Normalisation Textuelle du Dataset SFT** :
  - Mettre en place un nettoyage regex rigoureux dans `finetuning_dataset.py` pour éliminer le balisage HTML (`<br>`, `<i>`), les entités HTML et les caractères spéciaux parasites des descriptions brutes.

### 🗺️ Améliorations Lore World Map (UI/UX & Data Science)
- [ ] **Visualisation Interactive du Graphe** :
  - Remplacer la vue "grille de cartes" actuelle par un vrai composant de graphe interactif (ex: `react-force-graph-2d` ou `3d`) pour visualiser la topologie des clusters Neo4j.
- [ ] **Timeline de Généalogie des Studios** : 
  - Développer une vue chronologique des productions et influences entre studios/créateurs en utilisant les relations du graphe.
- [ ] **Interactivité des Éléments** :
  - Câbler le bouton "Explorer la zone" sur chaque carte de cluster pour ouvrir un panneau latéral ou une vue détaillée du cluster.
  - Rendre les badges d'entités cliquables pour lancer une recherche rapide contextuelle.
- [ ] **Légende et Couleurs Dynamiques** :
  - Appliquer dynamiquement les couleurs de la "Légende Dynamique" en fonction des métriques réelles (score de densité, modularité).
- [ ] **Recherche et Filtrage** :
  - Ajouter une barre de recherche en texte libre pour trouver rapidement un cluster par thématique ou entité.
  - Ajouter des filtres de tri (par taille de communauté, par score de pertinence, etc.).
- [ ] **Enrichissement des Métriques MLOps** :
  - Remplacer les textes statiques du panneau "État du Graphe" par les vraies métriques de clustering.

---

## 🎨 Qualité de Code & Accessibilité Frontend

### 🧹 Nettoyage des erreurs ESLint
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats.
  - Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](frontend/src/pages/utils/CustomConfigPage.tsx).
  - Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](frontend/src/types/api.d.ts).

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
- [ ] **Alertes de dégradation de performance** :
  - Configurer un système de notifications/alertes en cas de pic de latence d'inférence ou de dérive sémantique importante des profils d'archetypes utilisateur.

---

### 🧠 Améliorations de l'IA & MLOps Futures
- [x] **Système de Cache Persistant pour l'Augmentation Gemini :**
  - Implémenter un cache local persistant (ex: fichier JSON) pour stocker les paraphrases générées par Gemini, évitant les requêtes API répétitives lors des régénérations de dataset.
- [x] **Diversification des Genres et Ratios Configurables :**
  - Diversifier la base d'entraînement avec des genres plus larges (Shojo, Josei, Tranche de vie) et rendre les ratios de composition (Spécialisé, Méta, Général) configurables par variables d'environnement.
- [x] **Résilience des Scénarios d'Appels d'Outils (MCP) :**
  - Simuler des réponses d'erreur ou d'indisponibilité d'outils (`<tool_response>` en statut d'erreur/timeout) dans les exemples d'entraînement pour apprendre au modèle expert à réagir poliment et intelligemment en cas de panne.

### 🏗️ Pipeline RAG 2.0 (Next)
- [ ] **Implement RAG Processors**: Implement `SpeculateProcessor`, `VlmRerankProcessor`, `SynthesizeProcessor`, `JudgeProcessor`, `FallbackRagProcessor`, and `RAGOrchestrator`. Update DI container and refactor/remove `RAGWorkflowManager`.
