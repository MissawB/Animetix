# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🏗️ Nettoyage & Refactorisation Core
- [ ] **Suppression des Scripts Orphelins :** Supprimer les scripts de refactorisation et de fix temporaires devenus inutiles (`refactor_di.py`, `refactor_di_all.py`, `fix_explore_aria.py`, `backend/api/list_users.py`, `backend/api/list_users_fixed.py`).
- [ ] **Optimisation Boot Backend (Lazy Loading) :** Finaliser la refactorisation de `CoreServicesContainer.py` et `PersistenceContainer.py` pour utiliser des imports dynamiques (chaînes de caractères) afin de réduire le temps de démarrage du serveur (actuellement encore majoritairement statique).
- [ ] **Nettoyage Dépendances Frontend :** Auditer et supprimer les dépendances potentiellement inutilisées dans `package.json` (`three`, `plotly.js`) pour réduire la taille du bundle.
- [ ] **Audit de Sécurité SQL Guard :** Réaliser le "fuzzing" et la revue de sécurité formelle du parseur `sql_guard.py` (marqué comme HIGH-RISK dans le code).

### 🏗️ Complétion des Adapteurs (Stubs)
- [ ] **Génération de Sprites Réelle :** Remplacer le stub `"stub-url"` dans `DiffusersAdapter.generate_sprite` par une implémentation réelle utilisant le pipeline de diffusion.
- [ ] **Latence Alert Service :** Connecter l' `AlertService` à l'`ObservabilityService` pour récupérer et monitorer la latence réelle des requêtes RAG.
- [ ] **Endpoints MLOps Réels :** Implémenter la logique métier réelle pour `AdaptersView` et `DPOFeedbackLoopView` dans `backend/api/animetix/api/mlops.py` (actuellement en mode placeholder).

---

## ⚙️ MLOps, Qualité & Observabilité
- [ ] **Stabilisation des "Ghost Labs" :** Finaliser les tests d'intégration et le durcissement des services de recherche (LNN, Plasticité Synaptique, Quantum Cognition) pour passage en état "Operational" complet (actuellement en beta/recherche).
- [x] **Audit Accessibilité (WCAG) :** Finaliser l'audit complet via Playwright et corriger les derniers problèmes d'accessibilité identifiés.
- [x] **Monitoring Alerting :** Configurer les alertes Prometheus pour le drift d'archétype et la stabilité des modèles.

---

## 🎨 Interface & Expérience Utilisateur
- [ ] **Fusion Studio Multivers :** Unifier le workflow entre la génération (`MultiverseLabPage`) et la galerie (`MultiverseGalleryPage`).
- [ ] **Manga Reader Backend :** Finaliser la connexion au backend réel pour le chargement dynamique des chapitres.
- [ ] **UI Indexation Vidéo :** Finaliser l'interface d'indexation pour le Video-RAG côté Admin.

---

## 🚀 Expansion & Futur
- [ ] **Déploiement Multi-Régions :** Préparer les scripts d'infrastructure pour un déploiement sur plusieurs régions Google Cloud.
- [ ] **Rapports de Conformité :** Automatiser les rapports hebdomadaires de conformité sécurité.

---
*Dernière mise à jour : 15 Juin 2026*
