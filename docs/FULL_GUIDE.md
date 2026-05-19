# 🎭 Animetix : L'Encyclopédie Technique & Fonctionnelle (SOTA 2026)

Ce document constitue la spécification technique exhaustive et le manuel opérationnel de la plateforme **Animetix**. Il est conçu pour les ingénieurs IA, les développeurs Fullstack et les architectes système souhaitant comprendre ou faire évoluer cet écosystème complexe.

---

## 🏛️ 1. Architecture Cognitive : L'Hexagone 2.0

Animetix n'est pas une simple application web, c'est une **Cognitive Architecture** distribuée suivant les principes de l'architecture hexagonale.

### A. Core Domain (Intelligence Pure)
Situé dans `src/core/domain`, le domaine est le garant de la cohérence logique.
- **Services de Découverte (`AgenticRAGService`) :** Orchestre une boucle de raisonnement cognitive complexe sous forme de machine à états fini (FSM). Contrairement au RAG classique qui fait `Question -> Retrieval -> Answer`, Animetix exécute le cycle suivant :
    1.  **ANALYZE :** Analyse de la complexité et allocation d'un budget de réflexion (TTC).
    2.  **PLAN :** Le `SearchPlanner` établit une stratégie (Web vs Local vs Graphe).
    3.  **RESEARCH :** Recherche hybride et exploration multi-hop dans Neo4j via le `GraphExpert`.
    4.  **DISTILL :** Le `ScoutAgent` extrait un "Chemin de Vérité" (Truth Path) du bruit documentaire.
    5.  **VLM_RERANK :** (Si visuel) Ré-ordonnancement des candidats par inspection directe des images.
    6.  **SYNTHESIZE :** Rédaction finale par le `ResponseSynthesizer`.
    7.  **JUDGE :** Débat multi-agents (`DebateManager`) pour valider la fidélité au contexte.
- **Validation Strict Pydantic :** Chaque sortie d'un agent LLM est castée dans un modèle Pydantic (`ai_schemas.py`). Si le JSON est malformé, un mécanisme de **Self-Correction** renvoie l'erreur au LLM pour correction immédiate.
- **Prompt Management (`PromptManager`) :** Les prompts sont externalisés dans des templates YAML. Le système implémente une **Métacognition In-Context** : si une erreur est corrigée par l'utilisateur ou le Juge, elle est enregistrée dans `auto_corrections.json` et réinjectée dynamiquement comme Few-Shot pour éviter que l'IA ne répète la même erreur.

### B. Ports & Adapters (Isolation de l'Infrastructure)
- **InferencePort :** Interface unifiée supportant le streaming SSE, le *Test-Time Compute* (TTC) et le routage SLM.
- **RepositoryPort :** Interface de persistance capable de basculer dynamiquement entre une source relationnelle (PostgreSQL) et vectorielle (PgVector/Chroma).

---

## 🧠 2. Deep Dive : Pipeline IA & Modèles SOTA

### A. Inférence & Raisonnement (LLM & SLM)
Animetix utilise une hiérarchie de modèles pour optimiser le ratio **Coût / Latence / Précision** :
1.  **Thinking Model (8B+ - ex: DeepSeek-R1 Distill) :** Utilisé uniquement lorsque l'Analyseur de Complexité détecte une requête hautement ambiguë. Il génère des tokens de réflexion interne (`<thought>`) avant de répondre.
2.  **Synthesis Model (8B - ex: Llama-3 / Qwen3) :** Le modèle standard pour la rédaction finale de haute qualité.
3.  **Scout & Critic (1B-3B - ex: Phi-4-mini / SmolLM3) :** Modèles ultra-légers optimisés pour des tâches structurelles (extraction d'entités, évaluation de pertinence, planification). Ils tournent sur le CPU ou des GPU d'entrée de gamme avec une latence sub-seconde.
4.  **Quantisation BitNet (1.58-bit) :** Utilisation de poids ternaires pour réduire l'empreinte VRAM de 70% sans dégradation notable de l'intelligence.

### B. Espace Vectoriel & Matryoshka (MRL)
Animetix implémente le **Matryoshka Representation Learning** sur le modèle **Jina-v3** :
- **Concept :** Les embeddings sont entraînés pour que l'information la plus importante soit concentrée dans les premières dimensions.
- **Workflow de Recherche :**
    1.  **Phase de "Grossissage" :** Recherche vectorielle SQL sur les **128 premières dimensions** (index HNSW). C'est 8x plus rapide qu'une recherche complète.
    2.  **Phase de "Zoom" :** Les 50 meilleurs candidats sont ré-évalués en utilisant les **1024 dimensions** complètes.
- **Résultat :** Latence de recherche < 50ms sur 1 million d'items.

### C. Vision & Voice (Multimodalité SOTA)
Animetix ne se limite pas au texte, il intègre des capacités sensorielles avancées :
1.  **Vision (SigLIP-SO400M) :** Utilisation de SigLIP pour l'alignement Image-Texte. Contrairement à CLIP, SigLIP utilise une fonction de perte sigmoid permettant un alignement plus fin.
2.  **Visual Reranker (Qwen-VL) :** Pour les requêtes visuelles complexes, un modèle Vision-Langage inspecte réellement les fichiers images pour valider la correspondance visuelle exacte.
3.  **Voice Cloning (RVC) :** Le `VoiceCloningService` permet de générer des réponses audio avec la voix exacte d'un personnage à partir d'un échantillon de 10 secondes (Zero-shot cloning).
4.  **Native Speech LLM (S2S) :** Support des interactions Speech-to-Speech (S2S) via le `NativeSpeechLLMService`, traitant l'audio de bout en bout sans passer par une transcription textuelle intermédiaire, réduisant drastiquement la latence émotionnelle.

---

## 🕸️ 3. Graphe de Connaissances & GraphRAG

### A. Ontologie Neo4j
Le graphe n'est pas un simple index, c'est une structure de relations :
- **Nœuds :** `Media`, `Studio`, `Creator`, `Character`, `MicroTag` (thèmes ultra-précis).
- **Relations :** `PRODUCED_BY`, `CREATED_BY`, `FEATURES`, `HAS_THEME`, `INFLUENCED_BY`.

### B. Algorithmes de Raisonnement
- **Multi-Hop Traversal :** L'agent peut demander : *"Trouve tous les animes produits par le studio qui a fait 'Arcane' mais qui ont un style visuel similaire à 'Spirited Away'"*. Le système navigue de `Media -> Studio -> Creator -> Other Media` et croise avec la recherche vectorielle.
- **Global Community Summarization :** Utilisation de l'algorithme de détection de communautés (Leiden) pour générer des résumés de haut niveau. Neo4j agrège les données d'un groupe de nœuds et le LLM en fait une synthèse thématique (ex: "Panorama du genre Cyberpunk dans les années 90").

---

## 🎮 4. Analyse détaillée des Modes de Jeu

### 1. Mode Paradox Quest (IA Neuro-Symbolique)
*   **Technologie :** Combine un LLM avec un solveur logique (Z3 / Neuro-symbolic layer).
*   **Mécanique :** L'IA identifie 2 œuvres avec un lien logique fort et 1 "intrus". Le joueur doit trouver l'intrus. 
*   **Boucle de Résolution :**
    1.  **Extraction Sémantique :** Un "Oracle" (LLM) extrait les propriétés booléennes des items.
    2.  **Résolution Formelle :** Le solveur **Z3** traite ces faits pour identifier mathématiquement l'intrus (Preuve SAT).
    3.  **Vulgarisation :** L'Oracle traduit la preuve mathématique en une explication narrative compréhensible pour le joueur.

### 2. Mode Akinetix RL (Reinforcement Learning)
*   **Technologie :** Proximal Policy Optimization (PPO).
*   **Mécanique :** L'agent a été entraîné par renforcement dans un environnement simulé (`AkinetixRLService`) pour poser les questions les plus discriminantes le plus vite possible, minimisant le nombre de tours pour deviner un personnage.

### 3. Mode La Forge (Génération Multimodale)
*   **Technologie :** Stable Diffusion XL + IP-Adapter + ControlNet.
*   **Mécanique :** Fusion de deux univers sémantiques. Le LLM génère un synopsis hybride, et le pipeline de vision génère une affiche respectant les codes visuels des deux œuvres (ex: mélange du trait de *Akira* avec l'ambiance de *Ghibli*).

### 4. Mode Spatial Computing (Exploration 3D)
*   **Technologie :** DepthAnything + 3D Gaussian Splatting.
*   **Mécanique :** Reconstruction d'une scène 3D navigable à partir d'une simple image 2D (ex: poster généré dans La Forge). Le `SpatialComputingService` estime la carte de profondeur et génère un nuage de points volumétrique permettant une immersion VR immédiate dans l'univers hybride.

---

## 📊 5. MLOps, Observabilité & Évolution

### A. La boucle LooP (Real-time Evaluation)
Animetix implémente le pattern **LLM-as-a-Judge** :
- Chaque réponse est envoyée à un agent Juge.
- **Métriques Ragas :**
    - **Faithfulness :** La réponse est-elle supportée par le contexte ? (Anti-hallucination).
    - **Relevancy :** La réponse est-elle utile ?
- Si `Faithfulness < 0.7`, une alerte est levée et le système peut s'auto-corriger en direct avant que l'utilisateur ne voie la réponse (ou en affichant un disclaimer).

### B. Pipeline DPO (Direct Preference Optimization)
Le système s'auto-améliore via les feedbacks :
- **Collecte :** Les utilisateurs notent les réponses (Pouce levé/baissé).
- **Curation :** Les feedbacks négatifs sont analysés par le Juge pour identifier pourquoi l'IA a échoué.
- **Export :** Génération automatique de fichiers JSONL au format `(Prompt, Chosen, Rejected)`.
- **Alignement :** Ces données servent à ré-entraîner le modèle SLM via l'asset Dagster `trl_retraining`.

---

## 🛡️ 6. Sécurité & Compliance IA

### A. Sanitisation Robuste
- **Bleach Integration :** Toutes les sorties LLM passent par un filtre de liste blanche HTML strict. Aucun script ou style malveillant généré par l'IA ne peut être exécuté dans le navigateur.
- **Forbidden Terms :** Le `LLMService` dispose d'une couche de filtrage par Regex pour censurer les spoilers ou les contenus sensibles avant qu'ils ne sortent du moteur d'inférence.

### B. Secrets & Infrastructure
- **Isolation :** Aucun secret (API Key, DB URI) n'est présent dans le code ou les images Docker. Tout passe par le `Secret Manager` de l'environnement (ou fichier `.env` protégé).
- **Rate Limiting :** Protection contre le déni de service IA (DoS) via un middleware de limitation du nombre de tokens consommés par IP et par heure.

---

## 🚀 7. Roadmap de Déploiement

1.  **Staging :** Déploiement Docker Stack (Postgres, Redis, Neo4j, vLLM, Dagster).
2.  **Pre-Flight :** Exécution de `scripts/pre_flight_check.py` pour valider les 12 points de contrôle.
3.  **Production :** Activation du streaming SSE et du monitoring Prometheus/Grafana pour surveiller la latence des agents en temps réel.

---
*Fin du document technique - Animetix v3.0 - Mai 2026*
