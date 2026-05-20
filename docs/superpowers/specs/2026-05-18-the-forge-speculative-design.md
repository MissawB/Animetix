# Design Spec: The Forge (Speculative Logic Engine)

**Date:** 2026-05-18
**Status:** Approved
**Topic:** Implementing logic-based gap filling for Animetix Ultra+.

## 1. Problem Statement
Even with real-time Web/Jikan access (The Librarian), some information is simply unavailable (e.g., future release dates, unannounced sequels). Instead of returning a generic "I don't know," the system should provide value by analyzing existing data patterns to offer logical, informed hypotheses.

## 2. Proposed Solution
Introduce `The Forge` agent. When factual retrieval fails, the system transitions to a speculative mode. `The Forge` cross-references the Neo4j graph for similar entities (same studio, same author, same genre popularity) to deduce the most likely answer, while explicitly tagging it as a "Logic-Based Hypothesis."

## 3. Architecture

### A. The Forge Agent (`src/core/domain/services/rag/agents/forge.py`)
- New agent class.
- Responsibility: Pattern-based deduction.
- Logic:
    1. **Context Harvesting**: Gathers all available meta-data about the subject (even if the specific fact is missing).
    2. **Pattern Matching**: Looks for historical precedents in the graph (e.g., "How long does Studio MAPPA take between a manga's end and an anime's final season?").
    3. **Hypothesis Generation**: Formulates a reasoned guess based on these patterns.

### B. State Machine Integration
- New State: `SPECULATE`.
- Trigger: `ACQUIRE_KNOWLEDGE` (Librarian) returns "No data found" OR `JudgeAction.RESEARCH_MORE` fails after 2 attempts.
- Output: A reasoned hypothesis injected into the `Truth Path` with a `[SPECULATION]` prefix.

### C. Speculation Guardrails
- **Disclaimer**: The synthesizer must wrap any Forge-generated data with a clear disclaimer: *"Bien que l'information officielle soit absente, une analyse des patterns suggère..."*.
- **Consistency Check**: The `Logic Auditor` (from the Swarm) must verify that the hypothesis doesn't contradict existing facts.

## 4. Implementation Details

### A. Forge Prompt (`prompts.yaml`)
- `forge_speculation`: Instructions for "Detective Reasoning." Forces the model to cite the specific graph patterns it used for its deduction.

### B. Neo4j Query Enhancement
- `The Forge` uses a new set of Cypher queries to find "Similar Entity Behaviors" (e.g., `"MATCH (s:Studio {name: 'X'})-[:PRODUCED_BY]-(m:Media) RETURN m.year, m.status"`).

## 5. Success Criteria
- The system can provide a reasoned estimation for unannounced release dates (e.g., "One Punch Man Season 3") based on production cycles.
- User satisfaction on "Impossible Questions" increases because they get an expert-level estimation instead of a dead end.
- Clear distinction between Factual Lore and Speculative Lore is maintained.
