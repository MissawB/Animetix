# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧹 Nettoyage des erreurs ESLint
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats.
  - Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](frontend/src/pages/utils/CustomConfigPage.tsx).
  - Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](frontend/src/types/api.d.ts).

### 🏗️ Refactorisation Core
- [ ] **Finaliser la migration du RAG Workflow** :
  - Compléter la transition du `RAGWorkflowManager` vers l'architecture `StateProcessor`.
  - Nettoyer les résidus de logique de planification éparpillés dans les anciens services.

### 🔒 Sécurité & Robustesse
- [x] **Audit de Sécurité SQL (NL Query)** : 
  - Réviser rigoureusement `backend/adapters/persistence/django_repository_adapter.py` et `core/utils/sql_guard.py`.
  - S'assurer que les guardrails contre l'injection SQL sont infranchissables pour la fonctionnalité de requête en langage naturel.
  - *Fix: Implémentation d'une transaction strictement read-only avec timeout et renforcement du parseur SQL.*
- [x] **Alignement de la Documentation** :
  - Synchroniser `docs/ROADMAP.md` avec la réalité opérationnelle du `TODO.md` (Phases D à L).
  - Mettre à jour les dates et le statut des phases IA (certaines marquées `:done` alors qu'elles sont en cours d'optimisation).
  - *Fix: Roadmap mise à jour vers l'état "EN COURS" avec diagramme de Gantt et notes opérationnelles synchronisées.*

### ♿ Accessibilité (a11y)
- [ ] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA sur les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## ⚙️ MLOps et Qualité des Données
- [x] **Contrôle de qualité via dbt/Dataform** : Mettre en place des tests de qualité de données (schémas, doublons, intégrité référentielle) au niveau SQL avant l'entraînement.
- [x] **Orchestration Apache Beam scalable** : Migrer l'ingestion vers [lore_ingestion_beam.py](backend/pipeline/mlops/lore_ingestion_beam.py) exécuté sur Dataflow pour la robustesse et la scalabilité.
- [ ] **Phase L.2 - Multimodal SFT (Axe A)** : Indexation et génération de paires d'entraînement images/vidéos + texte (mangas, animes) pour fine-tuner le modèle expert sur les capacités vision-langage.

---

## 🎨 Interface & Expérience Utilisateur

### 📊 Suivi & Contrôle
- [x] **Tableau de Bord des Quotas IA (User Side)** : Créer une page `/settings/usage` permettant aux utilisateurs de suivre leur consommation de jetons.
- [ ] **Gestionnaire de Clés API Utilisateur** : Implémenter une interface dans les paramètres pour générer, copier et révoquer des clés API (`atx_...`) pour les développeurs tiers.

### 🧩 Exploration & Immersion
- [ ] **Explorateur de Voisinage de Graphe** : Développer la page `/graph/neighborhood` pour la visualisation des connexions locales (backend `GraphNeighborsView` déjà prêt).
- [ ] **Lecteur de Manga Immersif** : Créer un composant de lecture fluide pour les planches traitées par le `MangaLab`.
- [ ] **Carte Interactive Seichijunrei** : Transformer la liste des lieux de pèlerinage en une véritable carte géographique interactive.
- [ ] **Hub Unifié "Singularity Command Center"** : Centraliser les expériences IA Omega (Quantum, Plasticity, Swarm) dans une interface de monitoring unique.

---

## 📡 Observabilité & Alerting
- [ ] **Recalibrage des Alertes de Dérive** : Ajuster les seuils de l' `AlertService` pour la détection de dérive sémantique du profil utilisateur afin de minimiser les faux positifs.
