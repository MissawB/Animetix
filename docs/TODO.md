# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [ ] **Suppression de la dépendance LangChain** : Supprimer ou bypasser LangChain via l'héritage direct de `BaseRagasLLM` pour Ragas. Permet d'alléger l'environnement virtuel et d'éliminer les conflits de versions.
- [ ] **Migration Dagster ➡️ Celery** : Migrer le DAG de données (`dagster_app.py`) vers des workflows Celery (Chains/Groups) et Celery Beat pour fermer le serveur et le démon Dagster, libérant ainsi de la RAM.
- [ ] **Stabilisation de la recherche Web (DuckDuckGo ➡️ Gemini Grounding / Tavily)** : Remplacer le scraping DuckDuckGo instable par l'outil natif de Google Search Grounding (Gemini) ou une API structurée comme Tavily.
- [ ] **Simplification d'état Frontend (XState ➡️ Zustand)** : Refactoriser les machines d'état simples du dossier `/machines` en stores Zustand plus légers et fluides, réduisant la taille du bundle et le boilerplate.

## 🧬 Fonctionnalités Non Implémentées

- [ ] **Visualisation du Drift** : Ajouter une vue graphique de l'évolution du profil utilisateur dans l'Archetype Nexus.

## 🎨 UX & Interfaces de Nouvelle Génération (Nexus Series)

- [x] **Expert Nexus (Raisonnement Arborescent)** : Créer une page dédiée visualisant l'arbre de pensée (MCTS/Tree of Thoughts) lors des recherches de lore complexes pour une transparence totale de l'inférence.
- [ ] **Amélioration Expert Nexus** : Passer d'une timeline linéaire à une véritable visualisation arborescente (Graphe/Arbre) pour le raisonnement multi-agents.
- [x] **Archetype Nexus (Mémoire Épisodique & Logique)** : Interface permettant à l'utilisateur de visualiser son profil cognitif et les règles logiques formelles (Z3) déduites de ses préférences.
- [x] **AI Debate Arena (Théorie des Jeux)** : Interface pour orchestrer des débats sémantiques entre agents IA (ex: Goku vs Saitama) basés sur les faits du Knowledge Graph (Self-play/CFR).
- [x] **Visual Nexus (Search Vidéo Sémantique)** : Page de recherche sémantique spécialisée dans l'indexation temporelle des scènes d'anime via Video-LLaVA.
- [x] **Lore World Map (Graph Clustering)** : Visualisation macroscopique des communautés de lore (Leiden) pour explorer la base par thématiques globales plutôt que par titres.
- [x] **Quantum & Swarm Labs** : Étendre le Singularity Lab avec des interfaces pour la modélisation cognitive quantique et le consensus d'essaims d'agents.
- [x] **Live Transparency Dashboard** : Exposer publiquement les métriques de fidélité RAG, la latence réelle et les benchmarks de modèles SOTA (HuggingFace Best).
- [ ] **Benchmarks SOTA (Transparency)** : Implémenter l'affichage réel des benchmarks "HuggingFace Best" dans le Dashboard de Transparence (actuellement absent du composant).

## 🚀 Intégrations & Pages Manquantes

- [ ] **Counterfactual Simulator UI** : Créer une page dédiée pour simuler et visualiser les timelines conversationnelles alternatives ("mondes possibles") basées sur `counterfactual_simulator.py`.
- [ ] **Liquid Neural Network Lab** : Interface pour interagir avec les simulations neuromorphiques dynamiques de flux continus (`liquid_neural_network.py`).
- [ ] **DSPy Optimizer Dashboard** : Interface d'administration pour piloter et visualiser la mutation sémantique des prompts en boucle fermée.
- [ ] **Restauration de la Navigation (Hubs)** :
    - [ ] Réintégrer **Soundscape Lab** et **Speech-to-Speech Lab** dans le `LabHubPage`.
    - [ ] Réintégrer **Animinator**, **Undercover** et **Akinetix Classic** dans le `GamesHubPage`.


## 🛡️ Sécurité & Résilience

- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
- [x] **Sécurisation du Déploiement** : Remplacer les identifiants par défaut (Postgres, Neo4j, Chroma) dans `docker-compose.yml` par des variables d'environnement (`.env`) non commitées. (Terminé : Template .env.example créé, Docker Compose paramétré, Client ChromaDB sécurisé).
- [/] **Protection SSRF (High)** : Désactiver `follow_redirects=True` in `web_search_adapter.py` et les autres adaptateurs effectuant des requêtes externes. Implémenter une validation stricte du saut de redirection. (En cours : Adaptateurs critiques sécurisés via `safe_http_request` - Web, Brain, Jikan, Fandom, Cohere. Reste à harmoniser les scrapers de pipeline secondaires).

- [ ] **Renforcement des Guardrails** : Migrer la détection de jailbreak basique vers un modèle de modération dédié (ex: Llama-Guard ou NeMo Guardrails) pour une protection robuste.
- [ ] **Contrôle d'accès aux Labs** : Restreindre les endpoints coûteux en GPU (Generate3D, Depth Estimation) aux utilisateurs authentifiés et appliquer des quotas stricts par utilisateur/tier.
- [ ] **Assainissement des requêtes externes IA** : Encoder strictement toutes les entrées utilisateur insérées dans des URLs d'APIs tierces (ex: Jikan) pour prévenir toute manipulation de paramètres.
- [ ] **Suppression du code dormant risqué** : Supprimer ou isoler strictement l'exécution `exec()` dans `DynamicToolAgent` pour éviter tout risque de RCE.
- [ ] **Masquage des données de transparence** : Restreindre l'accès aux métriques techniques détaillées de `TransparencyDataView` aux administrateurs uniquement.
