# VS Battle Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a VS Battle game where users can compare two characters, with a multi-agent debate and final verdict based on power-scaling data from Fandom wikis.

**Architecture:** Hexagonal Architecture (Ports and Adapters). A new `VsBattleService` will orchestrate data fetching via a specialized `FandomAdapter` and simulate a combat debate using `InferencePort` and `MultiAgentBus` patterns.

**Tech Stack:** Python 3.10, Django, Pydantic, MediaWiki API (Fandom), LLM (InferencePort).

---

### Task 1: Define Entities

**Files:**
- Modify: `src/core/domain/entities/ai_schemas.py`

- [ ] **Step 1: Add CombatCharacter and CombatResult schemas**

```python
class CombatStats(BaseModel):
    tier: str = Field(description="Attack Potency Tier (e.g., 2-C)")
    speed: str = Field(description="Combat and Reaction speed")
    durability: str = Field(description="Durability and Stamina")
    intelligence: str = Field(description="Combat IQ and Strategy")
    abilities: List[str] = Field(default_factory=list, description="Hax and Special Powers")

class CombatCharacter(BaseModel):
    name: str
    wiki_url: str
    stats: CombatStats
    summary: str

class DebateTurn(BaseModel):
    agent: str # 'Advocate_A', 'Advocate_B', 'Judge'
    content: str

class CombatResult(BaseModel):
    character_a: CombatCharacter
    character_b: CombatCharacter
    debate_history: List[DebateTurn]
    winner: str
    verdict_summary: str
```

- [ ] **Step 2: Commit Entities**
```bash
git add src/core/domain/entities/ai_schemas.py
git commit -m "feat(domain): add combat entities for vs-battle game"
```

---

### Task 2: Implement Fandom Adapter

**Files:**
- Create: `src/core/ports/fandom_port.py`
- Create: `src/adapters/persistence/fandom_adapter.py`
- Modify: `src/backend/animetix/containers.py`

- [ ] **Step 1: Create FandomPort**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class FandomPort(ABC):
    @abstractmethod
    def fetch_character_data(self, character_name: str) -> Dict[str, Any]:
        """Fetches character data from VS Battles Wiki."""
        pass
```

- [ ] **Step 2: Implement FandomAdapter**
Using `requests` to call the MediaWiki API of `vsbattles.fandom.com`.

- [ ] **Step 3: Register in containers.py**

- [ ] **Step 4: Commit Adapter**
```bash
git add src/core/ports/fandom_port.py src/adapters/persistence/fandom_adapter.py src/backend/animetix/containers.py
git commit -m "feat(adapters): add FandomPort and adapter for VS Battles Wiki"
```

---

### Task 3: Add Battle Prompts

**Files:**
- Modify: `src/core/domain/services/prompts/prompts.yaml`

- [ ] **Step 1: Add advocate and judge prompts**
Include specific instructions for "Analytical focus with Hype style".

- [ ] **Step 2: Commit Prompts**
```bash
git add src/core/domain/services/prompts/prompts.yaml
git commit -m "feat(prompts): add vs_battle_advocate and vs_battle_judge prompts"
```

---

### Task 4: Implement VsBattleService

**Files:**
- Create: `src/core/domain/services/creative/vs_battle_service.py`
- Test: `tests/core/domain/services/creative/test_vs_battle_service.py`

- [ ] **Step 1: Write the failing test for battle orchestration**
- [ ] **Step 2: Implement VsBattleService logic**
    - `fetch_and_parse(char_name)`
    - `run_debate(char_a, char_b)`
- [ ] **Step 3: Run tests and verify**
- [ ] **Step 4: Commit Service**

---

### Task 5: Backend Integration (View & URL)

**Files:**
- Modify: `src/backend/animetix/views/media_games.py`
- Modify: `src/backend/animetix/urls.py`

- [ ] **Step 1: Add VS Battle view**
    - Support for manual selection.
    - Call `VsBattleService`.
- [ ] **Step 2: Add URL pattern**
- [ ] **Step 3: Commit Integration**
```bash
git add src/backend/animetix/views/media_games.py src/backend/animetix/urls.py
git commit -m "feat(backend): integrate VS Battle game view and URLs"
```
