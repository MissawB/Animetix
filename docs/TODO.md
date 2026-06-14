# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🏗️ Refactorisation Core & Robustesse
- [x] **Complétion des Ports :** Implémenter les méthodes d'interface encore vides (`pass`) dans les ports `AchievementPort` et `EvalPort` pour finaliser les intégrations (Note: les adaptateurs Django les implémentent déjà, mais le contrat de port doit être propre).
- [x] **Implement RAG Processors :** Finaliser l'implémentation de `SpeculateProcessor`, `VlmRerankProcessor`, `SynthesizeProcessor`, `JudgeProcessor`, `FallbackRagProcessor`. Mettre à jour le container DI et supprimer définitivement l'ancien `RAGWorkflowManager`.
- [x] **Hardening Text-to-SQL :** Effectuer une revue de sécurité approfondie et des tests de robustesse (fuzzing) sur le parseur `sql_guard.py` pour prévenir les injections complexes.
- [x] **Alignement Dépendances :** Créer le fichier `requirements.in` et migrer vers le workflow `pip-compile` pour respecter le mandat de gestion des dépendances défini dans `GEMINI.md`.
- [x] **Optimisation Boot Backend :** Refactoriser `CoreServicesContainer.py` pour utiliser des imports dynamiques/paresseux à l'intérieur des méthodes, afin de réduire la dette d'importation statique et accélérer le démarrage du serveur.

---

## ⚙️ MLOps et Qualité des Données
- [x] **Optimisation DSPy Contextuelle :** Lier les logs de production (erreurs de raisonnement) directement à l'interface `AdminDSPyDashboard` pour automatiser le cycle de correction des prompts.
- [x] **Gestion des Règles Cognitives :** Implémenter une interface de gestion granulaire pour les règles Neuro-Memory (permettant de révoquer ou d'ajuster le poids de règles spécifiques détectées comme obsolètes ou contradictoires).
- [x] **Dashboard d'Audit Sécurité IA :** Intégrer et lier la page `AISafetyAuditPage` existante dans le `MLOpsDashboard` et la navigation admin pour visualiser les `AISafetyEvent`.
- [x] **Gestionnaire de Tickets de Curation :** Raccorder le système de `DataCurationTicket` à l'interface d'administration (via l'onglet Graph Healer) pour résoudre structurellement les bugs de lore complexes.
- [x] **Observability Backend :** Connecter la page `ObservabilityConsolePage` aux métriques réelles de drift d'archétype et de stabilité de modèle via `ObservabilityView`.
- [ ] **Alerte Drift & Stabilité :** Configurer des alertes critiques dans Prometheus/Grafana pour le drift d'archétype utilisateur et la stabilité des modèles de raisonnement.


---

## 🎨 Interface & Expérience Utilisateur
- [x] **Seiyuu Discovery Lab :** Créer la page dédiée dans le Audio Lab (`/lab/audio/seiyuu/`) pour exposer l'API de recherche de doubleurs déjà opérationnelle.
- [x] **Studio Multivers Unifié :** Fusionner l'expérience utilisateur du `MultiverseLabPage` (Génération) et du `MultiverseGalleryPage` (Exposition) pour un workflow de création fluide.
- [x] **Barre de Navigation Admin :** Unifier l'accès aux pages critiques (`TTCMonitoringPage`, `FinancialDashboardPage`, `UserManagementPage`) dans un dashboard d'administration centralisé.
- [x] **Console de Pilotage Pipelines :** Permettre le déclenchement manuel des tâches backend (sync Neo4j, scrapers) directement depuis `HealthPage`.
- [x] **Audit Macro-Économique Berrix :** Créer un dashboard admin pour suivre les flux de Berrix (inflation, balance revenus pub vs coûts IA) via `WalletTransaction`.
- [ ] **Correction Navigation Admin :** Corriger les liens brisés dans le `MLOpsDashboard` (notamment le lien Transparence pointant vers `/transparency/` au lieu de `/social/transparency/`).
- [ ] **Audit Accessibilité (a11y) :** Réaliser un audit complet de l'accessibilité du frontend selon les standards WCAG en utilisant `@axe-core/playwright`.
- [ ] **Stabilisation "Ghost Labs" :** Finaliser et stabiliser les laboratoires marqués en Beta ou Expérimental (Neural Diagnostics, Synaptic Plasticity, Liquid Neural Networks) pour un passage en état "Operational".
- [x] **Mise à jour Manga Reader :** Connexion au backend réel pour le chargement des chapitres et des pages.
- [x] **UI Indexation Vidéo :** Interface d'upload et d'indexation pour le Video-RAG (Admin).
- [ ] **Mise à jour Roadmap :** Aligner les dates et statuts du `ROADMAP.md` avec l'état d'avancement réel du projet.


---

## 💰 Monétisation & Financement (Ad-Supported)
- [x] **Offres Développeur Payantes (Expert API)** : Mettre en place un système de facturation à la consommation via Stripe Billing pour l'utilisation de l'API (tier `pro`), permettant aux développeurs d'utiliser le moteur RAG d'Animetix dans leurs applications.
  - *Fix: Stripe Metered Billing intégré. Souscription Pro via Checkout, reporting de consommation automatique dans l'adapter d'usage, et portail développeur raccordé aux paiements réels.*
- [x] **Financement Participatif (Dons)** : Ajouter un bouton Ko-fi/Patreon dans l'Espace Sponsors pour permettre aux utilisateurs de soutenir le serveur, en débloquant des cosmétiques exclusifs sur leur profil.
