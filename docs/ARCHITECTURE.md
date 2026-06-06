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
        Persistence_Adapters[Adapteurs de Persistance: ChromaDB, Neo4j, Django DB]
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

Le code est organisé sous `backend/` :

- **`core/ports/`** : Abstractions (ABC) définissant les contrats métier.
  - `InferencePort` : Génération de texte/image, clonage de voix, reranking, et vision avancée.
  - `MlopsPort` : Gestion de la télémétrie, journalisation DPO et feedbacks IA via Celery.
  - `PersistencePort` : Accès aux données unifié (`UnifiedRepositoryAdapter`).
- **`core/domain/services/`** : Logique métier pure, sans dépendance infra.
- **`adapters/`** : Implémentations concrètes (Infrastructure).
  - `adapters/persistence/` : Gestion multi-source (ChromaDB, Neo4j).
  - `adapters/inference/` : Supports BrainAPI, Ollama (Unified), Transformers.
- **`api/`** : Orchestration Django. Injection via `containers/`.

---

## 3. Stockage & Persistance (Primary: ChromaDB)
Le projet utilise **ChromaDB** comme stockage vectoriel exclusif pour la recherche sémantique. L'accès aux données est unifié via `UnifiedRepositoryAdapter`. Neo4j est utilisé en complément pour la persistance des relations complexes du graphe de connaissances.


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
1. **Communication** : API REST JSON via `/api/v1/`.
2. **Gestion d'État** : Tout l'état de l'application et les logiques de jeux complexes (Akinetix, Paradox, Forge) ont été déportés de la couche de présentation Django vers des **Domain Services** dans `backend/core/domain/services/`.
3. **Sécurité et Authentification** : L'état d'authentification est centralisé côté React SPA, validé par un endpoint Django dédié (`feat(spa-auth)`).
4. **Configuration de Production** :
   - Construire le front avec `npm run build` dans le dossier `frontend/`.
   - Servir les fichiers statiques de `dist/` via Nginx ou un service CDN.
   - Configurer le reverse proxy pour diriger `/api/` et les connexions WebSocket `/ws/` vers le serveur d'application Django (Gunicorn/Uvicorn).

---

## 7. Écosystème des Adaptateurs d'Inférence

Le projet utilise un **FallbackInferenceAdapter** qui orchestre une chaîne de repli entre les différents moteurs d'inférence :

```mermaid
graph TD
    FallbackAdapter["FallbackInferenceAdapter"]
    
    subgraph Adaptateurs Texte
        BrainAPI["BrainAPIAdapter (Cloud - Primaire)"]
        Ollama["UnifiedInferenceAdapter (Ollama Local - Fallback)"]
        Langchain["LangchainAdapter"]
    end
    
    subgraph Adaptateurs Vision
        VisionTF["VisionTransformersAdapter"]
        Diffusers["DiffusersAdapter"]
        Qwen3VL["Qwen3VLAdapter"]
        Moondream["MoondreamAdapter"]
    end
    
    subgraph Adaptateurs Audio
        AudioTF["AudioTransformersAdapter"]
        XTTS["XTTSAdapter"]
    end
    
    FallbackAdapter --> BrainAPI
    FallbackAdapter --> Ollama
    FallbackAdapter --> VisionTF
    FallbackAdapter --> Diffusers
    FallbackAdapter --> AudioTF
```

Chaque adaptateur implémente un sous-ensemble de l'`InferencePort`. Le `FallbackInferenceAdapter` construit un **cache de capacités** au démarrage pour router chaque appel vers le premier adaptateur capable.

---

## 8. Architecture Mixin de VisionTransformersAdapter

Pour éviter un fichier monolithique, `VisionTransformersAdapter` est décomposé en **4 mixins** spécialisés :

```mermaid
classDiagram
    class InferencePort {
        <<abstract>>
        +generate()
        +health_check()
    }
    class DepthEstimationMixin {
        +estimate_depth()
        +generate_3d_scene()
    }
    class MangaOcrMixin {
        +process_manga_page()
    }
    class VideoAnalysisMixin {
        +get_video_temporal_embeddings()
        +localize_video_actions()
        +generate_video_description()
    }
    class ClipVisionMixin {
        +get_image_embedding()
        +classify_image()
        +calculate_visual_similarity()
        +visual_rerank()
        +get_multimodal_late_interaction()
    }
    class VisionTransformersAdapter {
        +detect_objects()
        +generate_image_description()
        +health_check()
    }
    
    InferencePort <|-- VisionTransformersAdapter
    DepthEstimationMixin <|-- VisionTransformersAdapter
    MangaOcrMixin <|-- VisionTransformersAdapter
    VideoAnalysisMixin <|-- VisionTransformersAdapter
    ClipVisionMixin <|-- VisionTransformersAdapter
```

---

## 9. Hiérarchie des Exceptions

Toutes les exceptions du projet dérivent de `AnimetixBaseError` :

```mermaid
classDiagram
    class AnimetixBaseError {
        +message: str
        +context: dict
    }
    class DomainError
    class InfrastructureError
    class InferenceError
    class InferenceTimeoutError
    class SpatialComputingError
    class MangaProcessingError
    class VideoProcessingError
    class ImageGenerationError
    class AdapterLoadError
    class ContentModerationError
    class KnowledgeGraphQueryError
    
    AnimetixBaseError <|-- InfrastructureError --|> AdapterLoadError
    AnimetixBaseError <|-- InfrastructureError --|> ContentModerationError
    AnimetixBaseError <|-- InfrastructureError --|> KnowledgeGraphQueryError
```

---

## 10. Accès & Modes de Déploiement

### A. Environnement Local (Développement manuel)
Dans cet environnement, le frontend et le backend tournent séparément pour permettre le *Hot Module Replacement* (HMR).

- **Backend (Django)** : 
  - URL : `http://localhost:8000`
  - Commande : `python backend/api/manage.py runserver`
- **Frontend (React/Vite)** : 
  - URL : `http://localhost:5173`
  - Commande : `cd frontend && npm run dev`
  - *Note* : Le serveur Vite proxyfie automatiquement `/api/*` et `/ws/*` vers Django.

### B. Environnement Dev / Staging (Docker)
L'utilisation de Docker regroupe tout dans des conteneurs isolés. Le frontend est pré-construit et servi par le backend.

- **Docker Standard** :
  - URL : `http://localhost:8000`
  - Commande : `docker-compose -f deploy/docker-compose.yml up`
- **Docker Staging** (avec modes expérimentaux & debug) :
  - URL : `http://localhost:8080`
  - Commande : `docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.staging.yml up`

### C. Environnement de Production (Hugging Face)
Animetix est optimisé pour un déploiement sur **Hugging Face Spaces**.

- **URL** : `https://huggingface.co/spaces/MissawB/Animetix` (ou URL personnalisée).
- **Port Interne** : Le conteneur expose le port `7860`.
- **Pipeline** : Déploiement automatisé via GitHub Actions (`deploy_to_hf.yml`).

