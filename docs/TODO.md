# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture (Inférence)

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [ ] **Suppression de la dépendance LangChain** : Supprimer ou bypasser LangChain via l'héritage direct de `BaseRagasLLM` pour Ragas. Permet d'alléger l'environnement virtuel et d'éliminer les conflits de versions.
- [ ] **Migration Dagster ➡️ Celery** : Migrer le DAG de données (`dagster_app.py`) vers des workflows Celery (Chains/Groups) et Celery Beat pour fermer le serveur et le démon Dagster, libérant ainsi de la RAM.
- [ ] **Stabilisation de la recherche Web (DuckDuckGo ➡️ Gemini Grounding / Tavily)** : Remplacer le scraping DuckDuckGo instable par l'outil natif de Google Search Grounding (Gemini) ou une API structurée comme Tavily.
- [ ] **Simplification d'état Frontend (XState ➡️ Zustand)** : Refactoriser les machines d'état simples du dossier `/machines` en stores Zustand plus légers et fluides, réduisant la taille du bundle et le boilerplate.

## 🧬 Fonctionnalités SOTA & Innovations

- [x] **Simulations Cognitives** : Interconnecter le `SynapticPlasticitySimulator` (Heure de Hebb/STDP) et le `QuantumCognitivePreferenceModel` au pipeline de RAG réel. L'historique conceptuel de l'utilisateur doit influencer dynamiquement les scores de pertinence du reranker. (FAIT, modèles interconnectés via AdvancedRAGService et mis à jour par RAGWorkflowManager).
- [x] **Génération 3D & Dioramas** : Remplacer les stubs par une intégration réelle de **Gaussian Splatting** ou de reconstruction volumétrique pour transformer des images d'anime en scènes 3D immersives. (FAIT, intégration API Tripo3D et viewer React implémentés).
- [x] **Vidéo-RAG (Embeddings Temporels)** : Implémenter l'extraction d'embeddings temporels via Qwen2-VL pour permettre une recherche sémantique précise à l'intérieur de clips vidéo. (FAIT, infrastructure Celery et segmentation par segments temporels activées).
- [ ] **Hyper-Personnalisation Graphique** : Implémenter une personnalisation dynamique de l'interface basée sur le "Archetype Drift" de l'utilisateur (couleurs et thèmes changeant selon les affinités détectées).

## 🖥️ Pages Frontend Manquantes (Dette UI)

- [x] **Fiche Détail Média** : Créer la page dynamique `/media/:type/:id/` pour afficher les synopsis, personnages et Seiyuu (API `/api/v1/media/`). (FAIT, MediaDetailPage implémentée avec Knowledge Graph context).
- [x] **Galerie Communautaire (Fusion Feed)** : Interface pour découvrir et liker les fusions créées par les autres membres (API `/api/v1/fusions/`). (FAIT, CommunityFeedPage implémentée avec système de likes).
- [x] **Recherche Globale & Résultats** : Créer une page de résultats complète `/search?q=...` classée par catégories (Anime, Manga, Personnages). (FAIT, SearchResultsPage avec filtrage et navigation Navbar implémentée).
- [x] **Companion Chat Hub** : Page `/companion/chat/` dédiée à l'immersion narrative longue durée avec le compagnon IA. (FAIT, CompanionChatPage implémentée avec sélection de mentors et synchronisation d'overlay).
- [x] **Hub des Laboratoires** : Création de `LabHubPage.tsx` pour centraliser l'accès à tous les modules expérimentaux (Video, Spatial, Manga, Audio, Singularity).
- [x] **Video Lab** : Création de `VideoLabPage.tsx` pour l'interface de transfert de style FateZero.
- [x] **Soundscape Lab** : Création de `SoundscapeLabPage.tsx` pour la génération d'ambiances sonores (API `/api/v1/labs/soundscape/`). (FAIT, interface AudioLDM synchronisée).
- [x] **Speech-to-Speech Lab** : Interface pour l'interaction vocale E2E (API `/api/v1/labs/s2s/`). (FAIT, interface native Moshi implémentée avec enregistrement micro).
- [x] **Interface MLOps & Curation DPO** : Créer un dashboard administrateur pour la validation manuelle des paires de préférence IA (API `/api/v1/mlops/dpo/curation/`). (FAIT, MLOpsDashboard et AdminDPOPage intégrés).
- [x] **Tableau de bord de Transparence (Drift)** : Compléter la page existante pour afficher les rapports de dérive des embeddings et la santé du Knowledge Graph. (FAIT, contrôles admins et visualisations Drift/Graph intégrés).
- [x] **Accessibilité des Préférences** : Ajouter des liens vers `CustomConfigPage.tsx` dans le profil utilisateur pour permettre la personnalisation réelle de l'expérience. (FAIT, navigation Profil ➡️ Configuration IA active).
- [x] **Games Hub** : Créer la page `/games/hub/` pour centraliser tous les jeux IA (Emoji, Blindtest, Vision, Paradox, etc.) avec système de récompenses. (FAIT, GamesHubPage implémentée avec navigation Navbar unifiée).
- [x] **Bibliothèque de Visual Novels (Theater)** : Créer la page `/theater/` pour parcourir et rejouer les VN générés par la communauté via La Forge. (FAIT, TheaterPage implémentée avec filtrage des fusions possédant un script VN).
- [x] **Arène de Duel (Versus Battle Arena)** : Améliorer `/game/vsbattle/` pour inclure un historique des combats publics et un système de vote communautaire. (FAIT, Arena Ultimatum implémentée avec persistance des duels et live feed).
- [ ] **Tableau de Bord Akinetix RL** : Page explicitive sur l'entraînement par renforcement de l'IA lors des sessions Akinetix Expert.

## 🛡️ Sécurité & Résilience (Post-Audit 2026)

- [x] **Remédiation SSRF (Proxy & Labs)** : Désactiver les redirections automatiques (`follow_redirects=False`) dans `httpx` ou valider l'URL finale après chaque saut pour les endpoints utilisant des URLs externes (`image_proxy_view`, `SpatialLabDataView`, etc.). (FAIT - Désactivation des redirections et validation appliquées).
- [ ] **Hachage des Clés API Utilisateur** : Migrer le stockage des clés API dans le modèle `Profile` vers un format haché (type `make_password`) au lieu du texte clair actuel.
- [ ] **Renforcement du Sandboxing IA** : Isoler l'exécution du code généré par le `DynamicToolAgent` dans un environnement plus strict (ex: gVisor, conteneur éphémère ou worker isolé sans accès réseau) pour limiter les risques de RCE via `exec()`.
- [ ] **Durcissement des Headers & SSL** : Activer `SECURE_HSTS_SECONDS` et forcer `SECURE_SSL_REDIRECT` dans la configuration de production. Désactiver `BasicAuthentication` dans `REST_FRAMEWORK` au profit de tokens plus sécurisés.
- [ ] **Sécurisation du Mode Développement** : Restreindre `ALLOWED_HOSTS` en développement et s'assurer qu'aucune `SECRET_KEY` par défaut n'est réutilisée dans des environnements de pré-production ou staging.
- [x] **Déploiement des Guardrails** : Intégrer systématiquement `GuardrailService` avant chaque appel à un `InferencePort` dans la couche de présentation API. (FAIT - Appliqué sur les endpoints critiques).
- [x] **Protection contre l'Inference Abuse** : Implémenter un rate-limiting strict par utilisateur authentifié et restreindre l'accès anonyme aux fonctionnalités d'IA lourdes. (FAIT - Authentification forcée + Quotas via UsagePort intégrés).
- [x] **Sécurisation des Flux Infra** : Renforcer la protection SSRF dans les communications Backend-to-BrainAPI et valider strictement les URLs externes. (FAIT - Centralisation de `is_safe_url` et filtrage systématique appliqués).
- [x] **Audit d'Injection Cypher (Neo4j)** : Étendre la validation `sanitize_cypher_identifier` à l'ensemble des propriétés dynamiques injectées. (FAIT - Regex stricte + Whitelist et gestion sécurisée des relations IA implémentées).
- [x] **Cloisonnement des Métriques & Docs** : Restreindre l'accès aux endpoints `/metrics/` et `/api/docs/` aux administrateurs. (FAIT - Décorateur `staff_member_required` appliqué).
- [x] **Conformité & PII (Sentry)** : Désactiver `send_default_pii` dans la configuration Sentry. (FAIT - Respect RGPD activé).
- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
