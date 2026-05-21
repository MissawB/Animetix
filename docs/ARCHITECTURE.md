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

Animetix est désormais conçu comme une **Pure SPA**. 

- **Frontend (Statique)** : `index.html` + Bundle React (Vite) peut être servi par n'importe quel serveur statique (Nginx, S3, Vercel).
- **Backend (API)** : Django sert exclusivement d'API JSON via `/api/v1/`.

La dépendance structurelle à `base.html` (Django Templates) est devenue optionnelle et conservée uniquement pour des raisons de rétrocompatibilité. Pour un déploiement 100% découplé :
1. Construire le front avec `npm run build` dans le dossier `frontend/`.
2. Servir le dossier `dist/` via Nginx ou un CDN.
3. Configurer le reverse proxy pour rediriger les appels `/api/` vers le backend Django.
