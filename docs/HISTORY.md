# Animetix - Historique des Refactorisations et Succès

Ce document archive les étapes majeures de l'évolution technique du projet.

## [2026-06-03] Session : Migration vectorielle ChromaDB vers pgvector (Cloud SQL)
- **Migration PostgreSQL pgvector** : Remplacement de ChromaDB par l'extension native `pgvector` de PostgreSQL (Cloud SQL) pour centraliser la persistance RAG en environnement serverless.
- **Approche hybride (SQLite Fallback)** : Développement d'un adaptateur et d'un client `PGVectorField` / `VectorRecord` personnalisés basculant de pgvector (PostgreSQL) en production vers un stockage texte + calcul de similarité NumPy en local et pendant les tests.
- **Client compatible** : Réécriture de `pipeline/chroma_client.py` pour émuler le client ChromaDB, assurant la compatibilité immédiate et sans modification de l'ensemble des scripts de pipeline d'ingestion.
- **Nettoyage architectural** : Suppression complète du conteneur et de la dépendance `chromadb` de `requirements.txt` et `docker-compose.yml`. Mise à niveau de l'image Postgres vers `pgvector/pgvector:pg16` en développement local.

## [2026-06-03] Session : Tâches planifiées avec Cloud Run Jobs & Cloud Scheduler
- **Sécurisation via Google Secret Manager** : Configuration de Cloud Run pour injecter les secrets et clés d'API (TMDB, IGDB, Hugging Face, Django Secret Key) depuis Secret Manager au lieu d'utiliser des fichiers `.env` en production.
- **Automatisation & ETL** : Création et configuration d'un job Cloud Run (`animetix-sync-catalog`) exécutant la commande de maintenance `python backend/api/manage.py sync_catalog` en production.
- **Planification Temporelle** : Mise en place d'un déclencheur Cloud Scheduler (`animetix-sync-catalog-trigger`) déployé en région proche (`europe-west1`) configuré pour invoquer le job via une requête HTTP POST authentifiée par OIDC/OAuth chaque jour à 2h00 du matin (Heure de Paris).
- **Script de Déploiement** : Écriture d'un script d'automatisation Python résilient (`scripts/deploy/deploy_jobs.py`) qui active les API nécessaires, configure le job (variables d'environnement, secrets GCP Secret Manager, connecteur VPC pour l'accès privé Cloud SQL/Redis) et crée le scheduler de manière idempotente.
- **Optimisation de Performance (Transactions)** : Optimisation de la commande Django `sync_catalog` en décorant la méthode `handle` avec `@transaction.atomic`. La synchronisation de ~45 000 éléments médias passe d'un comportement d'auto-commit unitaire (qui provoquait des timeouts après 10 minutes) à une transaction unique, exécutée et validée avec succès en 7 minutes et 2 secondes.
- **Intégration du Contexte Docker** : Ajustement de `.gcloudignore` pour lever l'ignorance sur `data/processed` et `data/artifacts`, permettant d'inclure correctement les fichiers de données JSON compilés dans le conteneur de production lors des builds GCP Cloud Build.

## [2026-06-03] Session : Intégration GCS & Persistance de la Forge & Migration BDD Cloud SQL
- **Stockage Cloud (Google Cloud Storage)** : Configuration de `django-storages` avec le backend `GoogleCloudStorage` en production (activé dynamiquement via la variable d'environnement `GS_BUCKET_NAME`) et maintien du stockage local `FileSystemStorage` pour le développement local.
- **Persistance Creative Fusion** : Résolution du bug où les résultats asynchrones des fusions (les images encodées en base64 Data URIs) n'étaient pas persistés dans la base de données. Implémentation du décodage base64 et de la sauvegarde des images sous forme de fichiers via l'API unifiée `default_storage`.
- **Intégration Google Cloud SQL (PostgreSQL)** : Configuration dynamique des paramètres de base de données dans `settings.py` pour détecter automatiquement les connexions par socket Unix (propres à GCP Cloud SQL sur Cloud Run) et désactiver l'application de `sslmode='require'` (incompatible avec les sockets Unix) tout en la maintenant pour les connexions TCP standard.
- **Tests d'Intégration** :
  - Création et passage de tests d'intégration dans `test_gcs_integration.py` pour le cycle de vie d'écriture/lecture de fichiers et le comportement de la vue de statut d'Archetypist.
  - Création et passage de tests unitaires dans `test_db_config.py` validant le comportement de parsing dynamique de `DATABASE_URL` pour les configurations TCP et Unix.

## [2026-06-02] Session : Inférence SOTA, Nettoyage des Bouchons, Guardrails Homogènes et Curation IA
- **Migration Google GenAI (Gemini 3.5 Flash / Vertex AI)** : Création de `GoogleGenAIAdapter` implémentant `InferencePort` avec support d'authentification hybride (Developer API et Vertex AI ADC), gestion native des réponses structurées Pydantic, extraction des logprobs depuis `logprobs_result` pour la perplexité, et intégration multimodale (génération de description d'image et visual rerank) avec tests unitaires complets.
- **Diagnostics & Incertitude Avancés (Logprobs)** : Migration des calculs d'incertitude (Shannon entropy, perplexité, confiance) basés sur le texte vers une exploitation réelle en O(1) des `logprobs` réels en cache fournis par la BrainAPI et Ollama.
- **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Suppression complète de `InferenceNotImplementedError` sur les 29 endpoints d' `InferencePort` en orchestrant et en résolvant proprement les mixins de vision et d'audio via la Method Resolution Order (MRO).
- **Modération de Contenu Homogène (Guardrails)** : Généralisation de la modération sémantique s'exécutant sur le LLM à tous les adaptateurs de texte (`LocalTextAdapter`, `Qwen3VLAdapter`, `UnifiedInferenceAdapter`) via le port parent, intégrant un fallback par mots-clés performant en cas de défaillance.
- **Tests & Qualité** : Automatisation des tests d'évaluation continue (Ragas) pour la fidélité et l'absence d'hallucinations via `ragas_eval_service.py` pour valider les métriques de `AIREvalResult`.
- **Intégrations & Pages Frontend complétées** : 
    - Pages d'authentification et d'onboarding, AccountSettingsPage, ClubEventPage avec participation réelle et countdown.
    - Flux de notifications temps réel avec store Zustand et WebSockets.
    - Historique des Feedbacks IA (AIFeedback).
    - Intégration du mode `VsBattle` (Arena Ultimatum), de l'accès World Boss et du Blindtest sur la Home.
    - Création de la page Cinematic Volumetric Reconstruction (3D dynamique) et du Dashboard SOTA Benchmarking.
- **Fonctionnalités IA & Jeux** : Lobby de Duel temps réel (/duel/lobby/), Explorateur de Catalogue /explore/, Dashboard de Curation des Données pour l'Admin, Hyper-Personnalisation dynamique avec auras réactives basées sur "Archetype Drift".
- **Innovation & Curation** :
    - Déploiement du Visual Graph Debugger pour la correction manuelle des conflits de lore Neo4j via `GraphHealerService`.
    - Implémentation de la page de gestion Neuro-Symbolique de la mémoire (règles Z3 déduites du profil).
- **Sécurité et Résilience** : 
    - **Suppression des Secrets par Défaut (Hardened)** : Élimination de tous les fallbacks de clés API en dur dans le code. Validation centralisée dans `settings.py` via `ImproperlyConfigured` en production et blocage du démarrage du service Brain API sans clé sécurisée.
    - **Isolation Réseau SOTA** : Retrait total de l'exposition des ports de base de données (Postgres, Redis, Chroma, Neo4j) et d'inférence (Ollama) sur l'hôte host. Les services communiquent désormais exclusivement via le réseau virtuel Docker, éliminant les vecteurs d'accès direct non autorisés.
    - **Durcissement SSRF Interne** : Refactorisation de `is_safe_url` pour imposer une liste blanche stricte (`ALLOWED_INTERNAL_HOSTS`) des services Docker autorisés. Même avec `allow_internal=True`, l'accès direct aux IPs privées non-résolues via hostname autorisé est désormais bloqué, empêchant le scan du réseau interne.
    - **Protection contre l'Empoisonnement de Modèle (STaR)** : Implémentation d'une boucle de validation humaine obligatoire (Human-in-the-Loop) pour le framework Self-Taught Reasoner. Les traces générées sont désormais stockées en base (is_validated=False) au lieu d'être directement écrites dans le dataset de Fine-Tuning, empêchant le "Model Collapse" ou l'apprentissage de biais.
    - Sécurisation de la Brain API via `X-API-Key`.
    - Mitigation Prompt Injection et affinage de la CSP (retrait de `'unsafe-eval'`).
    - Systématisation de la sanitisation des sorties IA (`sanitize_ai`/`bleach`).
    - Rate limiting sur `MediaSearchView` et protection contre le Mass Assignment dans `CreativeFusionSerializer`.

## [2026-06-01] Session : Refactoring SOTA, Caching Anti-DoS, Recherche 100% API et Purge XState
- **Simplification & Harmonisation de l'Architecture (Post-Audit)** : Purge des dépendances obsolètes (`ollama`, `google-ai-generativelanguage` et `umap-learn`) de `requirements.txt`. Purge de la bibliothèque `three` (redondante) de `package.json` car déjà encapsulée par `@google/model-viewer`. Sécurisation de `synthetic_gold_generator.py` en migrant de `urllib` vers `safe_http_request` (protection SSRF). Renommage complet de `DuckDuckGoSearchAdapter` en `UnifiedWebSearchAdapter` pour refléter ses capacités hybrides de recherche (Tavily et Google Search Grounding).
- **Nettoyage et Épuration des Dépendances** : Purge physique de la dépendance frontend redondante `plotly.js-dist-min` du `package.json` et suppression des paquets backend inutilisés ou en conflit (`safehttpx` et `environ` au profit exclusif de `django-environ`) dans `requirements.txt`.
- **Stabilisation de la Recherche Web** : Remplacement du scraping DuckDuckGo instable par un adaptateur de recherche web unifié résilient (Tavily Search API & Google Search Grounding via Gemini) et purge physique complète de la bibliothèque `duckduckgo_search`.
- **Simplification d'État Frontend (XState ➡️ Zustand)** : Refactorisation complète des machines de jeux du dossier `/machines` en stores Zustand légers et fluides, et désinstallation définitive de `xstate` et `@xstate/react` du package.json.
- **Optimisation Anti-DoS (Middleware)** : Mise en cache robuste pour 15 minutes des calculs complexes d'Archetype Drift de `PersonalizationMiddleware` afin d'éliminer les pics de requêtes SQLite/Neo4j répétées.
- **Lobby de Duel & Matchmaking PvP** : Implémentation du matchmaking PvP temps réel en WebSockets avec Arena interactive, scores et duels 1v1.
- **Explorateur de Catalogue (Media Browser)** : Déploiement de l'interface immersive ExplorePage pour la recommandation par catégories.
- **Dashboard de Curation IA** : Déploiement du dashboard d'administration de curation des données pour les correcteurs IA.
- **Authentification & Onboarding** : Intégration des flux et des interfaces d'enregistrement / de login avec le store global `authStore`.
- **Gestion de Compte & Profil** : Implémentation complète de la configuration utilisateur, du tier d'abonnement et de la génération sécurisée des jetons d'API.
- **Hyper-Personnalisation Graphique** : Couplage de la détection de dérive d'archétype avec des auras réactives `DynamicAuraWrapper` et du panneau de configuration de style.
- **Sécurisation & Résilience** : Intégration du rate-limiting on ChromaDB (`MediaSearchView`) et blocage des assignations en masse illégitimes dans le `CreativeFusionSerializer`.

## [2026-06-01] Session : Duel Arena & Real-time PvP
- **Matchmaking Engine :** Implémentation du `MatchmakingView` et du système de codes de salon privés pour les duels 1v1.
- **Duel Consumer :** Activation du WebSocket Consumer gérant les échanges de "guesses" et la synchronisation de l'état de jeu en temps réel.
- **Frontend Arena :** Déploiement de `DuelArenaPage.tsx` avec affichage "VS", logs de combat et feedback visuel des victoires.

## [2026-06-01] Session : Explore & Curation Dashboard
- **Media Explore API :** Création d'un endpoint dynamique extrayant les tendances et les catégories (Action, Romance...) du catalogue média.
- **Interface Netflix-like :** Implémentation de `ExplorePage.tsx` avec Hero section immersive et défilement horizontal par catégories.
- **Admin Curation :** Déploiement d'un dashboard de curation (`CurationDashboard.tsx`) permettant de valider les corrections structurelles suggérées par les agents IA Healers.

## [2026-06-01] Session : World Boss
- **World Boss API :** Création des vues `ActiveWorldBossView` et `WorldBossAttackView` gérant le cycle de vie des boss globaux.
- **Frontend Immersion :** Implémentation de `WorldBossPage.tsx` avec barre de vie dynamique et indices communautaires.

## [2026-06-01] Session : Flux Temps Réel & Optimisation Frontend
- **Notifications Temps Réel (WebSockets) :** Intégration complète d'un système de notification asynchrone via Django Channels. Un `NotificationConsumer` pousse instantanément les événements (succès d'amis, alertes système) vers les clients connectés. Côté React, un `useNotificationStore` (Zustand) maintient la connexion WebSocket, affiche des Toasts dynamiques et invalide le cache React Query en temps réel.
- **Migration d'État (Zustand) :** Refactorisation des jeux (Akinetix, Blindtest, Vision, Paradox) pour remplacer les machines XState lourdes par des stores Zustand légers, améliorant la performance et réduisant le bundle size.
- **Historique des Sessions de Jeu :** Implémentation du composant `GameHistoryPanel` sur la page de profil. Le backend expose désormais l'historique détaillé des parties (`GameplaySession`), permettant à l'utilisateur de revoir ses performances passées, les victoires/défaites, et les modes de jeu joués.

## [2026-05-31] Session : Audit Avancé de Sécurité
- **Prévention DoS (OOM)** : Configuration de `DATA_UPLOAD_MAX_MEMORY_SIZE` (50Mo) dans Django.
- **Validation MIME-Type Stricte** : Intégration de la librairie `filetype`.
- **Protection CSRF Cross-Domain** : Résolution de la vulnérabilité liée au cookie `SameSite=None`.
- **Sanitization JSON (Anti-XSS/NoSQL)** : Protection du profil utilisateur via Pydantic strict.
- **Prévention IDOR sur les Fusions** : Filtrage dynamique des querysets dans `CreativeFusionViewSet`.

## [2026-05-31] Session : Sécurité Complète et Intégrations SOTA
- **Audit de Dépendances Continu** : Automatisation du scan de vulnérabilités via Dependabot.
- **Protection SSRF** : Remplacement massif de l'usage direct de `httpx` par `safe_http_request`.
- **Renforcement des Guardrails IA** : Mise en place de sentinelles Input/Output.
- **Nouvelles Interfaces SOTA (Nexus Series)** : Déploiement de multiples UI expertes (MCTS, Z3 Logic, Swarm...).

## [2026-05-30] Session : Hyper-Personnalisation Graphique 100%
- **Moteur d'Archetype Drift (Backend) :** Implémentation du `ArchetypeDriftService`.
- **Infrastructure de Style Dynamique (Frontend) :** Création du `personalizationStore` (Zustand).
- **Auras et Effets Visuels :** Déploiement du composant `DynamicAuraWrapper`.

...
