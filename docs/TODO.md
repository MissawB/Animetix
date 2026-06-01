# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [ ] **Stabilisation de la recherche Web (DuckDuckGo ➡️ Gemini Grounding / Tavily)** : Remplacer le scraping DuckDuckGo instable par l'outil natif de Google Search Grounding (Gemini) ou une API structurée comme Tavily.
- [ ] **Simplification d'état Frontend (XState ➡️ Zustand)** : Refactoriser les machines d'état simples du dossier `/machines` en stores Zustand plus légers et fluides, réduisant la taille du bundle et le boilerplate.

## 🚀 Intégrations & Pages Manquantes

- [ ] **Lobby de Duel (Matchmaking & Ranked)** : Implémenter un hub de duel (`/duel/lobby/`) pour créer des salons 1v1, rejoindre via code, ou lancer du matchmaking classé.
- [ ] **Explorateur de Catalogue (Media Browser)** : Créer une interface "Netflix-like" (`/explore/`) pour parcourir les œuvres par popularité, année ou recommandations, au-delà de la simple recherche.
- [ ] **Dashboard de Curation des Données (Admin)** : Ajouter une interface dans la section Admin pour gérer, valider ou rejeter les `DataCurationTickets` générés par l'IA.
- [ ] **Restauration de la Navigation (Hubs)** :
    - [ ] Réintégrer **Animinator**, **Undercover** et **Akinetix Classic** dans le `GamesHubPage`.

## 🧬 Fonctionnalités SOTA & Innovations

- [ ] **Hyper-Personnalisation Graphique** : Implémenter une personnalisation dynamique de l'interface basée sur le "Archetype Drift" de l'utilisateur (couleurs et thèmes changeant selon les affinités détectées).

## 🛡️ Sécurité & Résilience (Post-Audit Deep-Dive)

- [x] **Remédiation IDOR (Clubs)** : Restreindre la modification et suppression des clubs aux créateurs (`IsCreatorOrReadOnly`) et masquer les clubs privés dans le `get_queryset` global. (FAIT - Permission IsCreatorOrReadOnly et filtrage du queryset implémentés).
- [x] **Optimisation du Middleware (Anti-DoS)** : Mettre en cache le calcul de l'Archetype Drift dans `PersonalizationMiddleware` (ex: cache 15 min par utilisateur) pour éviter de saturer la DB/CPU à chaque requête. (FAIT - Cache de 15 minutes implémenté via django-redis).
- [x] **Sécurisation des Victoires (Akinetix)** : Implémenter une validation croisée entre le choix de l'utilisateur et l'item cible stocké en session pour empêcher le farming d'XP frauduleux. (FAIT - Déclaration obligatoire du personnage cible en cas de victoire utilisateur et blocage des faux négatifs).
- [x] **Quota LLM Arena (VS Battle)** : Appliquer un rate-limit strict et exiger l'authentification pour les combats VS afin de protéger les ressources d'inférence coûteuses. (FAIT - Authentification obligatoire, rate-limit 1/min et quotas journaliers appliqués).
- [ ] **Durcissement du Proxy d'Images** : Intégrer la validation du type MIME binaire (`validate_file_mime_type`) et le contrôle de taille (`MAX_IMAGE_SIZE`) dans `image_proxy_view` pour bloquer les fichiers malveillants masqués.
- [ ] **Rate Limiting sur la Recherche** : Appliquer un rate-limit via `@ratelimit` sur `MediaSearchView` pour protéger ChromaDB et les ressources CPU/GPU contre le scraping intensif.
- [ ] **Protection contre le Mass Assignment (Fusions)** : Sécuriser le `CreativeFusionSerializer` pour empêcher un utilisateur de s'attribuer une fusion créée par un tiers ou de modifier le créateur original via l'API.
- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
