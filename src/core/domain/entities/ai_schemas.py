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
    optimized_query: str
    entities: List[str] = Field(default_factory=list)
    requires_web: bool = False
    requires_graph: bool = False
    is_visual_query: bool = False
    graph_traversal_steps: List[str] = Field(default_factory=list, description="List of relationship types to follow in the graph.")
    reasoning: Optional[str] = None

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
