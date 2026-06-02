# Design Doc: Task 5 - Thinking Mode (Chain-of-Thought) in AgenticRAG

## 1. Goal
Implement a "Thinking" mode (Chain-of-Thought) for the Agentic RAG system to improve reasoning quality on complex queries.

## 2. Components

### 2.1. Prompt Engineering
Update `prompts.yaml` to include explicit instructions for agents to "think out loud" when `thinking_mode` is enabled.
Affected prompts:
- `synthesizer_final`
- `synthesizer_correction`
- `answer_judge`
- `judge_lore_expert`
- `judge_logic_auditor`
- `judge_critic`

Instruction: "If thinking_mode is enabled, start your response with a `<thought>` tag containing your detailed reasoning process before providing the final answer."

### 2.2. Streaming Parser in `AgenticRAGService`
Update `_handle_synthesize` to parse tokens on the fly:
- Maintain a state (THINKING vs ANSWERING).
- Tokens between `<thought>` and `</thought>` are yielded as `StreamStep(type="thought", ...)`.
- Tokens after `</thought>` are yielded as `StreamStep(type="token", ...)` and appended to `ctx.full_answer`.
- Exclude thought content from `ctx.full_answer` for cache/memory consistency.

### 2.3. Token Budget Enforcement
- Implement a token counter (approximate by words or characters if needed, or use a proper tokenizer if available).
- If `thinking_budget` is reached, truncate further "thought" tokens and attempt to skip to the final answer.

### 2.4. Multi-Agent Integration
- Update `DebateManager` to pass `thinking_mode` and `thinking_budget` to judges.
- Ensure `robust_json_loads` handles the thought prefix correctly (it already seems to do so by finding the first `{`).

## 3. Data Flow
1. `_assess_complexity` determines `thinking_mode` and `thinking_budget`.
2. `_handle_synthesize` calls `synthesizer.synthesize_stream`.
3. The stream is processed by a new `ThinkingParser` class/method.
4. UI receives separate `thought` and `token` events.

## 4. Testing Strategy
- Mock the inference engine to return strings with `<thought>` tags.
- Verify that `StreamStep` objects have the correct type.
- Verify that `ctx.full_answer` does NOT contain the thought.
- Verify that `thinking_budget` stops the thought streaming.
