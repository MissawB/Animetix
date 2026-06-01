# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [ ] **Stabilisation de la recherche Web (DuckDuckGo ➡️ Gemini Grounding / Tavily)** : Remplacer le scraping DuckDuckGo instable par l'outil natif de Google Search Grounding (Gemini) ou une API structurée comme Tavily.
- [ ] **Simplification d'état Frontend (XState ➡️ Zustand)** : Refactoriser les machines d'état simples du dossier `/machines` en stores Zustand plus légers et fluides, réduisant la taille du bundle et le boilerplate.

## 🚀 Intégrations & Pages Manquantes

- [ ] **World Boss / Global Boss UI** : Créer l'interface épique (`/game/world-boss/`) pour afficher les boss globaux, leurs phases, et permettre la participation communautaire.
- [ ] **Page de Soutien / Wall of Fame** : Ajouter une page (`/support/` ou `/donate/`) pour valoriser les donateurs, expliquer le modèle économique et lier les plateformes (Patreon/Ko-fi).
- [ ] **Lobby de Duel (Matchmaking & Ranked)** : Implémenter un hub de duel (`/duel/lobby/`) pour créer des salons 1v1, rejoindre via code, ou lancer du matchmaking classé.
- [ ] **Explorateur de Catalogue (Media Browser)** : Créer une interface "Netflix-like" (`/explore/`) pour parcourir les œuvres par popularité, année ou recommandations, au-delà de la simple recherche.
- [ ] **Dashboard de Curation des Données (Admin)** : Ajouter une interface dans la section Admin pour gérer, valider ou rejeter les `DataCurationTickets` générés par l'IA.
- [ ] **Restauration de la Navigation (Hubs)** :
    - [ ] Réintégrer **Animinator**, **Undercover** et **Akinetix Classic** dans le `GamesHubPage`.

## 🧬 Fonctionnalités SOTA & Innovations

- [ ] **Hyper-Personnalisation Graphique** : Implémenter une personnalisation dynamique de l'interface basée sur le "Archetype Drift" de l'utilisateur (couleurs et thèmes changeant selon les affinités détectées).

## 🛡️ Sécurité & Résilience (Post-Audit 2026)

- [x] **Protection contre la Triche XP (Offline Sync)** : Sécuriser l'endpoint `sync_offline_data` en ajoutant une signature cryptographique (HMAC) sur les scores ou en limitant drastiquement le gain d'XP journalier synchronisable. (FAIT - Rate limiting 1/5m et plafond journalier de 200 XP appliqués).
- [x] **Généralisation du Helper Anti-SSRF** : Refactoriser `image_proxy_view` et les vues du laboratoire IA pour utiliser systématiquement `safe_http_request` (qui protège contre le DNS Rebinding) au lieu de `httpx` direct. (FAIT - Utilisation systématique du helper sécurisé avec validation des redirections).
- [x] **Implémentation d'une CSP (Content Security Policy)** : Configurer `django-csp` pour limiter les sources de scripts et de ressources, réduisant l'impact potentiel des failles XSS. (FAIT - Politique CSP stricte configurée).
- [ ] **Gestion des Secrets d'Infra** : Supprimer les mots de passe par défaut dans `deploy/docker-compose.yml` et migrer vers une injection systématique via variables d'environnement sécurisées.
- [ ] **Validation de la taille des uploads** : Ajouter une vérification `Content-Length` sur tous les endpoints acceptant des fichiers (Images/Audio/Vidéo) pour prévenir les attaques DoS.
- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
