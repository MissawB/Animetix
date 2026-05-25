# Architecture Technique & Modulaire (Atomic & Hexagonal)

Ce document décrit l'architecture logicielle du projet **Double_scenario_Project** (Anime Archetype Engine). Le projet adopte une approche **Atomic & Hexagonal** (Clean Architecture) pour garantir un découplage strict entre la logique métier (Domain) et l'infrastructure (Adapters).

---

## 1. Vue d'Ensemble de l'Hexagone

L'architecture s'articule autour de trois strates :

```mermaid
graph TD
    subgraph Frameworks & Adapters (Externe)
        Django[Django Backend & Channels]
        ML_Adapters[Adapteurs d'Inférence: LocalLlama, Diffusers, Transformers]
        Persistence_Adapters[Adapteurs de Persistance: PgVector (Primaire), Neo4j, ChromaDB]
    end

    subgraph Ports (Interfaces)
        InferencePort[InferencePort - inclut Reranking]
        PersistencePort[PersistencePort - UnifiedRepository]
    end

    subgraph Core Domain (Métier)
        Services[Services Métier: AdvancedRAGService, PromptManager, Agents]
        Models[Modèles Pydantic: DTOs, Schémas IA]
    end

    Django --> Services
    Services --> InferencePort
    Services --> PersistencePort
    ML_Adapters --> InferencePort
    Persistence_Adapters --> PersistencePort
```

---

## 2. Structure du Code Source

Le code est organisé sous `src/` :

- **`core/ports/`** : Abstractions (ABC) définissant les contrats métier.
  - `InferencePort` : Génération de texte/image, clonage de voix, et désormais `rerank_documents`.
  - `PersistencePort` : Accès aux données unifié (`UnifiedRepositoryAdapter`).
- **`core/domain/services/`** : Logique métier pure, sans dépendance infra.
- **`adapters/`** : Implémentations concrètes (Infrastructure).
  - `adapters/persistence/` : Gestion multi-source (PgVector, Neo4j, Fallback ChromaDB).
  - `adapters/inference/` : Supports vLLM, GGUF, Transformers.
- **`backend/`** : Orchestration Django. Injection via `containers.py`.

---

## 3. Stockage & Persistance (Primary: PgVector)

Le projet utilise **PgVector** comme stockage vectoriel principal. L'accès aux données est unifié via `PersistencePort` qui gère la logique de fallback (ex: utilisation de ChromaDB en cas d'indisponibilité de PgVector). Neo4j est utilisé en complément pour la persistance des relations complexes du graphe de connaissances.

---

## 4. Stratégie d'Importations Paresseuses (Lazy Imports)

Pour optimiser le chargement, les bibliothèques lourdes (`torch`, `transformers`, etc.) sont chargées via `lazy_import.py`. L'import réel ne se déclenche qu'au premier accès attributaire, évitant des surcoûts inutiles pour les composants non IA.

---

## 5. Gestion des Fonctionnalités & Extension

Les adaptateurs concrétisent les ports. Toute méthode non supportée lève `InferenceNotImplementedError`. L'ajout de fonctionnalités (ex: Reranking) suit le cycle :
1. Extension du **Port**.
2. Implémentation dans l'**Adapter** correspondant.
3. Mise à jour de l'injection dans `containers.py`.

---

## 6. Déploiement : Architecture découplée (Pure SPA)

Animetix est désormais conçu et déployé comme une **Pure SPA** (Single Page Application) totalement découplée.

- **Frontend (Statique)** : Une application React moderne construite avec **Vite** (`frontend/`). Le bundle généré (`dist/`) est servi de manière ultra-performante. En développement, Vite tourne sur le port `5173` et proxyfie les requêtes `/api` et `/ws` vers le backend Django.
- **Backend (Headless API)** : Django fonctionne strictement comme une API headless. Toutes les anciennes routes HTML et contrôleurs de vues Django obsolètes ont été **intégralement supprimés** (nettoyage complet de `base.html` et des templates associés). 
- **Routage Unifié** : Django configure un routage systématique où la racine et toutes les requêtes de fallback (`re_path(r'^(?!api/|static/|admin/).*$', spa_view)`) redirigent vers `spa_view` pour laisser React gérer le routage côté client via `react-router-dom`.

### Synthèse des flux et découplage
1. **Communication** : API REST JSON via `/api/v1/` et requêtes GraphQL interactives via `/graphql/` (Knowledge Graph).
2. **Gestion d'État** : Tout l'état de l'application et les logiques de jeux complexes (Akinetix, Paradox, Forge) ont été déportés de la couche de présentation Django vers des **Domain Services** dans `src/core/domain/services/`.
3. **Sécurité et Authentification** : L'état d'authentification est centralisé côté React SPA, validé par un endpoint Django dédié (`feat(spa-auth)`).
4. **Configuration de Production** :
   - Construire le front avec `npm run build` dans le dossier `frontend/`.
   - Servir les fichiers statiques de `dist/` via Nginx ou un service CDN.
   - Configurer le reverse proxy pour diriger `/api/`, `/graphql/` et les connexions WebSocket `/ws/` vers le serveur d'application Django (Gunicorn/Uvicorn).
