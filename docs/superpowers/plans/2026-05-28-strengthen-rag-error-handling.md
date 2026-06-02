# Strengthen RAG Services Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace broad `except Exception as e` blocks in RAG services and agents with specific, typed domain exceptions (`InferenceError`, `InfrastructureError`, `ParsingError`) and use `exc_info=True` for fallback exceptions.

**Architecture:** We are adhering to Hexagonal Architecture constraints by properly bubbling up or handling domain-specific exceptions defined in `backend/core/domain/exceptions.py`. This ensures we don't accidentally silence critical infrastructure or logic errors during RAG execution.

**Tech Stack:** Python, standard `logging` module, Pydantic/Orjson for parsing.

---

### Task 1: Fix Error Handling in AgenticRAGService

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`

- [ ] **Step 1: Replace generic exceptions in `_assess_complexity`**
  Modify `_assess_complexity` to catch specific exceptions first.

```python
    def _assess_complexity(self, query: str) -> tuple[int, int]:
        try:
            from .complexity_analyser import ComplexityAnalyser
            analyser = ComplexityAnalyser(self.prompt_manager, self.llm_service)
            return analyser.assess_complexity(query)
        except ImportError as e:
            logger.error(f"ComplexityAnalyser not available: {e}")
            return 0, 0
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"AI/Infrastructure error in dynamic complexity analysis: {e}")
            return 0, 0
        except Exception as e:
            logger.error(f"Error in dynamic complexity analysis: {e}", exc_info=True)
            return 0, 0
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/domain/services/agentic_rag_service.py
git commit -m "refactor: improve error handling in agentic_rag_service"
```

### Task 2: Fix Error Handling in Critic and Judge Agents

**Files:**
- Modify: `backend/core/domain/services/rag/agents/critic.py`
- Modify: `backend/core/domain/services/rag/agents/judge.py`

- [ ] **Step 1: Implement explicit error handling in `critic.py`**
  Find the `except Exception as e:` block and replace it with:
```python
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"Critic generation failed due to AI/Infrastructure error: {e}")
            return {"feedback": "Une erreur de génération est survenue.", "passed": False}
        except Exception as e:
            logger.error(f"Unexpected error in ResponseCritic: {e}", exc_info=True)
            return {"feedback": f"Erreur interne critique: {str(e)}", "passed": False}
```

- [ ] **Step 2: Implement explicit error handling in `judge.py`**
  Find the `except Exception as e:` block and replace it with:
```python
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"Judge generation failed due to AI/Infrastructure error: {e}")
            return {"decision": "FAIL", "reason": "Erreur d'inférence lors de l'évaluation finale."}
        except Exception as e:
            logger.error(f"Unexpected error in ResponseJudge: {e}", exc_info=True)
            return {"decision": "FAIL", "reason": f"Erreur interne: {str(e)}"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/rag/agents/critic.py backend/core/domain/services/rag/agents/judge.py
git commit -m "refactor: strengthen error handling in critic and judge agents"
```

### Task 3: Fix Error Handling in Graph Expert and Debate Manager

**Files:**
- Modify: `backend/core/domain/services/rag/agents/graph_expert.py`
- Modify: `backend/core/domain/services/rag/agents/debate_manager.py`

- [ ] **Step 1: Implement explicit error handling in `graph_expert.py`**
  Replace `except Exception as e:` with:
```python
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"Graph Expert inference error: {e}")
            return {"extracted_entities": [], "relationships": []}
        except Exception as e:
            logger.error(f"Unexpected error in GraphExpert: {e}", exc_info=True)
            return {"extracted_entities": [], "relationships": []}
```

- [ ] **Step 2: Implement explicit error handling in `debate_manager.py`**
  Replace all 3 occurrences of `except Exception as e:` in `debate_manager.py` with:
```python
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"DebateManager inference/infrastructure error: {e}")
            # Renvoyer une réponse par défaut ou un dict vide selon le contexte de la fonction
        except Exception as e:
            logger.error(f"Unexpected error in DebateManager: {e}", exc_info=True)
            # Renvoyer une réponse par défaut ou un dict vide selon le contexte de la fonction
```
*(Note to implementer: adapt the `return` statement to match what was originally returned in the bare `except Exception as e` block of the respective functions).*

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/rag/agents/graph_expert.py backend/core/domain/services/rag/agents/debate_manager.py
git commit -m "refactor: strengthen error handling in graph_expert and debate_manager"
```
