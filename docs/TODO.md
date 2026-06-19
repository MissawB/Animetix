# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## ✨ Fonctionnalités Manquantes (Expérience Utilisateur)

### 🧩 Navigation & Découvrabilité (Audit Juin 2026)

- [x] **Exposition des Fonctionnalités Orphelines :**
    - Ajouter des entrées Sidebar pour **Nexus Pro** (`/social/nexus/`) et **Transparence Système** (`/social/transparency/`).
    - Créer une section **"Outils Admin & Monitoring"** dans la Sidebar (visible pour le staff) incluant :
        - Audit de Sécurité IA (`/admin/safety-audit/`)
        - Monitoring TTC / Latence (`/admin/ttc-monitoring/`)
        - Gestion Financière & Coûts API (`/admin/financials/`)
- [x] **Raccordement des "Ghost Labs" (Beta) :**
    - Rendre accessibles via le menu principal ou une navigation secondaire :
        - Synthèse Vocale Seiyuu (`/lab/audio/seiyuu/`)
        - Compilateur Numba/IA (`/lab/compiler/`)
        - Video RAG (Recherche flux vidéo) (`/lab/video-rag/`)
        - Oracle de Cove (Prédictions) (`/lab/cove-oracle/`)

### 🛠️ Nouvelles Pages Dédiées (Backend Mapping)

- [x] **Centre de Synchronisation de Données :**
    - Créer une page permettant de visualiser les données locales/hors-ligne en attente de synchronisation et de forcer la réconciliation manuelle (`sync_offline_data`).
- [x] **Historique des Feedbacks IA :**
    - Implémenter la vue pour `/social/ai-feedback-history/` permettant aux utilisateurs de revoir leurs interactions passées avec les agents de validation.
- [x] **Portail de Données Ouvertes (Open Data) :**
    - Page de téléchargement des datasets publics (paires DPO, logs anonymisés) pour la conformité académique.
- [ ] **Tableau de Bord "État du Cluster" :**
    - Visualisation temps réel de la santé des instances NVIDIA H100, Ollama, et du Knowledge Graph (Neo4j).

### 🌌 Autres Fonctionnalités

- [ ] **Catalogue de la Galerie Multivers (Multiverse Gallery) :**
    - Implémenter une véritable page "Catalogue" (grille/liste) avec filtres et recherche pour explorer les univers synthétiques générés par la communauté.
- [ ] **Boutique d'Actifs Digitaux (Market/Trading) :**
    - Créer une page de type "Shop" ou "Marketplace" dédiée à l'achat/vente et à l'échange d'actifs digitaux.

---

## 🧹 Résolution de la Dette Technique

- [ ] **Centralisation HTTP (Frontend) :** Remplacer les appels directs à `fetch()` par `apiClient` dans les pages de jeu (`AkinetixRLPage`, `DuelLobbyPage`, `paradoxStore`, etc.) pour assurer la transmission automatique des tokens Firebase/CSRF et l'unification des messages d'erreur..
- [ ] **Dépréciations Pydantic V2 :** Mettre à jour les modèles héritant de Pydantic V1 (comme `PersonalizationSchema` dans `social.py`) vers la syntaxe standard `ConfigDict`.
- [ ] **Correction de sync-api.bat :** Aligner le chemin de sortie de génération des types OpenAPI dans `sync-api.bat` sur `src\types\api.d.ts`.

---

## 🚀 Expansion & Futur
- [ ] **Rapports de Conformité :** Automatiser les rapports hebdomadaires de conformité sécurité.
---
*Dernière mise à jour : 19 Juin 2026*
