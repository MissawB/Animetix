# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## 🏗️ Dette Technique & Architecture

### 🎨 Frontend (Assainissement Linter - ~350 problèmes restants)

- [x] **Stabilisation Initiale :** Correction de `Math.random()`, `set-state-in-effect` (coeur), et accès avant déclaration.
- [x] **Typage Strict :** Élimination massive du type `any` dans les services, stores et pages métier (Couverture > 95%).
- [x] **TypeScript & Qualité (Priorité Haute) :**
    - [x] Éliminer les occurrences résiduelles de `any` dans les tests et intégrations SDK tierces.
    - [ ] Nettoyer les variables et imports inutilisés restants (`@typescript-eslint/no-unused-vars`).
- [x] **Accessibilité (Conformité WCAG) :** Finalisation de la première passe de mise en conformité des interactions clavier et des rôles ARIA.

---

## ✨ Fonctionnalités Manquantes (Expérience Utilisateur)

- [ ] **Catalogue de la Galerie Multivers (Multiverse Gallery) :**
    - Implémenter une véritable page "Catalogue" (grille/liste) avec filtres et recherche pour explorer les univers synthétiques générés par la communauté.
- [ ] **Boutique d'Actifs Digitaux (Market/Trading) :**
    - Créer une page de type "Shop" ou "Marketplace" dédiée à l'achat/vente et à l'échange d'actifs digitaux.

---

## 🚀 Expansion & Futur
- [ ] **Déploiement Multi-Régions :** Préparer les scripts d'infrastructure pour un déploiement sur plusieurs régions Google Cloud.
- [ ] **Rapports de Conformité :** Automatiser les rapports hebdomadaires de conformité sécurité.

---
*Dernière mise à jour : 16 Juin 2026*
