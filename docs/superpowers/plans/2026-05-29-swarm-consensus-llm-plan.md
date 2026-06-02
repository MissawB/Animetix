# Semantic Swarm Consensus (LLM Integration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the multi-agent `SwarmConsensusOrchestrator` to a real LLM (`InferencePort`) to perform actual semantic voting consensus via a single, unified structured prompt, while retaining a robust static fallback.

**Architecture:** We add `inference_engine` in `SwarmConsensusOrchestrator`'s constructor. When a fact is proposed, we call the LLM using `inference_engine.generate_structured` with a custom Pydantic schema returning all agent votes. If `inference_engine` is absent or throws, we fallback to the keyword-matching heuristic dynamically.

**Tech Stack:** Python, Pydantic, Pytest.

---

### Task 1: Refactor `SwarmConsensusOrchestrator` for LLM Voting

**Files:**
- Modify: `backend/core/domain/services/swarm_consensus.py`

- [ ] **Step 1: Update constructor and add dynamic imports & Pydantic schema**

Open `backend/core/domain/services/swarm_consensus.py`. Import `BaseModel`, `Field` and `Dict` at the top. Modify `__init__` to accept `inference_engine`. Define the Pydantic `SwarmConsensusVotes` class.

```python
# In backend/core/domain/services/swarm_consensus.py:

from pydantic import BaseModel, Field
from typing import Dict

class SwarmConsensusVotes(BaseModel):
    votes: Dict[str, float] = Field(
        ..., 
        description="Dictionnaire associant chaque nom d'agent à son score de confiance (entre 0.0 et 1.0)."
    )
```

And update `__init__`:

```python
    def __init__(self, agent_names: Optional[List[str]] = None, inference_engine: Optional[Any] = None):
        self.agents = agent_names or ["VisualExpert", "AcousticExpert", "LoreExpert"]
        self.consensus_log: List[Dict[str, Any]] = []
        self.inference_engine = inference_engine
```

- [ ] **Step 2: Implement the unified LLM vote query helper**

Add `_get_swarm_votes_via_llm` to query the inference engine for all votes in one structured call.

```python
    def _get_swarm_votes_via_llm(self, fact: str, media: str) -> Dict[str, float]:
        """
        Query the unified inference engine for all agents' semantic confidence scores.
        """
        specialties = {
            "VisualExpert": "spécialisé dans les visuels, l'art, le dessin, l'animation et la cinématographie.",
            "AcousticExpert": "spécialisé dans la musique, les OST, les openings/endings, les voix et effets sonores.",
            "LoreExpert": "spécialisé dans le scénario, la mythologie, les personnages et la cohérence de l'univers."
        }
        
        system_prompt = (
            "Tu es l'Orchestrateur du Consensus d'Essaim (Swarm Consensus Orchestrator) d'Animetix.\n"
            "Ton rôle est de faire voter les micro-agents de l'essaim sur la véracité ou la pertinence d'un fait concernant un média (Anime/Manga).\n\n"
            "Voici la liste des agents votants et leur spécialité :\n"
            f"- VisualExpert : {specialties['VisualExpert']}\n"
            f"- AcousticExpert : {specialties['AcousticExpert']}\n"
            f"- LoreExpert : {specialties['LoreExpert']}\n\n"
            "Évalue le fait proposé et attribue à CHAQUE agent un score de confiance sémantique individuel entre 0.0 et 1.0 en fonction de sa spécialité.\n"
            "Réponds UNIQUEMENT au format JSON valide avec la clé 'votes' contenant le dictionnaire des scores. Exemple : {\"votes\": {\"VisualExpert\": 0.85, \"AcousticExpert\": 0.50, \"LoreExpert\": 0.90}}"
        )
        
        prompt = (
            f"Média : {media}\n"
            f"Fait proposé : {fact}\n\n"
            "Évalue ce fait pour chaque expert. Quel est le dictionnaire des scores ?"
        )
        
        try:
            result = self.inference_engine.generate_structured(
                prompt=prompt,
                response_model=SwarmConsensusVotes,
                system_prompt=system_prompt
            )
            if isinstance(result, SwarmConsensusVotes):
                return result.votes
            elif isinstance(result, dict) and "votes" in result:
                return {k: float(v) for k, v in result["votes"].items()}
        except Exception as e:
            logger.warning(f"⚠️ Swarm LLM evaluation failed: {e}. Falling back to keyword heuristics.")
        
        # In case of any loading failure or parsing error, return an empty dictionary to trigger the per-agent fallback
        return {}
```

- [ ] **Step 3: Refactor `propose_fact` to leverage the LLM and the robust fallback**

Modify `propose_fact` to check if `self.inference_engine` is set.
If set: fetch votes from `_get_swarm_votes_via_llm`. Fallback to `self._simulate_agent_vote` for any agent missing from the LLM dictionary.
If not set: fallback directly to simulated keyword matching for all agents.

```python
    def propose_fact(self, proposer: str, fact: str, media_title: str) -> Tuple[bool, float]:
        """
        Soumet un fait à l'essaim d'agents.
        """
        logger.info(f"🐝 Swarm: Proposing fact: '{fact}' for media '{media_title}' by agent '{proposer}'...")
        
        votes = {}
        llm_votes = {}
        if self.inference_engine:
            llm_votes = self._get_swarm_votes_via_llm(fact, media_title)
            
        for agent in self.agents:
            if agent == proposer:
                votes[agent] = 1.0  # Le proposant vote toujours pour
            elif agent in llm_votes:
                votes[agent] = llm_votes[agent]
            else:
                # Simulation de vote sémantique basé sur les mots-clés statiques
                votes[agent] = self._simulate_agent_vote(agent, fact, media_title)
                
        # Calcul du verdict (Majorité absolue s'appuyant sur un seuil de confiance de 0.6)
        positive_votes = sum(1 for a, score in votes.items() if score >= 0.6)
        majority_achieved = positive_votes > len(self.agents) / 2
        consensus_score = sum(votes.values()) / len(self.agents)
        
        verdict = {
            "media": media_title,
            "fact": fact,
            "proposer": proposer,
            "votes": votes,
            "consensus_score": consensus_score,
            "majority_achieved": majority_achieved
        }
        
        if majority_achieved:
            self.consensus_log.append(verdict)
            logger.info(f"✅ Swarm Consensus Achieved! Fact recorded (Score: {consensus_score:.2f}).")
        else:
            logger.warning(f"❌ Swarm Consensus Failed! Fact rejected (Score: {consensus_score:.2f}).")
            
        return majority_achieved, consensus_score
```

- [ ] **Step 4: Run existing tests to verify everything still compiles and passes**

Run: `.venv\Scripts\python -m pytest tests/pipeline/test_quantum_swarm.py -v`
Expected: PASS (uses the simulated fallback)

- [ ] **Step 5: Commit task 1**

```bash
git add backend/core/domain/services/swarm_consensus.py
git commit -m "feat: add unified LLM voting and fallback logic in SwarmConsensusOrchestrator"
```

---

### Task 2: Inject `inference_engine` in Dependency Injection Container

**Files:**
- Modify: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Update Dependency Injection wiring**

Open `backend/api/animetix/containers/core_services.py`. Modify `swarm_consensus_orchestrator` Singleton definition to inject `inference_engine=inference.inference_engine`.

```python
# Around line 357 in backend/api/animetix/containers/core_services.py:
    swarm_consensus_orchestrator = providers.Singleton(
        SwarmConsensusOrchestrator,
        agent_names=["VisualExpert", "AcousticExpert", "LoreExpert"],
        inference_engine=inference.inference_engine
    )
```

- [ ] **Step 2: Commit Task 2**

```bash
git add backend/api/animetix/containers/core_services.py
git commit -m "feat: inject inference_engine into swarm_consensus_orchestrator singleton"
```

---

### Task 3: Create Semantic Voting Unit Tests

**Files:**
- Modify: `tests/pipeline/test_quantum_swarm.py`

- [ ] **Step 1: Add new tests for structured LLM swarm consensus**

Open `tests/pipeline/test_quantum_swarm.py`. Add tests verifying the LLM path and the exception fallback path.

```python
# Add at the end of tests/pipeline/test_quantum_swarm.py:

def test_swarm_consensus_llm_success():
    from core.domain.services.swarm_consensus import SwarmConsensusOrchestrator, SwarmConsensusVotes
    
    mock_engine = MagicMock()
    # Mocking generate_structured to return a SwarmConsensusVotes model
    mock_votes = SwarmConsensusVotes(votes={
        "VisualExpert": 0.85,
        "AcousticExpert": 0.35,
        "LoreExpert": 0.90
    })
    mock_engine.generate_structured.return_value = mock_votes
    
    orchestrator = SwarmConsensusOrchestrator(inference_engine=mock_engine)
    
    # VisualExpert proposes, should get AcousticExpert=0.35 (below 0.6) and LoreExpert=0.90 (above 0.6)
    # Proposer VisualExpert is automatically 1.0. Majority positive votes: VisualExpert (1.0), LoreExpert (0.90) = 2/3 (absolute majority!)
    success, score = orchestrator.propose_fact(
        proposer="VisualExpert",
        fact="L'animation est de toute beauté.",
        media_title="Bleach"
    )
    
    assert success is True
    assert score == pytest.approx((1.0 + 0.35 + 0.90) / 3) # 0.75
    mock_engine.generate_structured.assert_called_once()

def test_swarm_consensus_llm_failure_fallback():
    from core.domain.services.swarm_consensus import SwarmConsensusOrchestrator
    
    mock_engine = MagicMock()
    mock_engine.generate_structured.side_effect = Exception("LLM connection timed out")
    
    orchestrator = SwarmConsensusOrchestrator(inference_engine=mock_engine)
    
    # Because LLM fails, should fallback to keyword-based simulator.
    # Proposer: VisualExpert
    # Fact contains 'musique', so AcousticExpert keyword matching gives 0.90 (>= 0.6)
    # LoreExpert doesn't match and gives 0.52 (< 0.6)
    # Proposer VisualExpert is 1.0. Majority: VisualExpert (1.0) and AcousticExpert (0.90) = 2/3 (absolute majority!)
    success, score = orchestrator.propose_fact(
        proposer="VisualExpert",
        fact="La musique de cet anime est magique.",
        media_title="Bleach"
    )
    
    assert success is True
    # Verify it executed fallback and successfully retrieved simulated scores
    assert score == pytest.approx((1.0 + 0.90 + 0.52) / 3) # 0.8066
```

- [ ] **Step 2: Run all tests in the swarm test suite to verify they pass**

Run: `.venv\Scripts\python -m pytest tests/pipeline/test_quantum_swarm.py -v`
Expected: 4 passed!

- [ ] **Step 3: Commit Task 3**

```bash
git add tests/pipeline/test_quantum_swarm.py
git commit -m "test: add SwarmConsensusOrchestrator semantic LLM and fallback unit tests"
```

---

### Task 4: Verify Full Baseline Tests

- [ ] **Step 1: Execute all pipeline test suite to verify no regression**

Run: `.venv\Scripts\python -m pytest tests/pipeline/test_quantum_swarm.py -v`
Expected: PASS

---

### Task 5: Document Completion in TODO & HISTORY

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/HISTORY.md`

- [ ] **Step 1: Update `docs/TODO.md`**

Check off the task:
```markdown
- [x] **Optimisation sémantique (Swarm Consensus)** : Connecter le consensus d'essaim `SwarmConsensusOrchestrator` à de véritables évaluations d'agents sémantiques ou de LLMs au lieu de simples correspondances de mots-clés statiques.
```

- [ ] **Step 2: Update `docs/HISTORY.md`**

Register the success log in the history document.

```markdown
- **Semantic Swarm Consensus (Single Call Paxos LLM) :** Interconnexion de `SwarmConsensusOrchestrator` avec l'API d'inférence sémantique (`InferencePort`). Implémentation d'une requête unifiée et optimisée (Option B) via un modèle Pydantic dynamique, permettant d'évaluer la véracité d'un fait proposé sous l'angle de chaque expert d'essaim (Visual, Acoustic, Lore) en un unique appel LLM pour un coût et une latence minimisés. Maintien d'un fallback algorithmique robuste par correspondance de mots-clés en cas d'indisponibilité du LLM.
```

- [ ] **Step 3: Commit documentation updates**

```bash
git add docs/TODO.md docs/HISTORY.md
git commit -m "docs: document semantic swarm consensus LLM integration"
```
