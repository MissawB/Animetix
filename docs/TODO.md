# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## 🧠 Recherche & Innovation IA

### 🚀 Optimisation du Raisonnement (Inspiré par VibeThinker-3B)
- [x] **Implémentation du "Reasoning Core" Local :** Étudier l'intégration de modèles 3B compacts (type VibeThinker) dans les adaptateurs d'inférence.
    - [x] Créer un `CompactReasoningAdapter` pour décharger les requêtes de niveau 1 et 2 vers des modèles locaux.
    - [x] Réduire la latence du *Paradox Quest* et du *Star Reasoner* via cette compression de paramètres.

### 🎥 Multimodalité Évolutive (Inspiré par VisualClaw)
- [ ] **Système de "Skill Bank" pour Video-RAG :** Implémenter une boucle d'apprentissage auto-évolutive dans `video_language_indexing_service.py`.
    - [ ] Enregistrer les échecs de reconnaissance (actions de combat, styles graphiques) comme "Expériences de Correction".
    - [ ] Utiliser ces expériences pour affiner dynamiquement les prompts du Video-RAG.

### ⚖️ Raffinement du Budget TTC (Inspiré par Nemotron 3 Ultra)
- [ ] **Dynamic Reasoning Budget :** Refondre la logique de `complexity_analyser.py` pour une allocation granulaire du "Thinking Budget".
    - [ ] Passer d'un budget statique à un budget prédictif basé sur la structure sémantique de la requête.

---

## 🚨 Sécurité & Risques Critiques (Priorité Haute)

- [ ] **Audit Formel SQL Guard :** Réaliser le "fuzzing" et la revue de sécurité formelle du parseur `sql_guard.py` (marqué comme HIGH-RISK). Valider contre les injections SQL complexes générées par IA.
- [ ] **Isolation des Secrets :** Vérifier que les logs de `mlops.py` et `DPOFeedbackLoop` ne fuitent pas de métadonnées sensibles lors du fine-tuning.
- [x] **Pipeline de Validation HITL :** Finaliser le "Universal HITL Gate" pour empêcher le "Model Collapse" via une validation croisée systématique.

---

## 🏗️ Dette Technique & Architecture

### 🎨 Frontend (Assainissement Linter - 549 erreurs)
- [ ] **Cycles de Vie React :** Supprimer l'utilisation de `Math.random()` dans les rendus (`AdminDSPyDashboard.tsx`, `CognitionHubPage.tsx`) pour stabiliser l'UI.
- [ ] **Pureté des Effets :** Corriger les erreurs `set-state-in-effect` dans `ClubChat.tsx` et `VNPlayer.tsx` (risques de boucles de rendu).
- [ ] **Typage Strict :** Remplacer systématiquement les types `any` par des interfaces TypeScript rigoureuses conformément aux mandats `GEMINI.md`.
- [ ] **Déclarations :** Résoudre les accès aux fonctions avant déclaration dans `AkinetixRLPage.tsx` et `ExpertNexusPage.tsx`.

### 🧠 Backend & Inférence
- [ ] **Optimisation Boot (Lazy Loading) :** Vérifier et renforcer le chargement paresseux des modèles dans le container DI pour garantir un démarrage serveur < 5s.
- [ ] **Complétion du Port d'Inférence :** 
    - [ ] Implémenter `generate_sprite` réel dans `BrainAPIAdapter` (bloque le Game Engine).
    - [ ] Implémenter `localize_video_actions` et `estimate_depth` pour les Labs Spatiaux.
    - [ ] Remplacer le placeholder statique (`0.5`) de similarité dans `GoogleGenAIAdapter` par un embedding réel.

---

## 🧪 "Ghost Labs" & Fonctionnalités Beta

- [x] **Manga Lab :**
    - [x] Implémenter `inpaint_text_bubbles` pour le nettoyage automatique des pages avant traduction.
    - [x] Finaliser le flux backend `manga_flow.py` pour le chargement dynamique des chapitres et pages (Raccordé à `MangaService`).
- [ ] **Video RAG :** Finaliser l'UI d'indexation temporelle côté Admin et stabiliser le service `video_language_indexing_service.py`.
- [ ] **MLOps Pipeline :** Finaliser les vues API réelles pour le `DPOFeedbackLoop` (actuellement partiellement en stub).
- [ ] **Accessibilité (WCAG) :** Intégrer les tests d'accessibilité automatisés dans le pipeline CI via Playwright.

---

## 🚀 Expansion & Futur
- [ ] **Déploiement Multi-Régions :** Préparer les scripts d'infrastructure pour un déploiement sur plusieurs régions Google Cloud.
- [ ] **Rapports de Conformité :** Automatiser les rapports hebdomadaires de conformité sécurité.

---
*Dernière mise à jour : 16 Juin 2026*

