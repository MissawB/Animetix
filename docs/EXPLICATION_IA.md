# 🧠 Le Fonctionnement Général de l'IA d'Animetix : Du Début à la Fin

Bienvenue dans ce guide explicatif complet de l'écosystème d'Intelligence Artificielle d'**Animetix** (Anime Archetype Engine). Ce document détaille de manière pédagogique le cycle de vie complet de l'information et le fonctionnement des algorithmes d'IA, depuis la collecte brute des données jusqu'aux interactions multimodales en temps réel avec l'utilisateur.

---

## 🏛️ Vue d'ensemble du Cycle Cognitif

L'intelligence d'Animetix ne repose pas uniquement sur un grand modèle de langage (LLM) statique. C'est une architecture dynamique à **6 phases** combinant extraction de données, stockage hybride, recherche sémantique, raisonnement logique, apprentissage par renforcement et auto-évaluation continue.

```mermaid
flowchart TD
    subgraph Phase 1 : Collecte & Ingestion
        A1[Scrapers Jikan / API MAL] & A2[Scraper AnimeThemes] & A3[Synthèses Gemini / TV Tropes] --> Dagster{Orchestrateur Dagster}
    end

    subgraph Phase 2 : Structuration Multicouche
        Dagster --> B1[(SQLite DB)]
        Dagster --> B2[(JSON Files)]
        Dagster --> B3[(Neo4j Graph)]
        Dagster --> B4[(ChromaDB / PgVector)]
    end

    subgraph Phase 3 : Recherche Sémantique (RAG)
        C1[Requête Utilisateur] --> C2[Matryoshka Embedding]
        C2 --> C3[Recherche Vectorielle + Multi-Hop Neo4j]
        C3 --> C4[Cross-Encoder Reranking BGE]
    end

    subgraph Phase 4 : Agent de Raisonnement
        C4 --> D1[Thinking Model DeepSeek-R1]
        D1 --> D2[Internal Thought thought]
        D2 --> D3[Synthesis Model Llama-3]
    end

    subgraph Phase 5 : Modes Intéractifs & Multimédias
        D3 --> E1[Akinetix RL - PPO]
        D3 --> E2[Paradox Quest - Z3]
        D3 --> E3[La Forge - SDXL & Voice Cloning]
    end

    subgraph Phase 6 : MLOps & Amélioration Continue
        E1 & E2 & E3 --> F1[LLM-as-a-Judge Ragas]
        F1 --> F2[Feedback Utilisateur DPO]
        F2 --> F3[GraphHealer & Auto-Entraînement]
    end
```

---

## 🔌 Phase 1 : Collecte des Données & Ingestion Spécialisée

Toute IA de pointe dépend de la qualité de sa base de connaissances. Animetix ingère des informations spécialisées à partir de multiples API et plateformes en ligne :

1. **Jikan (API non officielle MyAnimeList)** : Récupération des métadonnées fondamentales (titres, dates, popularité, recommandations humaines et fiches de doublage/casting complets).
2. **AnimeThemes** : Compilation des titres d'openings (OP) et d'endings (ED) avec leurs interprètes officiels pour capturer la dimension musicale.
3. **IGDB (API Twitch OAuth2)** : Extraction de toutes les adaptations réelles en jeux vidéo de chaque licence.
4. **Modèles de Synthèse Spécialisés (Gemini)** : Extraction intelligente des tropes scénaristiques (clichés littéraires sur TV Tropes), des plateformes de streaming officielles actives en France (avec statut VF/VOSTFR), et des lieux réels du Japon servant d'inspiration visuelle (*Seichijunrei*).

### L'Orchestrateur Dagster
L'ensemble de ces scrapers est structuré comme des **Assets Dagster** chaînés séquentiellement. Si un scraper en amont échoue, le flux s'arrête ou applique des politiques de retry automatique avec délai pour respecter strictement les limites de requêtes (rate-limiting) des API externes.

---

## 🗄️ Phase 2 : La Structuration et le Stockage Hybride (Multi-Couches)

Une fois collectées, les données sont persistées de 4 manières complémentaires pour servir différents objectifs :

* **La Base Relationnelle (SQLite)** : Assure la cohérence transactionnelle pour les sessions utilisateurs, l'authentification et les métadonnées de base structurées.
* **Les Fichiers JSON de Référence (`clean_root_animes/mangas.json`)** : Versionnent l'état brut nettoyé des données, servant de base fiable pour l'entraînement ou la restauration rapide.
* **Le Graphe de Connaissances (Neo4j)** : Modélise les liens sémantiques profonds. Les entités (`Media`, `Studio`, `Creator`, `Character`) deviennent des nœuds connectés par des relations typées (`PRODUCED_BY`, `FEATURES`, `INFLUENCED_BY`).
* **La Base Vectorielle (PgVector / ChromaDB)** : Indexe la représentation mathématique (les embeddings) des descriptions textuelles pour permettre des comparaisons sémantiques ultra-rapides.

---

## 🔍 Phase 3 : La Recherche Intelligente (RAG - Retrieval Augmented Generation)

Lorsqu'un utilisateur pose une question (ex: *"Trouve un manga cyberpunk des années 90 qui parle de mémoire humaine"*), le système n'effectue pas une simple recherche par mots-clés. Il passe par un pipeline RAG avancé :

### 1. Encodage Vectoriel Matryoshka (MRL)
La requête est traduite en un vecteur numérique de haute dimension à l'aide d'un modèle d'embedding (Jina-v3) optimisé avec le concept de **poupées russes (Matryoshka)** :
- Une recherche "grossière" et ultra-rapide (< 10ms) est lancée sur les **128 premières dimensions** du vecteur.
- Les 50 résultats les plus proches sont ensuite réévalués en effectuant un "zoom" sur les **1024 dimensions** complètes pour une précision optimale.

### 2. Parcours Graph sémantique (Multi-Hop Traversal)
Parallèlement à la recherche vectorielle, Animetix interroge Neo4j pour traverser le graphe. Si l'utilisateur mentionne un studio ou un créateur, le graphe remonte instantanément tous les projets connectés, les personnages associés et les influences croisées.

### 3. Le Réordonnancement (Cross-Encoder Reranking)
Les documents trouvés via le vecteur et le graphe sont fusionnés et envoyés à un modèle **Cross-Encoder (BGE-Reranker)**. Contrairement aux embeddings classiques qui encodent les textes séparément, le reranker analyse la requête et chaque document conjointement pour calculer un score de pertinence absolu, ne retenant que la crème de la crème pour alimenter le prompt du LLM.

---

## 🧠 Phase 4 : L'Agent de Raisonnement (LLM & Test-Time Compute)

Pour formuler la réponse finale, le prompt enrichi par le contexte RAG est soumis à une architecture de modèles d'IA configurée en cascade selon la complexité :

### 1. Analyseur de Complexité & Test-Time Compute (TTC)
Une micro-IA évalue l'ambiguïté de la question.
- **Requête Simple** : Résolue directement par un modèle de synthèse léger (ex: Llama 3 8B) en moins d'une seconde.
- **Requête Complexe/Ambiguë** : Routée vers un modèle de raisonnement profond (Thinking Model - ex: DeepSeek-R1 Distill). Ce modèle utilise le *Test-Time Compute*, c'est-à-dire qu'il s'accorde du temps de réflexion en générant des étapes de pensée logique délimitées par les balises `<thought>...</thought>` avant de produire la réponse finale en français.

---

## 🎮 Phase 5 : Les Modes de Jeu Interactifs

L'IA d'Animetix n'est pas seulement un chatbot, elle orchestre également plusieurs mécaniques interactives complexes :

### A. Akinetix RL (Apprentissage par Renforcement)
Dans ce mode inspiré d'Akinator, l'IA doit deviner le personnage auquel pense l'utilisateur.
- Elle utilise un agent entraîné par **PPO (Proximal Policy Optimization)** dans un environnement de jeu simulé.
- L'algorithme calcule à chaque tour quelle question possède le plus haut pouvoir discriminant (entropie) pour éliminer le maximum de personnages possibles, minimisant le nombre de tours nécessaires pour gagner.

### B. Paradox Quest (IA Neuro-Symbolique)
Ce jeu de logique demande de trouver un intrus sémantique fort entre plusieurs œuvres.
- **Neuro** : Le LLM extrait les propriétés de chaque média sous forme de faits booléens.
- **Symbolique** : Ces faits sont injectés dans un solveur logique formel (**Z3 Solver**). Z3 calcule et prouve mathématiquement quel élément viole la règle logique ou constitue l'intrus (Preuve SAT).
- Le LLM traduit ensuite cette preuve logique froide en une narration ludique et accessible en français.

### C. La Forge (Génération de Médias)
Permet à l'utilisateur de fusionner des univers graphiques (ex: *Dragon Ball* dessiné dans le style du *Studio Ghibli*).
- Utilise **Stable Diffusion XL** combiné à **IP-Adapter** (pour conserver la structure et les traits caractéristiques des personnages) et **ControlNet** (pour guider la composition et la posture).
- Un service de clonage vocal (RVC) génère également la réponse textuelle parlée avec le timbre de voix exact du personnage sélectionné.

---

## 📊 Phase 6 : MLOps & Amélioration Continue (La Boucle Fermée)

L'écosystème d'Animetix s'auto-évalue et s'améliore continuellement en production :

1. **Évaluation en direct (LLM-as-a-Judge)** : Un agent critique (Scout & Critic) évalue chaque réponse générée selon les métriques Ragas :
   - **Faithfulness (Anti-hallucination)** : La réponse est-elle strictement étayée par le contexte du RAG ?
   - **Answer Relevancy (Pertinence)** : Répond-elle précisément à la question posée ?
   Si le score est insuffisant, le système déclenche une correction sémantique à la volée.
2. **Collecte de Préférences (DPO)** : Lorsque les utilisateurs cliquent sur "pouce levé" ou "pouce baissé", ces données sont enregistrées. Les échecs sont compilés sous forme de jeux de données au format `(Prompt, Choisi, Rejeté)`.
3. **Auto-entraînement (Continuous Training)** : Les datasets DPO générés déclenchent périodiquement des entraînements de modèles (LoRA) pour spécialiser l'IA sur les spécificités de la culture otaku.
4. **L'Agent d'Auto-Guérison (GraphHealer)** : Cet agent surveille Neo4j pour identifier les nœuds isolés, les relations manquantes ou incohérentes, et réécrit ou enrichit les connexions du graphe de manière autonome pour optimiser les futurs RAG.
