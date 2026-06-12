# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

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

### ♿ Accessibilité (a11y)
- [ ] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA on les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## ⚙️ MLOps et Qualité des Données
- [x] **Contrôle de qualité via dbt/Dataform** : Mettre en place des tests de qualité de données (schémas, doublons, intégrité référentielle) au niveau SQL avant l'entraînement.
- [ ] **Orchestration Apache Beam scalable** : Migrer l'ingestion vers [lore_ingestion_beam.py](backend/pipeline/mlops/lore_ingestion_beam.py) exécuté sur Dataflow pour la robustesse et la scalabilité.

