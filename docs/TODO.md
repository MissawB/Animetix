# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger.

---

## 🚨 Urgences & Incohérences Détectées (Analyse du 13/06/2026)

### 🛰️ Routage & Accessibilité
- [ ] **Routage GraphNeighborhood :** Ajouter la route `/graph/neighborhood/` dans `GraphRoutes.tsx` (Page existante mais isolée du routeur).
- [ ] **Routage PowerStation :** Router `/power-station/` vers `PowerStationPage.tsx` et mettre à jour les liens (Navbar/Pricing) pour remplacer la page "Legacy" de pricing.

### 🧪 Lab & IA (Frontend -> Backend)
- [ ] **Mise à jour API Manga Lab :** Corriger `MangaLabPage.tsx` pour utiliser les endpoints réels `/api/v1/manga-lab/clean/` et `/api/v1/manga-lab/translate/` (Actuellement en 404).
- [x] **Connexion Video-RAG UI :** Lier les composants `Timeline` et `Inspector` de `VideoRagPage.tsx` aux services réels de recherche vectorielle (`VideoRAGSearchView`).

### 🏗️ Architecture & Données
- [ ] **Modèles Manga Backend :** Implémenter le modèle `Chapter` (ou `MangaPage`) dans `backend/api/animetix/models.py` pour alimenter le `MangaReader` avec de vraies données.
- [ ] **UI Indexation Vidéo :** Créer une interface d'upload et d'indexation pour le Video-RAG (Fonctionnalité backend présente mais orpheline d'UI).
- [ ] **Wiki Marché Japonais :** Créer une page de visualisation/Wiki pour explorer les données éditeurs/diffuseurs japonais intégrées via le pipeline MLOps.

---

## 🛠️ Dette Technique & Architecture (Prioritaire)

### 🧹 Nettoyage des erreurs ESLint et Typage
- [ ] **Résoudre les 607 problèmes du linter frontend** :
  - [x] **Généralisation du typage :** Hardening des stores (`akinetix`, `blindtest`, `vision`, `paradox`), des services (`animinator`, `codemanga`, `audioLab`) et des composants critiques (`XaiReportDisplay`, `XaiReportViewer`) via les types générés.
  - [x] Remplacer l'utilisation abusive du type `any` par des types/interfaces TypeScript adéquats (ex: [CustomConfigPage.tsx](frontend/src/pages/utils/CustomConfigPage.tsx)).
  - [x] Corriger la mise à jour synchrone d'état React dans l'effet de [CustomConfigPage.tsx](frontend/src/pages/utils/CustomConfigPage.tsx).
  - [x] Corriger les caractères d'espacement irréguliers dans le fichier de typages généré [api.d.ts](frontend/src/types/api.d.ts).

### 🏗️ Refactorisation Core & Robustesse
- [x] **Finaliser la migration du RAG Workflow**
- [ ] **Gestion des Erreurs Backend :** Identifier et supprimer les blocs `except: pass` silencieux dans les adaptateurs (`google_genai_adapter.py`, `image_gen_mixin.py`, etc.) pour restaurer la visibilité des erreurs d'API.
- [ ] **Complétion des Ports :** Implémenter les méthodes d'interface encore vides (`pass`) dans les ports `AchievementPort` et `EvalPort` pour finaliser les intégrations.
- [ ] **Revue de Sécurité SQL (NL Query) :** Audit approfondi de `sql_guard.py` pour garantir l'étanchéité totale contre les injections SQL sur les requêtes en langage naturel.

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
- [x] **Exécuter le plan de nettoyage a11y** ([2026-06-09-frontend-a11y-cleanup.md](docs/superpowers/plans/2026-06-09-frontend-a11y-cleanup.md)) :
  - Associer correctement les labels et contrôles de formulaires sur les pages d'authentification, de support et de social.
  - Ajouter les écouteurs d'événements clavier (`onKeyDown`) et les rôles ARIA sur les composants interactifs non natifs (ex: cartes cliquables, éléments de Navbar).
  - Ajouter des pistes de sous-titres (`<track>`) sur les lecteurs de média.

---

## ⚙️ MLOps et Qualité des Données
- [x] **Contrôle de qualité via dbt** : Mettre en place des tests de qualité de données (schémas, doublons, intégrité référentielle) au niveau SQL avant l'entraînement.
- [x] **Orchestration Apache Beam scalable** : Migrer l'ingestion vers [lore_ingestion_beam.py](backend/pipeline/mlops/lore_ingestion_beam.py) exécuté sur Dataflow pour la robustesse et la scalabilité.
- [ ] **Phase L.2 - Multimodal SFT (Axe A)** : Indexation et génération de paires d'entraînement images/vidéos + texte (mangas, animes) pour fine-tuner le modèle expert sur les capacités vision-langage.

---

## 🎨 Interface & Expérience Utilisateur

### 📊 Suivi & Contrôle
- [x] **Démocratisation Totale (Zéro Paywall)** : Suppression de toutes les restrictions "Premium" sur le site. Toutes les fonctionnalités IA sont désormais gratuites.
- [x] **Économie Circulaire des Berrix (Bx)** : Implémentation du système de jetons financés par les "Rewarded Ads" (recharge active et minage passif).
- [x] **Tableau de Bord des Berrix (Bx)** : Création de la page `/pricing/` (Power Station) pour le suivi du portefeuille et la recharge énergétique.
- [x] **Portail Développeur Dédié** : Sortir la gestion des clés API de la page "Compte" pour créer un espace dédié avec documentation rapide et suivi de consommation technique.
  - *Fix: DeveloperPortalPage implémenté (/developer/) incluant la gestion sécurisée des clés atx_..., des snippets de code interactifs et un dashboard de santé système.*

### 🧩 Exploration & Immersion
- [x] **Explorateur de Voisinage de Graphe (Ouvert)** : Déploiement de la page `/graph/neighborhood` accessible à tous pour la visualisation profonde des connexions.
- [x] **Lecteur de Manga Immersif** : Composant de lecture fluide pour les planches traitées (Manga Lab) intégré.
- [x] **Carte Interactive Seichijunrei** : Transformer la liste des lieux de pèlerinage en une véritable carte géographique interactive.
  - *Fix: Scraper mis à jour avec géolocalisation, API SeichijunreiMapView créée, et page interactive déployée via Plotly.js.*
- [x] **Hub Unifié "Singularity Command Center"** : Centraliser les expériences IA dans une interface de monitoring unique.
  - *Fix: API SingularityCommandCenterView agrégée, Hub de monitoring temps réel Plotly/Framer-motion déployé.*

### 🚀 Nouvelles Pages Dédiées (Manquantes)
- [x] **Lecteur de Manga Immersif (`MangaReader`)** : Créer une page de lecture dédiée (`/media/manga/:mangaId/:chapterId/`) utilisant la feature `manga-reader`.
  - *Fix: Page MangaReaderPage implémentée, store mis à jour avec gestion des pages, et navigation intégrée à la fiche média.*
- [x] **Galerie des Créations 3D / Dioramas** : Page permettant aux utilisateurs de retrouver et visualiser leurs reconstructions spatiales (SGS) et cinématographiques (DCS) générées.
  - *Fix: Page DioramaGalleryPage implémentée avec filtrage, navigation et intégration au Lab Spatial.*
- [x] **Fiches Détaillées Personnages & Staff** : Implémenter des pages de profil pour les personnages et les créateurs (seiyuu, studios, auteurs) avec intégration du Knowledge Graph.
  - *Fix: Pages CharacterDetailPage et StaffDetailPage implémentées avec support des métadonnées étendues (archétypes, filmographies) et mise à jour du routage global.*
- [x] **Hub de Transparence Communautaire IA** : Page affichant l'évolution globale du modèle expert et l'impact des feedbacks de la communauté sur le cerveau d'Animetix.
  - *Fix: TransparencyPage enrichie avec des graphiques d'évolution (Recharts), audit de dérive vectorielle et métriques d'éthique IA. API TransparencyDataView mise à jour pour agréger les données réelles de feedback et du graphe.*
- [x] **Onboarding & Guide Scientifique des Archétypes** : Page pédagogique expliquant les concepts de cognition neuro-symbolique et de profilage logique de manière accessible.
  - *Fix: ArchetypeGuidePage implémentée avec une narration visuelle sur le cycle cognitif, le profilage logique (engrammes) et les moteurs d'expérience (Z3, PPO).*

---

## 🏗️ Optimisation des Coûts & Infrastructure
- [x] **Stratégie "Local-First"** : Priorisation des modèles SLM locaux (Qwen2.5) avant le repli vers les APIs payantes.
- [x] **Instances GPU Spot** : Configuration Docker & Cloud prête pour le déploiement sur des instances préemptibles (-70% de coût).
- [ ] **Caching Sémantique RAG** : Implémenter une couche de cache sémantique via similarité vectorielle pour éviter de recalculer les requêtes RAG identiques.


---

## 📡 Observabilité & Alerting
- [x] **Recalibrage des Alertes de Dérive** : Ajuster les seuils de l' `AlertService` pour la détection de dérive sémantique du profil utilisateur afin de minimiser les faux positifs.
  - *Fix: AlertService restauré et centralisé. Seuils recalibrés (KS-test à 0.01, Knowledge drift à 0.40).*
