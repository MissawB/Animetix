# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture (Inférence)

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
- [ ] **Suppression de la dépendance LangChain** : Supprimer ou bypasser LangChain via l'héritage direct de `BaseRagasLLM` pour Ragas. Permet d'alléger l'environnement virtuel et d'éliminer les conflits de versions.
- [ ] **Migration Dagster ➡️ Celery** : Migrer le DAG de données (`dagster_app.py`) vers des workflows Celery (Chains/Groups) et Celery Beat pour fermer le serveur et le démon Dagster, libérant ainsi de la RAM.
- [ ] **Stabilisation de la recherche Web (DuckDuckGo ➡️ Gemini Grounding / Tavily)** : Remplacer le scraping DuckDuckGo instable par l'outil natif de Google Search Grounding (Gemini) ou une API structurée comme Tavily.
- [ ] **Simplification d'état Frontend (XState ➡️ Zustand)** : Refactoriser les machines d'état simples du dossier `/machines` en stores Zustand plus légers et fluides, réduisant la taille du bundle et le boilerplate.

## 🧬 Fonctionnalités SOTA & Innovations

- [ ] **Hyper-Personnalisation Graphique** : Implémenter une personnalisation dynamique de l'interface basée sur le "Archetype Drift" de l'utilisateur (couleurs et thèmes changeant selon les affinités détectées).

## 🖥️ Pages Frontend Manquantes (Dette UI)

- [ ] **Soundscape Lab** : Créer la page `SoundscapeLabPage.tsx` pour la génération d'ambiances sonores (API `/api/v1/labs/soundscape/`).
- [ ] **Speech-to-Speech Lab** : Interface pour l'interaction vocale E2E (API `/api/v1/labs/s2s/`).
- [ ] **Accessibilité des Préférences** : Ajouter des liens vers `CustomConfigPage.tsx` dans le profil utilisateur pour permettre la personnalisation réelle de l'expérience.

## 🛡️ Sécurité & Résilience (Post-Audit 2026)

- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
