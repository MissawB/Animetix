# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [x] **Suppression de la dépendance LangChain** : Supprimer ou bypasser LangChain via l'héritage direct de `BaseRagasLLM` pour Ragas. Permet d'alléger l'environnement virtuel et d'éliminer les conflits de versions. (Terminé : Suppression complète de LangChain/Ragas, implémentation d'un juge LLM autonome structuré avec Pydantic et Instructor).
- [ ] **Migration Dagster ➡️ Celery** : Migrer le DAG de données (`dagster_app.py`) vers des workflows Celery (Chains/Groups) et Celery Beat pour fermer le serveur et le démon Dagster, libérant ainsi de la RAM.
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

## 🛡️ Sécurité & Fiabilité (Audit Avancé)

- [x] **Prévention DoS (OOM)** : Configurer `DATA_UPLOAD_MAX_MEMORY_SIZE` dans Django et implémenter un traitement par chunks pour les uploads lourds dans les Labs (Génération 3D, Vidéo). (Terminé : Limite fixée à 50 Mo, fichier > 2.5 Mo sur disque, et utilisation systématique de `.chunks()` au lieu de `.read()`).
- [x] **Validation stricte des fichiers (MIME-Type)** : Vérifier la signature binaire ("Magic Number") des fichiers uploadés (images/vidéos/audio) avant transmission aux moteurs d'inférence pour prévenir les injections malveillantes. (Terminé : Intégration de `filetype` et filtrage strict dans `labs.py` et `core.py`).
- [x] **Protection CSRF (SameSite=None)** : Sécuriser les API REST cross-domain en s'assurant de la validation systématique des tokens CSRF ou en migrant vers une authentification Stateless (JWT) pour pallier les risques liés aux cookies SameSite=None. (Terminé : Suppression de `@csrf_exempt` et activation stricte des Trusted Origins).
- [x] **Sanitization du JSON (XSS/NoSQL)** : Définir un schéma Pydantic ou un Serializer strict pour la validation de `personalization_settings` (Social API) afin de bloquer les payloads malformés ou les injections de scripts. (Terminé : Validation Pydantic stricte avec `extra = "forbid"` sur l'endpoint `update_personalization`).
- [x] **Prévention IDOR (Fusions)** : S'assurer que le queryset global de `CreativeFusionViewSet.remix` empêche l'accès et le "clonage" des fusions privées d'autres utilisateurs. (Terminé : Implémentation d'un `get_queryset` dynamique basé sur `is_public` et le propriétaire).
