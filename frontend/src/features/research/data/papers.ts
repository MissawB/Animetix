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
    url: 'https://arxiv.org/abs/2501.12948',
    category: 'reasoning',
    keyConcept: 'Utilisation du GRPO pour entraîner des modèles au raisonnement profond par auto-correction (TTC).',
    implementation: 'Fonde notre mode Réflexion : l\'IA élabore un raisonnement interne avant de formuler sa réponse.'
  },
  {
    id: 'cove',
    title: 'Chain-of-Verification Reduces Hallucination in Large Language Models',
    source: 'arXiv:2309.11495',
    url: 'https://arxiv.org/abs/2309.11495',
    category: 'reasoning',
    keyConcept: 'Délibération via planification et réponse à des questions de vérification indépendantes.',
    implementation: 'Sert à vérifier les faits du lore anime avant de répondre, pour limiter les hallucinations.'
  },
  {
    id: 'star',
    title: 'STaR: Bootstrapping Reasoning With Reasoning',
    source: 'arXiv:2203.14465',
    url: 'https://arxiv.org/abs/2203.14465',
    category: 'reasoning',
    keyConcept: 'Amélioration itérative du raisonnement par génération de justifications et apprentissage sur les succès.',
    implementation: 'Alimente la résolution d\'énigmes complexes par raisonnement itératif.'
  },
  {
    id: 'tree-of-thoughts',
    title: 'Tree of Thoughts: Deliberate Problem Solving with LLMs',
    source: 'arXiv:2305.10601',
    url: 'https://arxiv.org/abs/2305.10601',
    category: 'reasoning',
    keyConcept: 'Exploration de branches de raisonnement avec retour en arrière (backtracking).',
    implementation: 'Guide la stratégie de questionnement d\'Akinetix en explorant plusieurs pistes de déduction.'
  },
  {
    id: 'memgpt',
    title: 'MemGPT: Towards LLMs as Operating Systems',
    source: 'arXiv:2310.08560',
    url: 'https://arxiv.org/abs/2310.08560',
    category: 'reasoning',
    keyConcept: 'Gestion hiérarchique de mémoire virtuelle paginée.',
    implementation: 'Inspire notre gestion de la mémoire à long terme des conversations.'
  },
  {
    id: 'vibethinker',
    title: 'VibeThinker-3B: Verifiable Reasoning in Small Language Models',
    source: 'arXiv:2606.16140',
    url: 'https://arxiv.org/abs/2606.16140',
    category: 'reasoning',
    keyConcept: 'Compression des aptitudes de raisonnement logico-mathématique dans des modèles de 3B paramètres.',
    implementation: 'Permet de traiter localement les requêtes de raisonnement les plus simples.'
  },
  {
    id: 'nemotron-3',
    title: 'Nemotron 3 Ultra: Hybrid Mamba-Transformer for Agentic Reasoning',
    source: 'arXiv:2606.15007',
    url: 'https://arxiv.org/abs/2606.15007',
    category: 'reasoning',
    keyConcept: 'Contrôle granulaire et dynamique du budget de réflexion (Reasoning Budget).',
    implementation: 'Ajuste l\'effort de réflexion alloué selon la complexité de la demande.'
  },
  {
    id: 'ring-attention',
    title: 'Ring Attention with Blockwise Transformers for Near-Infinite Context',
    source: 'arXiv:2310.01889',
    url: 'https://arxiv.org/abs/2310.01889',
    category: 'reasoning',
    keyConcept: 'Calcul distribué de l\'attention pour traiter des séquences quasi-infinies.',
    implementation: 'Rend possible l\'analyse de sagas entières sur de très longs contextes.'
  },
  {
    id: 'research-rl',
    title: 'ReSearch: Learning to Reason with Search for LLMs via Reinforcement Learning',
    source: 'arXiv:2503.19470',
    url: 'https://arxiv.org/abs/2503.19470',
    category: 'reasoning',
    keyConcept: 'Intégration d\'outils de recherche web directement au cœur des processus de raisonnement par apprentissage par renforcement (descendant de DeepSeek-R1).',
    implementation: 'Permet à l\'IA d\'activer d\'elle-même des outils de recherche (bases anime, actualités) au fil de son raisonnement.'
  },

  // --- AGENTS & THÉORIE DES JEUX ---
  {
    id: 'react',
    title: 'ReAct: Synergizing Reasoning and Acting in Language Models',
    source: 'arXiv:2210.03629',
    url: 'https://arxiv.org/abs/2210.03629',
    category: 'agents',
    keyConcept: 'Entrelacement des traces de raisonnement et des actions d\'appel d\'API.',
    implementation: 'Structure nos agents qui alternent raisonnement et actions pour prendre des décisions.'
  },
  {
    id: 'toolformer',
    title: 'Toolformer: LLMs Can Teach Themselves to Use Tools',
    source: 'arXiv:2302.04761',
    url: 'https://arxiv.org/abs/2302.04761',
    category: 'agents',
    keyConcept: 'Apprentissage auto-supervisé de l\'utilisation d\'API externes.',
    implementation: 'Guide la conception des outils que l\'IA sait invoquer (recherche anime, calculs).'
  },
  {
    id: 'strategic-werewolf',
    title: 'Learning Strategic Language Agents in the Werewolf Game (CFR + LLM)',
    source: 'arXiv:2502.04686',
    url: 'https://arxiv.org/abs/2502.04686',
    category: 'agents',
    keyConcept: 'Minimisation du regret contrefactuel appliquée aux dialogues LLM.',
    implementation: 'Sous-tend la stratégie de jeu d\'Akinetix et de nos modes sociaux.'
  },
  {
    id: 'moa',
    title: 'Mixture-of-Agents Enhances LLM Capabilities',
    source: 'arXiv:2406.04692',
    url: 'https://arxiv.org/abs/2406.04692',
    category: 'agents',
    keyConcept: 'Collaboration en cascade de multiples LLMs spécialistes.',
    implementation: 'Fait collaborer plusieurs experts IA (visuel, audio, lore) vers un consensus.'
  },
  {
    id: 'eureka',
    title: 'Eureka: Human-Level Reward Design via Coding Large Language Models',
    source: 'arXiv:2310.12931',
    url: 'https://arxiv.org/abs/2310.12931',
    category: 'agents',
    keyConcept: 'Utilisation des LLMs comme planificateurs de haut niveau pour écrire, compiler et auto-améliorer du code source ou des fonctions de récompense de manière itérative et évolutive.',
    implementation: 'Inspire notre laboratoire où l\'IA génère et optimise du code de calcul à la volée.'
  },

  // --- MULTIMODALITÉ ---
  {
    id: 'video-llava',
    title: 'Video-LLaVA: Learning United Visual Representation',
    source: 'arXiv:2311.10122',
    url: 'https://arxiv.org/abs/2311.10122',
    category: 'multimodal',
    keyConcept: 'Unification des espaces images/vidéos pour une compréhension temporelle.',
    implementation: 'Alimente l\'analyse et l\'indexation d\'extraits vidéo.'
  },
  {
    id: 'visual-claw',
    title: 'VisualClaw: A Real-Time, Personalized Agent for the Physical World',
    source: 'arXiv:2606.16295',
    url: 'https://arxiv.org/abs/2606.16295',
    category: 'multimodal',
    keyConcept: 'Agent multimodal doté d\'une Skill Bank auto-évolutive apprenant de ses échecs.',
    implementation: 'Permet à notre reconnaissance visuelle d\'apprendre de ses erreurs au fil du temps.'
  },
  {
    id: 'gaussian-splatting',
    title: '3D Gaussian Splatting for Real-Time Radiance Field Rendering',
    source: 'arXiv:2308.04079',
    url: 'https://arxiv.org/abs/2308.04079',
    category: 'multimodal',
    keyConcept: 'Rendu 3D temps réel à partir d\'images 2D.',
    implementation: 'Rend nos scènes 3D volumétriques (Dioramas) en temps réel.'
  },
  {
    id: 'audiolm',
    title: 'AudioLM: a Language Modeling Approach to Audio Generation',
    source: 'arXiv:2209.03143',
    url: 'https://arxiv.org/abs/2209.03143',
    category: 'multimodal',
    keyConcept: 'Modélisation de l\'audio via des tokens acoustiques discrets.',
    implementation: 'Fonde nos fonctionnalités de synthèse et de clonage vocal.'
  },

  // --- RAG & GRAPHES ---
  {
    id: 'self-rag',
    title: 'Self-RAG: Learning to Retrieve, Generate, and Critique',
    source: 'arXiv:2310.11511',
    url: 'https://arxiv.org/abs/2310.11511',
    category: 'rag',
    keyConcept: 'Récupération adaptive et auto-critique via reflection tokens.',
    implementation: 'Pilier de notre recherche augmentée : l\'IA récupère, génère puis s\'auto-critique.'
  },
  {
    id: 'matryoshka',
    title: 'Matryoshka Representation Learning',
    source: 'arXiv:2205.13147',
    url: 'https://arxiv.org/abs/2205.13147',
    category: 'rag',
    keyConcept: 'Représentations vectorielles tronquables hyper-performantes.',
    implementation: 'Optimise notre recherche sémantique par similarité.'
  },
  {
    id: 'lego-graphrag',
    title: 'LEGO-GraphRAG: Modularizing Graph-based RAG',
    source: 'arXiv:2411.05844',
    url: 'https://arxiv.org/abs/2411.05844',
    category: 'rag',
    keyConcept: 'Modularisation de l\'extraction de sous-graphes et du filtrage de chemins.',
    implementation: 'Inspire notre exploration modulaire du graphe de connaissances.'
  },
  {
    id: 'ftg-kgc',
    title: 'Filter-then-Generate: Structure-Text Adapter for Knowledge Graph Completion',
    source: 'arXiv:2412.09094',
    url: 'https://arxiv.org/abs/2412.09094',
    category: 'rag',
    keyConcept: 'Complétion de graphe (KGC) via synergie LLM et graphes ego.',
    implementation: 'Alimente la complétion et la réparation automatique du graphe de connaissances.'
  },
  {
    id: 'meancache',
    title: 'MeanCache: User-Centric Semantic Caching for LLM Web Services',
    source: 'arXiv:2403.02694',
    url: 'https://arxiv.org/abs/2403.02694',
    category: 'rag',
    keyConcept: 'Cache sémantique évitant le rappel de l\'API sur des requêtes similaires.',
    implementation: 'Met en cache les requêtes similaires pour réduire les coûts d\'inférence.'
  },
  {
    id: 'agentic-rag-survey',
    title: 'Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG',
    source: 'arXiv:2501.09136',
    url: 'https://arxiv.org/abs/2501.09136',
    category: 'rag',
    keyConcept: 'Modélisation et taxonomie des architectures de RAG Agentic selon leur autonomie, leur granularité et leurs structures de contrôle.',
    implementation: 'Sert de cadre de référence pour structurer notre recherche augmentée agentique.'
  },
  {
    id: 'evolving-orchestration',
    title: 'Experience as a Compass: Multi-agent RAG with Evolving Orchestration and Agent Prompts',
    source: 'arXiv:2604.00901',
    url: 'https://arxiv.org/abs/2604.00901',
    category: 'rag',
    keyConcept: 'Topologie évolutive et adaptation dynamique des invites (prompts) des agents selon l\'historique des requêtes et les échecs passés pour les tâches complexes multi-sauts.',
    implementation: 'Améliore la coordination de nos agents lors de l\'extraction de faits sur des sagas denses.'
  },

  // --- MLOPS & SÉCURITÉ ---
  {
    id: 's-lora',
    title: 'S-LoRA: Serving Thousands of Concurrent LoRA Adapters',
    source: 'arXiv:2311.03285',
    url: 'https://arxiv.org/abs/2311.03285',
    category: 'mlops',
    keyConcept: 'Unified Paging pour servir des milliers d\'adaptateurs LoRA simultanément.',
    implementation: 'Permet de servir de nombreuses personnalités de personnages en parallèle.'
  },
  {
    id: 'llama-guard',
    title: 'Llama Guard: LLM-based Input-Output Safeguard',
    source: 'arXiv:2312.06674',
    url: 'https://arxiv.org/abs/2312.06674',
    category: 'mlops',
    keyConcept: 'Modèle de modération agissant comme un bouclier d\'entrée/sortie.',
    implementation: 'Fonde notre bouclier de modération (détection de jailbreaks et de spoilers).'
  },
  {
    id: 'constitutional-ai',
    title: 'Constitutional AI: Harmlessness from AI Feedback',
    source: 'arXiv:2212.08073',
    url: 'https://arxiv.org/abs/2212.08073',
    category: 'mlops',
    keyConcept: 'Entraînement par auto-critique basée sur des principes (RLAIF).',
    implementation: 'Inspire notre auto-évaluation et nos tests de robustesse (red teaming).'
  },
  {
    id: 'dspy',
    title: 'DSPy: Compiling Declarative Language Model Calls',
    source: 'arXiv:2310.03714',
    url: 'https://arxiv.org/abs/2310.03714',
    category: 'mlops',
    keyConcept: 'Optimisation itérative et mathématique des prompts via compilation.',
    implementation: 'Supporte l\'optimisation automatique de nos prompts selon des métriques de qualité.'
  },
  {
    id: 'ragas',
    title: 'RAGAS: Automated Evaluation of Retrieval Augmented Generation',
    source: 'arXiv:2309.15217',
    url: 'https://arxiv.org/abs/2309.15217',
    category: 'mlops',
    keyConcept: 'Framework de métriques LLM-as-a-judge (Faithfulness, Relevance).',
    implementation: 'Calcule le score de confiance de nos réponses augmentées.'
  },
  {
    id: 'dpo',
    title: 'Direct Preference Optimization: Your LM is Secretly a Reward Model',
    source: 'arXiv:2305.18290',
    url: 'https://arxiv.org/abs/2305.18290',
    category: 'mlops',
    keyConcept: 'Alignement stable par classification de paires de préférences.',
    implementation: 'Nourrit notre alignement continu à partir des préférences des joueurs.'
  },
  {
    id: 'model-collapse',
    title: 'Is Model Collapse Inevitable? Breaking the Curse of Recursion',
    source: 'arXiv:2404.01413',
    url: 'https://arxiv.org/abs/2404.01413',
    category: 'mlops',
    keyConcept: 'Prévention de la dégénérescence par accumulation de données réelles/synthétiques.',
    implementation: 'Guide notre validation des données synthétiques et notre supervision humaine.'
  },
  {
    id: 'know-what-they-know',
    title: 'Language Models (Mostly) Know What They Know',
    source: 'arXiv:2207.05221',
    url: 'https://arxiv.org/abs/2207.05221',
    category: 'mlops',
    keyConcept: 'Quantification de l\'incertitude native via l\'entropie des logprobs.',
    implementation: 'Alimente notre mesure de confiance et nos diagnostics d\'explicabilité.'
  },
  {
    id: 'distilling-step-by-step',
    title: 'Distilling Step-by-Step! Outperforming Larger Language Models',
    source: 'arXiv:2305.02301',
    url: 'https://arxiv.org/abs/2305.02301',
    category: 'mlops',
    keyConcept: 'Distillation de la connaissance via la supervision des "rationales" des modèles géants.',
    implementation: 'Guide la distillation qui entraîne nos petits modèles locaux.'
  },
  {
    id: 'who-flips',
    title: 'Who Flips? Self- and Cross-Model Counterarguments Reveal Answer Instability in LLMs',
    source: 'arXiv:2606.16011',
    url: 'https://arxiv.org/abs/2606.16011',
    category: 'mlops',
    keyConcept: 'Étude mesurant la vulnérabilité des LLMs face à des contre-arguments plausibles mais faux (Flip Rate).',
    implementation: 'Guide la conception de nos débats IA pour résister aux contre-arguments persuasifs mais faux.'
  },
  {
    id: 'medusa',
    title: 'Medusa: Simple LLM Generation Acceleration with Multiple Decoding Heads',
    source: 'arXiv:2401.10774',
    url: 'https://arxiv.org/abs/2401.10774',
    category: 'mlops',
    keyConcept: 'Décodage spéculatif sans modèle auxiliaire en ajoutant plusieurs têtes de prédiction sur le modèle de base.',
    implementation: 'Inspire nos optimisations d\'accélération de la génération de texte.'
  },
  {
    id: 'eagle',
    title: 'EAGLE: Speculative Decoding Can Be Light-Speed',
    source: 'arXiv:2401.15077',
    url: 'https://arxiv.org/abs/2401.15077',
    category: 'mlops',
    keyConcept: 'Utilisation d\'un modèle draft ultra-léger travaillant au niveau des features pour une spéculation plus rapide.',
    implementation: 'Accélère la génération de texte de nos modèles locaux.'
  },
  {
    id: 'radix-attention',
    title: 'RadixAttention: Efficiently Serving LLMs in SGLang with RadixAttention',
    source: 'arXiv:2402.16646',
    url: 'https://arxiv.org/abs/2402.16646',
    category: 'mlops',
    keyConcept: 'Partage dynamique de KV cache à travers un arbre Radix pour les requêtes partageant des préfixes communs.',
    implementation: 'Optimise la réutilisation du cache pour accélérer les réponses de nos modèles locaux.'
  },
  {
    id: 'dr-grpo',
    title: 'Understanding R1-Zero-Like Training: A Critical Perspective (Dr. GRPO)',
    source: 'arXiv:2503.20783',
    url: 'https://arxiv.org/abs/2503.20783',
    category: 'mlops',
    keyConcept: 'Analyse critique de l\'entraînement de type R1-Zero, corrigeant les biais d\'optimisation de GRPO pour stabiliser l\'apprentissage et optimiser l\'efficacité des jetons.',
    implementation: 'Améliore la robustesse de notre boucle de fine-tuning et d\'alignement locale.'
  },

  // --- SCIENCES AVANCÉES ---
  {
    id: 'lnn',
    title: 'Closed-form Continuous-time Neural Models',
    source: 'arXiv:2106.13898',
    url: 'https://arxiv.org/abs/2106.13898',
    category: 'advanced',
    keyConcept: 'Liquid Neural Networks (LNNs) post-entraînement adaptables.',
    implementation: 'Alimente notre laboratoire de traitement audio adaptatif.'
  },
  {
    id: 'qnlp',
    title: 'Foundations for Near-Term Quantum Natural Language Processing',
    source: 'arXiv:2012.03755',
    url: 'https://arxiv.org/abs/2012.03755',
    category: 'advanced',
    keyConcept: 'Traitement du langage avec superposition et ZX-calculus.',
    implementation: 'Alimente notre laboratoire quantique pour gérer l\'ambiguïté des tropes narratifs.'
  },
  {
    id: 'neuro-symbolic',
    title: 'Sound and Complete Neuro-symbolic Reasoning',
    source: 'arXiv:2507.09751',
    url: 'https://arxiv.org/abs/2507.09751',
    category: 'advanced',
    keyConcept: 'Synergie réseaux de neurones et solveurs logiques SAT/Z3.',
    implementation: 'Alimente la preuve formelle dans notre mode Paradoxe.'
  },
  {
    id: 'counterfactual',
    title: 'MalAlgoQA: Pedagogical Evaluation of Counterfactual Reasoning',
    source: 'arXiv:2407.00938',
    url: 'https://arxiv.org/abs/2407.00938',
    category: 'advanced',
    keyConcept: 'Raisonnement sur des uchronies (What-if) cohérentes.',
    implementation: 'Alimente nos simulations d\'uchronies (et si… ?) sur le lore.'
  },
  {
    id: 'memo-games',
    title: 'MEMO: Memory-augmented model context optimization for robust multi-turn multi-agent LLM games',
    source: 'arXiv:2603.09022',
    url: 'https://arxiv.org/abs/2603.09022',
    category: 'advanced',
    keyConcept: 'Utilisation de mémoires de travail sélectives pour optimiser les contextes de modèles de langage lors de jeux multi-agents en multi-tours.',
    implementation: 'Aide Akinetix à retenir l\'historique des questions/réponses sans saturer le contexte.'
  }
];
