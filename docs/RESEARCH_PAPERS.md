# 📚 Références & Papiers de Recherche IA (Animetix)

L'architecture d'**Animetix** repose sur une combinaison de techniques d'Intelligence Artificielle à l'état de l'art. Ce document centralise les papiers de recherche fondamentaux (et les concepts associés) qui ont directement inspiré l'implémentation de nos services, de notre RAG et de notre pipeline de raisonnement.

---

## 🧠 1. Mécanismes de Raisonnement & Mémoire (CoT)

### DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning
* **ID / Source :** [arXiv:2501.12948](https://huggingface.co/papers/2501.12948)
* **Concept Clé :** Utilisation du **GRPO** pour entraîner des modèles de langage à développer des capacités de raisonnement profond par auto-correction. L'introduction du *Test-Time Compute* (TTC).
* **Implémentation dans Animetix :** Le fondement de notre **Thinking Mode**. Le modèle génère une trace de pensée interne (`<thought>`) avant de répondre.

### Chain-of-Verification Reduces Hallucination in Large Language Models
* **ID / Source :** [arXiv:2309.11495](https://huggingface.co/papers/2309.11495)
* **Concept Clé :** La méthode CoVe permet aux LLMs de délibérer sur leurs réponses en planifiant et en répondant à des questions de vérification indépendantes.
* **Implémentation dans Animetix :** Le `CoveOracleService` implémente ce protocole pour s'assurer que les faits (lore) ne sont pas hallucinés.

### STaR: Bootstrapping Reasoning With Reasoning
* **ID / Source :** [arXiv:2203.14465](https://huggingface.co/papers/2203.14465)
* **Concept Clé :** Le "Self-Taught Reasoner" permet à un modèle de langage d'améliorer ses capacités de raisonnement en générant et validant ses propres justifications.
* **Implémentation dans Animetix :** Cœur de notre `StarReasonerService`. Génère des trajectoires de résolution d'énigmes et s'affine sur ses succès.

### Tree of Thoughts: Deliberate Problem Solving with Large Language Models
* **ID / Source :** [arXiv:2305.10601](https://huggingface.co/papers/2305.10601)
* **Concept Clé :** Cadre permettant aux LLMs d'explorer des branches de raisonnement de manière délibérée avec retour en arrière (backtracking).
* **Implémentation dans Animetix :** Intégré dans le `TreeOfThoughtsSearchService` pour les énigmes complexes d'Akinetix.

### MemGPT: Towards LLMs as Operating Systems
* **ID / Source :** [arXiv:2310.08560](https://huggingface.co/papers/2310.08560)
* **Concept Clé :** Gestion hiérarchique de "mémoire virtuelle" paginée, s'affranchissant de la limite de contexte du LLM.
* **Implémentation dans Animetix :** Inspiration de notre `EpisodicMemoryCompressor`. Le système archive dynamiquement les interactions passées en épisodes et les pagine dans le contexte.

### VibeThinker-3B & Nemotron 3 Ultra
* **ID / Source :** Hugging Face Daily Papers (Juin 2026)
* **Concept Clé :** SLMs hyper-rationnels et allocation d'un **Reasoning Budget** dynamique.
* **Implémentation dans Animetix :** Création du `CompactReasoningAdapter` et mise à jour du `ComplexityAnalyser` pour une allocation granulaire du TTC.

### Ring Attention with Blockwise Transformers for Near-Infinite Context
* **ID / Source :** [arXiv:2310.01889](https://huggingface.co/papers/2310.01889)
* **Concept Clé :** Calcul de l'attention distribué pour traiter des séquences infinies sans saturer la VRAM.
* **Implémentation dans Animetix :** Sous-tend le `LongContextDiscoveryService` et validé par notre test "Multimodal Needle in a Haystack" (arXiv:2406.11230).

---

## 🤖 2. Agents Autonomes & Théorie des Jeux

### ReAct: Synergizing Reasoning and Acting in Language Models
* **ID / Source :** [arXiv:2210.03629](https://huggingface.co/papers/2210.03629)
* **Concept Clé :** Entrelacement des traces de raisonnement et des actions (appel d'API, recherche) permettant une prise de décision interactive, robuste et interprétable.
* **Implémentation dans Animetix :** L'architecture centrale de notre `DynamicToolAgent`. L'agent raisonne ("Je dois trouver l'âge de ce personnage"), agit (Recherche Web/API) et observe le résultat avant de conclure.

### Toolformer: Language Models Can Teach Themselves to Use Tools
* **ID / Source :** [arXiv:2302.04761](https://huggingface.co/papers/2302.04761)
* **Concept Clé :** Modèle apprenant de manière auto-supervisée quand et comment appeler des API externes pour pallier ses faiblesses intrinsèques (mathématiques, recherche de faits temporels).
* **Implémentation dans Animetix :** Les principes du Toolformer guident la conception de nos outils internes injectés dans l'orchestrateur. L'IA d'Animetix détermine de manière autonome s'il faut appeler l'API Jikan (MyAnimeList) ou exécuter une fonction de calcul interne.

### Eureka: Human-Level Reward Design via Coding Large Language Models
* **ID / Source :** [arXiv:2310.12931](https://huggingface.co/papers/2310.12931)
* **Concept Clé :** Utilisation des LLMs comme planificateurs de haut niveau pour écrire, compiler et auto-améliorer du code source ou des fonctions de récompense de manière itérative et évolutive.
* **Implémentation dans Animetix :** C'est le principe derrière notre `SelfEvolvingCompiler`. Le système génère dynamiquement des noyaux de calcul mathématiques en Python, les compile à la volée via Numba (JIT), et les met à jour s'ils ne sont pas assez performants.

### Learning Strategic Language Agents in the Werewolf Game (CFR + LLM)
* **ID / Source :** [arXiv:2502.04686](https://huggingface.co/papers/2502.04686)
* **Concept Clé :** Minimisation du regret contrefactuel (CFR) appliquée au LLM pour optimiser la prise de décision stratégique.
* **Implémentation dans Animetix :** Moteur du `CFRGameSolver` et d'`AkinetixEngine` pour réduire l'incertitude dans le jeu de devinettes de personnages.

### Mixture-of-Agents Enhances Large Language Model Capabilities
* **ID / Source :** [arXiv:2406.04692](https://huggingface.co/papers/2406.04692)
* **Concept Clé :** Approche "Mixture-of-Agents" (MoA) où de multiples LLMs en cascade collaborent et raffinent les réponses des agents précédents.
* **Implémentation dans Animetix :** Notre `SwarmConsensusOrchestrator` orchestre différents experts IA (Visuel, Lore, Audio) pour établir un consensus final.

---

## 🎥 3. Multimodalité, Vision & Audio

### Video-LLaVA: Learning United Visual Representation by Alignment Before Projection
* **ID / Source :** [arXiv:2311.10122](https://huggingface.co/papers/2311.10122)
* **Concept Clé :** Unification des espaces images/vidéos pour une compréhension temporelle supérieure.
* **Implémentation dans Animetix :** Moteur du `VideoLanguageIndexingService` pour la génération narrative dense d'extraits d'animes.

### VisualClaw: A Real-Time, Personalized Agent for the Physical World
* **ID / Source :** [arXiv:2606.16295](https://huggingface.co/papers/2606.16295) (Juin 2026)
* **Concept Clé :** Agent multimodal doté d'une "Skill Bank" auto-évolutive apprenant de ses échecs.
* **Implémentation dans Animetix :** Boucle d'auto-évolution du Video-RAG pour corriger continuellement les erreurs de reconnaissance (ex: confusion de techniques d'arts martiaux).

### 3D Gaussian Splatting for Real-Time Radiance Field Rendering
* **ID / Source :** [arXiv:2308.04079](https://huggingface.co/papers/2308.04079)
* **Concept Clé :** Rendu en temps réel de scènes 3D à partir d'images 2D, plus performant que les NeRFs.
* **Implémentation dans Animetix :** Cœur du `CinematicVolumetricReconstructionService` reconstruisant des scènes d'anime en dioramas 3D.

### AudioLM: a Language Modeling Approach to Audio Generation
* **ID / Source :** [arXiv:2209.03143](https://huggingface.co/papers/2209.03143)
* **Concept Clé :** Modélisation de la génération audio via des tokens acoustiques discrets.
* **Implémentation dans Animetix :** Base du `NativeSpeechLLMService` et du `VoiceCloningService` pour la synthèse vocale spatialisée des personnages.

---

## 🗄️ 4. Embeddings, RAG & Graphes de Connaissances

### Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
* **ID / Source :** [arXiv:2310.11511](https://huggingface.co/papers/2310.11511)
* **Concept Clé :** Un framework où l'IA apprend à décider de manière adaptative *quand* récupérer des documents, *comment* générer la réponse et *critiquer* (évaluer) la pertinence de ses propres récupérations via des "reflection tokens".
* **Implémentation dans Animetix :** Le pilier de notre `rag_orchestrator.py` et de l'`AgenticRAGService`. Au lieu de faire un RAG "aveugle", notre orchestrateur s'évalue lui-même, décide si le contexte issu de la base vectorielle est suffisant, et émet des critiques sur la fidélité de sa synthèse finale.

### Matryoshka Representation Learning
* **ID / Source :** [arXiv:2205.13147](https://huggingface.co/papers/2205.13147)
* **Concept Clé :** Représentations vectorielles tronquables (l'information majeure au début du vecteur).
* **Implémentation dans Animetix :** Optimise le stockage ChromaDB pour une recherche sémantique ultra-rapide et économique.

### LEGO-GraphRAG: Modularizing Graph-based Retrieval-Augmented Generation
* **ID / Source :** [arXiv:2411.05844](https://huggingface.co/papers/2411.05844)
* **Concept Clé :** Décomposition modulaire du RAG sur graphes (Extraction, Filtrage, Raffinement).
* **Implémentation dans Animetix :** Modèle le `HierarchicalGraphRAGService`. Notre agent "Scout" filtre et extrait des "Truth Paths" depuis Neo4j.

### Filter-then-Generate: LLMs with Structure-Text Adapter for Knowledge Graph Completion
* **ID / Source :** [arXiv:2412.09094](https://huggingface.co/papers/2412.09094)
* **Concept Clé :** KGC (Knowledge Graph Completion) via une synergie LLM et graphes ego pour limiter les hallucinations.
* **Implémentation dans Animetix :** Cœur du `GraphHealerService` qui cicatrise automatiquement les nœuds et relations manquants dans Neo4j.

### MeanCache: User-Centric Semantic Caching for LLM Web Services
* **ID / Source :** [arXiv:2403.02694](https://huggingface.co/papers/2403.02694)
* **Concept Clé :** Cache sémantique évitant le rappel de l'API LLM sur des requêtes de sens similaire.
* **Implémentation dans Animetix :** `SemanticCacheService` pour réduire les coûts d'inférence.

---

## ⚙️ 5. MLOps, Sécurité & Inférence à l'Échelle

### Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations
* **ID / Source :** [arXiv:2312.06674](https://huggingface.co/papers/2312.06674)
* **Concept Clé :** Modèle de modération agissant comme un bouclier (safeguard) pour catégoriser et bloquer les requêtes malveillantes (Jailbreaks, Hate Speech, Prompt Injection) et filtrer les réponses toxiques en entrée comme en sortie.
* **Implémentation dans Animetix :** Il s'agit du socle de notre `GuardrailService`. Ce service intercepte toutes les requêtes entrantes pour détecter les tentatives de jailbreak et vérifie toutes les réponses sortantes pour bloquer les spoilers non désirés ou les fuites du prompt système.

### Constitutional AI: Harmlessness from AI Feedback
* **ID / Source :** [arXiv:2212.08073](https://huggingface.co/papers/2212.08073)
* **Concept Clé :** Entraîner une IA à être inoffensive (harmless) en utilisant uniquement un ensemble de principes ou de règles (Constitution) et en lui demandant de s'auto-critiquer et de réviser ses réponses.
* **Implémentation dans Animetix :** Les mécanismes d'auto-critique du papier Constitutional AI inspirent le "Red Teaming Agent" et notre boucle de rétroaction qui pousse l'agent Juge à s'auto-évaluer avant de valider un débat.

### S-LoRA: Serving Thousands of Concurrent LoRA Adapters
* **ID / Source :** [arXiv:2311.03285](https://huggingface.co/papers/2311.03285)
* **Concept Clé :** Système de "Unified Paging" (pool de mémoire unifié pour les poids dynamiques et le KV cache) permettant de servir de manière concurrente des milliers d'adaptateurs LoRA sur un seul modèle de base (Foundation Model) avec un surcoût quasi nul.
* **Implémentation dans Animetix :** C'est le secret de notre `MultiLoraManager`. Il permet à des centaines d'utilisateurs de discuter simultanément avec des personnages d'anime ayant des "personnalités" (LoRA adapters) différentes, le tout tournant de manière hyper-optimisée sur nos GPU.

### DSPy: Compiling Declarative Language Model Calls
* **ID / Source :** [arXiv:2310.03714](https://huggingface.co/papers/2310.03714)
* **Concept Clé :** Optimisation itérative et mathématique des prompts.
* **Implémentation dans Animetix :** Le `DSPyPromptOptimizer` compile les system prompts pour maximiser les métriques de RAGAS.

### Distilling Step-by-Step! Outperforming Larger Language Models
* **ID / Source :** [arXiv:2305.02301](https://huggingface.co/papers/2305.02301)
* **Concept Clé :** Distillation de la connaissance via la supervision des "rationales" des modèles géants.
* **Implémentation dans Animetix :** La `ModelDistillationPipeline` s'en sert pour former nos SLMs locaux.

### RAGAS: Automated Evaluation of Retrieval Augmented Generation
* **ID / Source :** [arXiv:2309.15217](https://huggingface.co/papers/2309.15217)
* **Concept Clé :** Framework "LLM-as-a-judge" pour évaluer la fidélité et la pertinence du RAG.
* **Implémentation dans Animetix :** Calcule le "Trust Score" des réponses via le `RagasEvalService`.

### Direct Preference Optimization (DPO)
* **ID / Source :** [arXiv:2305.18290](https://huggingface.co/papers/2305.18290)
* **Concept Clé :** Alignement RL sans modèle de récompense (Reward Model), par classification de paires de préférences.
* **Implémentation dans Animetix :** Nourrit le `DPOFeedbackLoop` pour l'alignement continu des modèles.

### Who Flips? Self- and Cross-Model Counterarguments Reveal Answer Instability in LLMs
* **ID / Source :** [arXiv:2606.16011](https://huggingface.co/papers/2606.16011) (Juin 2026)
* **Concept Clé :** Étude mesurant la vulnérabilité des LLMs face à des contre-arguments plausibles mais faux ("Flip Rate").
* **Implémentation dans Animetix :** Informent la conception de notre `SelfPlayDebateService`. Le système est durci pour résister aux hallucinations persuasives de l'agent "Avocat du Diable" en se basant sur le graphe Neo4j.

### Is Model Collapse Inevitable? Breaking the Curse of Recursion
* **ID / Source :** [arXiv:2404.01413](https://huggingface.co/papers/2404.01413)
* **Concept Clé :** La prévention de la dégénérescence des modèles par une validation hybride données réelles/synthétiques.
* **Implémentation dans Animetix :** Fonde l'Universal HITL Gate du `SyntheticValidationService`.

### Language Models (Mostly) Know What They Know
* **ID / Source :** [arXiv:2207.05221](https://huggingface.co/papers/2207.05221)
* **Concept Clé :** Quantification de l'incertitude native via l'entropie des logprobs.
* **Implémentation dans Animetix :** Le `XaiDiagnosticService` s'auto-régule si le score de confiance mathématique chute sous 0.7.

---

## 🔬 6. Réseaux de Neurones Avancés & Sciences Cognitives

### Closed-form Continuous-time Neural Models
* **ID / Source :** [arXiv:2106.13898](https://huggingface.co/papers/2106.13898)
* **Concept Clé :** Les Liquid Neural Networks (LNNs) avec solution fermée pour une adaptation continue post-entraînement.
* **Implémentation dans Animetix :** Cœur de notre `LiquidNeuralNetworkService` pour le traitement de signaux dynamiques.

### Foundations for Near-Term Quantum Natural Language Processing
* **ID / Source :** [arXiv:2012.03755](https://huggingface.co/papers/2012.03755)
* **Concept Clé :** QNLP, traitement du langage avec superposition et ZX-calculus.
* **Implémentation dans Animetix :** `QuantumCognitiveService` (expérimental) pour la gestion d'ambiguïté de tropes.

### Sound and Complete Neuro-symbolic Reasoning
* **ID / Source :** [arXiv:2507.09751](https://huggingface.co/papers/2507.09751)
* **Concept Clé :** IA combinant réseaux de neurones et solveurs logiques (Z3/SAT).
* **Implémentation dans Animetix :** Le `NeuroSymbolicService` prouve mathématiquement les paradoxes d'anime.

### MalAlgoQA: Pedagogical Evaluation of Counterfactual Reasoning
* **ID / Source :** [arXiv:2407.00938](https://huggingface.co/papers/2407.00938)
* **Concept Clé :** Raisonnement sur des événements irréels (what-if) logiquement cohérents.
* **Implémentation dans Animetix :** Le `CounterfactualConversationSimulator` calcule les uchronies du lore.

---
*Document généré et maintenu par le système IA d'Animetix. Mises à jour continues en fonction de l'état de l'art.*