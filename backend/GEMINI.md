# GEMINI - Mandats Backend

Ce fichier définit les contraintes spécifiques à la couche serveur et au domaine IA.

## 🏗️ Architecture & Injection
- **Hexagonal Integrity :** Respecter le flux `Presentation -> Core (Domain/Ports) <- Adapters`.
- **Dependency Injection :** Utiliser le container global situé dans `backend/api/animetix/containers.py`. Les dépendances IA (modèles, adaptateurs) doivent être chargées de manière **lazy** pour optimiser le temps de démarrage.

## 🐍 Standards Python & API
- **Version :** Python 3.11+.
- **Validation :** Utilisation systématique de `Pydantic` (v2) pour les schémas d'entités et d'échange IA.
- **Django :** Utiliser les `Forms` pour la validation des entrées API. Les vues doivent rester fines (thin views) et déléguer la logique aux `Domain Services`.
- **Asynchronisme :** Utiliser `Channels` pour les flux temps réel (SSE/WebSockets). Préférer `contextvars` pour la gestion des états de requête en environnement asynchrone.

## 🧠 Intelligence Artificielle & MLOps
- **Orchestration :** Les pipelines d'ingestion et d'entraînement doivent suivre les patterns **Dagster**.
- **Inference :** Toujours passer par `InferencePort`. Implémenter le fallback vers Ollama ou BrainAPI.
- **RAG :** Maintenir la synchronisation entre `ChromaDB` (recherche sémantique) et `Neo4j` (raisonnement par graphe).

## 🧪 Tests & Qualité
- **Suite de tests :** `pytest` avec couverture obligatoire des Use Cases du Domaine.
- **Logging :** Ne jamais utiliser `print()`. Utiliser des loggers hiérarchiques.
