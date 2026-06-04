# Thinking Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Chain-of-Thought (Thinking) mode in AgenticRAG to improve reasoning on complex queries.

**Architecture:**
1. Update prompts to instruct LLM to use `<thought>` tags.
2. Implement a streaming parser in `AgenticRAGService._handle_synthesize` to separate thoughts from answer tokens.
3. Enforce token budget for thinking.
4. Enable thinking mode for multi-agent judges.

**Tech Stack:** Python, Pydantic, YAML.

---

### Task 1: Prompt Engineering

**Files:**
- Modify: `backend/core/domain/services/prompts/prompts.yaml`

- [ ] **Step 1: Update synthesizer and judge prompts**
Add thinking instructions to `synthesizer_final`, `synthesizer_correction`, `answer_judge`, `judge_lore_expert`, `judge_logic_auditor`, and `judge_critic`.

```yaml
# Add to synthesizer_final and synthesizer_correction templates:
# "Si `thinking_mode` est activé (budget > 0), tu DOIS commencer ta réponse par une balise `<thought>` contenant ton raisonnement détaillé, tes doutes et tes vérifications logiques avant de fournir le JSON final."

# Add to judge templates similarly.
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/prompts/prompts.yaml
git commit -m "prompts: add thinking mode instructions to synthesizer and judges"
```

### Task 2: Implement Thinking Parser in AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`

- [ ] **Step 1: Update `_handle_synthesize` to parse `<thought>` tags**

```python
    def _handle_synthesize(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if ctx.correction_feedback:
            yield StreamStep(type="thought", content="[Synthesizer] Tentative d'auto-correction...").model_dump()
        else:
            yield StreamStep(type="thought", content="[Synthesizer] Rédaction de la réponse expert...").model_dump()
        
        ctx.full_answer = ""
        syn_start = time.time()
        
        in_thought = False
        thought_buffer = ""
        token_count = 0
        
        for token in self.synthesizer.synthesize_stream(
            ctx.query, 
            ctx.truth_path, 
            thinking_budget=ctx.thinking_budget, 
            thinking_mode=ctx.thinking_mode,
            correction_feedback=ctx.correction_feedback
        ):
            # Simple token estimation
            token_count += 1
            
            if "<thought>" in token or "thought" in token.lower() and not in_thought:
                if "<thought>" in token:
                    in_thought = True
                    # Yield content after <thought> if any
                    parts = token.split("<thought>", 1)
                    if parts[1]:
                        yield StreamStep(type="thought", content=parts[1]).model_dump()
                    continue

            if "</thought>" in token and in_thought:
                in_thought = False
                parts = token.split("</thought>", 1)
                if parts[0]:
                    yield StreamStep(type="thought", content=parts[0]).model_dump()
                if parts[1]:
                    ctx.full_answer += parts[1]
                    yield StreamStep(type="token", content=parts[1]).model_dump()
                continue

            if in_thought:
                if ctx.thinking_budget > 0 and token_count > ctx.thinking_budget:
                    # Truncate thought if budget exceeded
                    continue
                yield StreamStep(type="thought", content=token).model_dump()
            else:
                ctx.full_answer += token
                yield StreamStep(type="token", content=token).model_dump()
        
        logger.info(f"PERF: Synthesizer took {(time.time() - syn_start)*1000:.2f}ms")
        # ... rest of method
```

- [ ] **Step 2: Commit**
```bash
git add backend/core/domain/services/agentic_rag_service.py
git commit -m "feat: implement thinking parser in AgenticRAGService"
```

### Task 3: Enable Thinking for Multi-Agent Debate

**Files:**
- Modify: `backend/core/domain/services/rag/agents/debate_manager.py`

- [ ] **Step 1: Pass thinking parameters to judges**

```python
    def conduct_debate(self, query: str, context: str, answer: str, thinking_budget: int = 0, thinking_mode: bool = False) -> DebateOutcome:
        critiques: Dict[str, JudgeEvaluation] = {}
        judges = ["judge_lore_expert", "judge_logic_auditor", "judge_critic"]
        
        for j_key in judges:
            try:
                prompt, sys = self.prompt_manager.get_prompt(j_key, query=query, context=context, answer=answer)
                # Pass thinking params
                raw = self.llm_service.generate(
                    prompt, sys, 
                    use_slm=True, 
                    thinking_budget=thinking_budget // 3, # Split budget among judges
                    thinking_mode=thinking_mode
                )
                # ... rest of logic
```

- [ ] **Step 2: Update `AgenticRAGService._handle_judge` to pass parameters**

```python
    def _handle_judge(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        # ...
        outcome = self.debate_manager.conduct_debate(
            ctx.query, ctx.truth_path, ctx.full_answer,
            thinking_budget=ctx.thinking_budget,
            thinking_mode=ctx.thinking_mode
        )
        # ...
```

- [ ] **Step 3: Commit**
```bash
git add backend/core/domain/services/rag/agents/debate_manager.py backend/core/domain/services/agentic_rag_service.py
git commit -m "feat: enable thinking mode for multi-agent debate"
```

### Task 4: Verification

- [ ] **Step 1: Create a test script**
Create `scripts/verify_thinking_mode.py` that mocks the inference engine and checks if thoughts are streamed separately and answer is clean.

- [ ] **Step 2: Run verification**
Run: `python scripts/verify_thinking_mode.py`
Expected: 
- Stream contains `type="thought"` events.
- `ctx.full_answer` does not contain `<thought>` content.
- `thinking_budget` stops the thought stream.

- [ ] **Step 3: Commit**
```bash
git add scripts/verify_thinking_mode.py
git commit -m "test: add verification script for thinking mode"
```
