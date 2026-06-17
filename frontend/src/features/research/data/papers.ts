export interface ResearchPaper {
  id: string;
  title: string;
  source: string;
  url: string;
  keyConcept: string;
  implementation: string;
  category: 'reasoning' | 'agents' | 'multimodal' | 'rag' | 'mlops' | 'advanced';
}

export const researchPapers: ResearchPaper[] = [
  // --- RAISONNEMENT & MÉMOIRE ---
  {
    id: 'deepseek-r1',
    title: 'DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning',
    source: 'arXiv:2501.12948',
    url: 'https://huggingface.co/papers/2501.12948',
    category: 'reasoning',
    keyConcept: 'Utilisation du GRPO pour entraîner des modèles au raisonnement profond par auto-correction (TTC).',
    implementation: 'Fondement de notre "Thinking Mode". L\'IA génère une trace de pensée interne <thought> avant de répondre.'
  },
  {
    id: 'cove',
    title: 'Chain-of-Verification Reduces Hallucination in Large Language Models',
    source: 'arXiv:2309.11495',
    url: 'https://huggingface.co/papers/2309.11495',
    category: 'reasoning',
    keyConcept: 'Délibération via planification et réponse à des questions de vérification indépendantes.',
    implementation: 'Implémenté dans le CoveOracleService pour valider les faits du lore anime.'
  },
  {
    id: 'star',
    title: 'STaR: Bootstrapping Reasoning With Reasoning',
    source: 'arXiv:2203.14465',
    url: 'https://huggingface.co/papers/2203.14465',
    category: 'reasoning',
    keyConcept: 'Amélioration itérative du raisonnement par génération de justifications et apprentissage sur les succès.',
    implementation: 'Cœur du StarReasonerService pour la résolution d\'énigmes complexes.'
  },
  {
    id: 'tree-of-thoughts',
    title: 'Tree of Thoughts: Deliberate Problem Solving with LLMs',
    source: 'arXiv:2305.10601',
    url: 'https://huggingface.co/papers/2305.10601',
    category: 'reasoning',
    keyConcept: 'Exploration de branches de raisonnement avec retour en arrière (backtracking).',
    implementation: 'Utilisé dans le TreeOfThoughtsSearchService pour l\'optimisation d\'Akinetix.'
  },
  {
    id: 'memgpt',
    title: 'MemGPT: Towards LLMs as Operating Systems',
    source: 'arXiv:2310.08560',
    url: 'https://huggingface.co/papers/2310.08560',
    category: 'reasoning',
    keyConcept: 'Gestion hiérarchique de mémoire virtuelle paginée.',
    implementation: 'Inspiration de l\'EpisodicMemoryCompressor pour la mémoire à long terme.'
  },
  {
    id: 'vibethinker',
    title: 'VibeThinker-3B: Verifiable Reasoning in Small Language Models',
    source: 'HF Daily Papers (2026)',
    url: 'https://huggingface.co/papers/2606.16140',
    category: 'reasoning',
    keyConcept: 'Compression des aptitudes de raisonnement logico-mathématique dans des modèles de 3B paramètres.',
    implementation: 'Utilisé dans le CompactReasoningAdapter pour décharger les requêtes de niveau 1 & 2.'
  },
  {
    id: 'nemotron-3',
    title: 'Nemotron 3 Ultra: Hybrid Mamba-Transformer for Agentic Reasoning',
    source: 'HF Daily Papers (2026)',
    url: 'https://huggingface.co/papers/2606.15007',
    category: 'reasoning',
    keyConcept: 'Contrôle granulaire et dynamique du budget de réflexion (Reasoning Budget).',
    implementation: 'Refonte du ComplexityAnalyser pour une allocation granulaire du budget TTC.'
  },
  {
    id: 'ring-attention',
    title: 'Ring Attention with Blockwise Transformers for Near-Infinite Context',
    source: 'arXiv:2310.01889',
    url: 'https://huggingface.co/papers/2310.01889',
    category: 'reasoning',
    keyConcept: 'Calcul distribué de l\'attention pour traiter des séquences quasi-infinies.',
    implementation: 'Supporte le LongContextDiscoveryService pour l\'analyse de sagas entières.'
  },

  // --- AGENTS & THÉORIE DES JEUX ---
  {
    id: 'react',
    title: 'ReAct: Synergizing Reasoning and Acting in Language Models',
    source: 'arXiv:2210.03629',
    url: 'https://huggingface.co/papers/2210.03629',
    category: 'agents',
    keyConcept: 'Entrelacement des traces de raisonnement et des actions d\'appel d\'API.',
    implementation: 'Architecture centrale du DynamicToolAgent pour la prise de décision interactive.'
  },
  {
    id: 'toolformer',
    title: 'Toolformer: LLMs Can Teach Themselves to Use Tools',
    source: 'arXiv:2302.04761',
    url: 'https://huggingface.co/papers/2302.04761',
    category: 'agents',
    keyConcept: 'Apprentissage auto-supervisé de l\'utilisation d\'API externes.',
    implementation: 'Conception des outils dynamiques (Jikan API, calculs internes) dans l\'orchestrateur.'
  },
  {
    id: 'strategic-werewolf',
    title: 'Learning Strategic Language Agents in the Werewolf Game (CFR + LLM)',
    source: 'arXiv:2502.04686',
    url: 'https://huggingface.co/papers/2502.04686',
    category: 'agents',
    keyConcept: 'Minimisation du regret contrefactuel appliquée aux dialogues LLM.',
    implementation: 'Moteur du CFRGameSolver et d\'AkinetixEngine.'
  },
  {
    id: 'moa',
    title: 'Mixture-of-Agents Enhances LLM Capabilities',
    source: 'arXiv:2406.04692',
    url: 'https://huggingface.co/papers/2406.04692',
    category: 'agents',
    keyConcept: 'Collaboration en cascade de multiples LLMs spécialistes.',
    implementation: 'Utilisé dans le SwarmConsensusOrchestrator (Visual, Acoustic, Lore experts).'
  },

  // --- MULTIMODALITÉ ---
  {
    id: 'video-llava',
    title: 'Video-LLaVA: Learning United Visual Representation',
    source: 'arXiv:2311.10122',
    url: 'https://huggingface.co/papers/2311.10122',
    category: 'multimodal',
    keyConcept: 'Unification des espaces images/vidéos pour une compréhension temporelle.',
    implementation: 'Moteur du VideoLanguageIndexingService pour l\'analyse d\'extraits.'
  },
  {
    id: 'visual-claw',
    title: 'VisualClaw: A Real-Time, Personalized Agent for the Physical World',
    source: 'arXiv:2606.16295',
    url: 'https://huggingface.co/papers/2606.16295',
    category: 'multimodal',
    keyConcept: 'Agent multimodal doté d\'une Skill Bank auto-évolutive apprenant de ses échecs.',
    implementation: 'Boucle d\'auto-évolution du Video-RAG pour corriger les erreurs de reconnaissance.'
  },
  {
    id: 'gaussian-splatting',
    title: '3D Gaussian Splatting for Real-Time Radiance Field Rendering',
    source: 'arXiv:2308.04079',
    url: 'https://huggingface.co/papers/2308.04079',
    category: 'multimodal',
    keyConcept: 'Rendu 3D temps réel à partir d\'images 2D.',
    implementation: 'Cœur du CinematicVolumetricReconstructionService (Dioramas 3D).'
  },
  {
    id: 'audiolm',
    title: 'AudioLM: a Language Modeling Approach to Audio Generation',
    source: 'arXiv:2209.03143',
    url: 'https://huggingface.co/papers/2209.03143',
    category: 'multimodal',
    keyConcept: 'Modélisation de l\'audio via des tokens acoustiques discrets.',
    implementation: 'Base du NativeSpeechLLMService et du VoiceCloningService.'
  },

  // --- RAG & GRAPHES ---
  {
    id: 'self-rag',
    title: 'Self-RAG: Learning to Retrieve, Generate, and Critique',
    source: 'arXiv:2310.11511',
    url: 'https://huggingface.co/papers/2310.11511',
    category: 'rag',
    keyConcept: 'Récupération adaptive et auto-critique via reflection tokens.',
    implementation: 'Pilier de l\'AgenticRAGService et du rag_orchestrator.py.'
  },
  {
    id: 'matryoshka',
    title: 'Matryoshka Representation Learning',
    source: 'arXiv:2205.13147',
    url: 'https://huggingface.co/papers/2205.13147',
    category: 'rag',
    keyConcept: 'Représentations vectorielles tronquables hyper-performantes.',
    implementation: 'Optimisation de la Vector DB ChromaDB pour la recherche sémantique.'
  },
  {
    id: 'lego-graphrag',
    title: 'LEGO-GraphRAG: Modularizing Graph-based RAG',
    source: 'arXiv:2411.05844',
    url: 'https://huggingface.co/papers/2411.05844',
    category: 'rag',
    keyConcept: 'Modularisation de l\'extraction de sous-graphes et du filtrage de chemins.',
    implementation: 'Inspire le HierarchicalGraphRAGService et l\'agent Scout.'
  },
  {
    id: 'ftg-kgc',
    title: 'Filter-then-Generate: Structure-Text Adapter for Knowledge Graph Completion',
    source: 'arXiv:2412.09094',
    url: 'https://huggingface.co/papers/2412.09094',
    category: 'rag',
    keyConcept: 'Complétion de graphe (KGC) via synergie LLM et graphes ego.',
    implementation: 'Cœur du GraphHealerService pour la cicatrisation de Neo4j.'
  },
  {
    id: 'meancache',
    title: 'MeanCache: User-Centric Semantic Caching for LLM Web Services',
    source: 'arXiv:2403.02694',
    url: 'https://huggingface.co/papers/2403.02694',
    category: 'rag',
    keyConcept: 'Cache sémantique évitant le rappel de l\'API sur des requêtes similaires.',
    implementation: 'Utilisé dans le SemanticCacheService pour réduire les coûts.'
  },

  // --- MLOPS & SÉCURITÉ ---
  {
    id: 's-lora',
    title: 'S-LoRA: Serving Thousands of Concurrent LoRA Adapters',
    source: 'arXiv:2311.03285',
    url: 'https://huggingface.co/papers/2311.03285',
    category: 'mlops',
    keyConcept: 'Unified Paging pour servir des milliers d\'adaptateurs LoRA simultanément.',
    implementation: 'L\'épine dorsale du MultiLoraManager pour les personnalités de personnages.'
  },
  {
    id: 'llama-guard',
    title: 'Llama Guard: LLM-based Input-Output Safeguard',
    source: 'arXiv:2312.06674',
    url: 'https://huggingface.co/papers/2312.06674',
    category: 'mlops',
    keyConcept: 'Modèle de modération agissant comme un bouclier d\'entrée/sortie.',
    implementation: 'Socle du GuardrailService pour la détection de Jailbreaks et Spoilers.'
  },
  {
    id: 'constitutional-ai',
    title: 'Constitutional AI: Harmlessness from AI Feedback',
    source: 'arXiv:2212.08073',
    url: 'https://huggingface.co/papers/2212.08073',
    category: 'mlops',
    keyConcept: 'Entraînement par auto-critique basée sur des principes (RLAIF).',
    implementation: 'Inspire le Red Teaming Agent et l\'auto-évaluation du Juge de débat.'
  },
  {
    id: 'dspy',
    title: 'DSPy: Compiling Declarative Language Model Calls',
    source: 'arXiv:2310.03714',
    url: 'https://huggingface.co/papers/2310.03714',
    category: 'mlops',
    keyConcept: 'Optimisation itérative et mathématique des prompts via compilation.',
    implementation: 'Supporte le DSPyPromptOptimizer pour maximiser les métriques de qualité.'
  },
  {
    id: 'ragas',
    title: 'RAGAS: Automated Evaluation of Retrieval Augmented Generation',
    source: 'arXiv:2309.15217',
    url: 'https://huggingface.co/papers/2309.15217',
    category: 'mlops',
    keyConcept: 'Framework de métriques LLM-as-a-judge (Faithfulness, Relevance).',
    implementation: 'Calcule le Trust Score via le RagasEvalService.'
  },
  {
    id: 'dpo',
    title: 'Direct Preference Optimization: Your LM is Secretly a Reward Model',
    source: 'arXiv:2305.18290',
    url: 'https://huggingface.co/papers/2305.18290',
    category: 'mlops',
    keyConcept: 'Alignement stable par classification de paires de préférences.',
    implementation: 'Nourrit le DPOFeedbackLoop pour l\'alignement continu.'
  },
  {
    id: 'model-collapse',
    title: 'Is Model Collapse Inevitable? Breaking the Curse of Recursion',
    source: 'arXiv:2404.01413',
    url: 'https://huggingface.co/papers/2404.01413',
    category: 'mlops',
    keyConcept: 'Prévention de la dégénérescence par accumulation de données réelles/synthétiques.',
    implementation: 'Fonde le SyntheticValidationService et l\'Universal HITL Gate.'
  },
  {
    id: 'know-what-they-know',
    title: 'Language Models (Mostly) Know What They Know',
    source: 'arXiv:2207.05221',
    url: 'https://huggingface.co/papers/2207.05221',
    category: 'mlops',
    keyConcept: 'Quantification de l\'incertitude native via l\'entropie des logprobs.',
    implementation: 'Mesure de confiance native dans le XaiDiagnosticService.'
  },

  // --- SCIENCES AVANCÉES ---
  {
    id: 'lnn',
    title: 'Closed-form Continuous-time Neural Models',
    source: 'arXiv:2106.13898',
    url: 'https://huggingface.co/papers/2106.13898',
    category: 'advanced',
    keyConcept: 'Liquid Neural Networks (LNNs) post-entraînement adaptables.',
    implementation: 'Cœur du LiquidNeuralNetworkService pour le traitement audio.'
  },
  {
    id: 'qnlp',
    title: 'Foundations for Near-Term Quantum Natural Language Processing',
    source: 'arXiv:2012.03755',
    url: 'https://huggingface.co/papers/2012.03755',
    category: 'advanced',
    keyConcept: 'Traitement du langage avec superposition et ZX-calculus.',
    implementation: 'QuantumCognitiveService pour la gestion d\'ambiguïté de tropes.'
  },
  {
    id: 'neuro-symbolic',
    title: 'Sound and Complete Neuro-symbolic Reasoning',
    source: 'arXiv:2507.09751',
    url: 'https://huggingface.co/papers/2507.09751',
    category: 'advanced',
    keyConcept: 'Synergie réseaux de neurones et solveurs logiques SAT/Z3.',
    implementation: 'NeuroSymbolicService pour la preuve formelle des paradoxes.'
  },
  {
    id: 'counterfactual',
    title: 'MalAlgoQA: Pedagogical Evaluation of Counterfactual Reasoning',
    source: 'arXiv:2407.00938',
    url: 'https://huggingface.co/papers/2407.00938',
    category: 'advanced',
    keyConcept: 'Raisonnement sur des uchronies (What-if) cohérentes.',
    implementation: 'CounterfactualConversationSimulator pour les simulations de lore.'
  }
];
