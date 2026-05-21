from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# --- AGENTIC RAG 2.0 SCHEMAS ---

class JudgeAction(str, Enum):
    APPROVE = "APPROVE"
    REWRITE = "REWRITE"
    RESEARCH_MORE = "RESEARCH_MORE"
    REPLAN = "REPLAN"

class SearchPlan(BaseModel):
    optimized_query: str = Field(description="Query optimized for the search engine.")
    entities: List[str] = Field(default_factory=list, description="Key entities identified in the query.")
    requires_web: bool = Field(default=False, description="Whether web search is required to answer the query.")
    requires_graph: bool = Field(default=False, description="Whether graph exploration (Cypher) is required for complex relationships.")
    requires_saga: bool = Field(default=False, description="Whether saga executive summary is required for macro-context.")
    is_visual_query: bool = Field(default=False, description="Whether the query involves visual analysis (e.g. poster, visual vibe).")
    graph_traversal_steps: List[str] = Field(default_factory=list, description="List of relationship types to follow in the graph.")
    reasoning: str = Field(description="Brief explanation of the search strategy.")

class CritiqueResult(BaseModel):
    is_relevant: bool
    relevance_score: float # 0.0 to 1.0
    missing_info: Optional[str] = None
    suggested_action: str # 'RETRY_LOCAL', 'TRIGGER_WEB', 'PROCEED'

class FinalSynthesis(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float

# --- REAL-TIME EVALUATION (LooP) SCHEMAS ---

class JudgeEvaluation(BaseModel):
    faithfulness_score: float = Field(ge=0, le=1.0)
    relevancy_score: float = Field(ge=0, le=1.0)
    hallucination_detected: bool
    reasoning: str
    is_reliable: bool
    next_action: JudgeAction

class DebateOutcome(BaseModel):
    critiques: Dict[str, JudgeEvaluation] = Field(description="Critiques from specialized agents.")
    consensus_action: JudgeAction = Field(description="Final action decided by the Debate Manager.")
    final_reasoning: str = Field(description="Summary of the debate and final decision.")

# --- LEGACY SCHEMAS (Internal mapping) ---

class AgenticAnalysis(BaseModel):
    entities: List[str] = Field(default_factory=list)
    requires_web: bool = False
    search_query: str

class AgenticCritique(BaseModel):
    is_sufficient: bool
    missing_info: Optional[str] = None
    new_search_query: Optional[str] = None

class CoVePlan(BaseModel):
    verification_questions: List[str] = Field(default_factory=list)

class ParadoxLogic(BaseModel):
    reasoning: str
    scenario: str

class RagasReport(BaseModel):
    avg_faithfulness: float
    avg_answer_relevancy: float
    timestamp: str

class StreamStep(BaseModel):
    type: str # 'thought' or 'token' or 'eval'
    content: Any

class RAGState(str, Enum):
    """États de la machine à états RAG."""
    ANALYZE = "ANALYZE"
    PLAN = "PLAN"
    SAGA_LOOKUP = "SAGA_LOOKUP"
    GRAPH_EXPLORE = "GRAPH_EXPLORE"
    RESEARCH = "RESEARCH"
    ACQUIRE_KNOWLEDGE = "ACQUIRE_KNOWLEDGE"
    SPECULATE = "SPECULATE"
    VLM_RERANK = "VLM_RERANK"
    SYNTHESIZE = "SYNTHESIZE"
    JUDGE = "JUDGE"
    FINALIZE = "FINALIZE"
    FALLBACK_RAG = "FALLBACK_RAG"
    FAILED = "FAILED"

class RAGContext(BaseModel):
    """Contexte de la session RAG agentique."""
    model_config = {"arbitrary_types_allowed": True}

    query: str
    media_type: str
    user_id: Optional[str] = None
    thinking_budget: int = 0
    thinking_mode: bool = False
    memories: str = ""
    plan: Optional[SearchPlan] = None
    raw_context: str = ""
    candidates: List[Dict] = Field(default_factory=list)
    truth_path: str = ""
    full_answer: str = ""
    correction_feedback: Optional[str] = None
    iteration: int = 0
    max_iterations: int = 10
    knowledge_acquired: bool = False
    saga_name: Optional[str] = None
    current_state: RAGState = RAGState.ANALYZE
    graph_expert: Any = None # To avoid circular imports
    visual_context: Optional[str] = None
    image_paths: List[str] = Field(default_factory=list)
    debate_outcome: Optional[DebateOutcome] = None

# --- FORGE AGENT SCHEMAS ---

class ForgeHypothesis(BaseModel):
    hypothesis: str
    rationale: str
    confidence: float

# --- GRAPH EXTRACTION SCHEMAS ---

class GraphEntity(BaseModel):
    name: str = Field(description="Nom de l'entité (ex: Naruto Uzumaki, Konoha)")
    type: str = Field(description="Type de l'entité (ex: Personnage, Lieu, Clan, Technique)")
    description: str = Field(description="Brève description de l'entité")

class GraphRelation(BaseModel):
    source: str = Field(description="Nom de l'entité source")
    target: str = Field(description="Nom de l'entité cible")
    relation: str = Field(description="Nature de la relation (ex: MEMBRE_DE, RIVAL_DE, MAITRISE)")
    description: str = Field(description="Description ou contexte de la relation")

class GraphExtraction(BaseModel):
    entities: List[GraphEntity] = Field(default_factory=list)
    relations: List[GraphRelation] = Field(default_factory=list)

# --- VS BATTLE GAME SCHEMAS ---

class CombatStats(BaseModel):
    tier: str = Field(description="Attack Potency Tier (e.g., 2-C)")
    tier_value: int = Field(default=0, description="Normalized power scale (0-100)")
    speed: str = Field(description="Combat and Reaction speed")
    durability: str = Field(description="Durability and Stamina")
    intelligence: str = Field(description="Combat IQ and Strategy")
    abilities: List[str] = Field(default_factory=list, description="Hax and Special Powers")

class CombatCharacter(BaseModel):
    name: str = Field(description="Name of the character.")
    image_url: Optional[str] = Field(default=None, description="URL of the character portrait")
    wiki_url: str = Field(description="Source URL for character statistics (e.g. VS Battles Wiki).")
    stats: CombatStats = Field(description="Structured combat statistics and abilities.")
    summary: str = Field(description="Brief summary of the character's background and powers.")

class DebateTurn(BaseModel):
    agent: str = Field(description="Role: 'Advocate_A', 'Advocate_B', or 'Judge'")
    content: str = Field(description="The actual argument or verdict text provided by the agent.")

class CombatResult(BaseModel):
    character_a: CombatCharacter = Field(description="The first combatant.")
    character_b: CombatCharacter = Field(description="The second combatant.")
    debate_history: List[DebateTurn] = Field(default_factory=list, description="Chronological record of the debate turns.")
    winner: str = Field(description="Name of the winning character.")
    verdict_summary: str = Field(description="Detailed explanation of the final decision and scaling factors.")
