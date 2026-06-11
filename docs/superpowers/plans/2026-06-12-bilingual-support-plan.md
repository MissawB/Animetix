# Bilingual Support (English & French) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable bilingual capability (English + French) in the Animetix AI agent RAG pipeline and the SFT training dataset compiler.

**Architecture:** We will propagate the target language (defaulting to "Français") via `RAGContext` to the synthesis and fallback processors, dynamically formatting prompt templates in the target language. The SFT training dataset compiler will compile a balanced bilingual mix of training examples and save the language indicator to each record, allowing the trainer to apply language-specific system prompts.

**Tech Stack:** Django, Python, Pytest, Pydantic, Hugging Face Datasets.

---

### Task 1: Add language attribute to RAGContext

**Files:**
- Modify: `backend/core/domain/entities/ai_schemas.py`
- Test: `tests/backend/core/domain/services/rag/processors/test_processors_suite.py`

- [ ] **Step 1: Write the failing test**
  Write a test case `test_rag_context_language` in `tests/backend/core/domain/services/rag/processors/test_processors_suite.py` checking that `RAGContext` can accept a `language` property which defaults to `"Français"`.
  
  ```python
  def test_rag_context_language():
      from core.domain.entities.ai_schemas import RAGContext
      ctx = RAGContext(query="test", media_type="Anime")
      assert ctx.language == "Français"
      
      ctx_en = RAGContext(query="test", media_type="Anime", language="English")
      assert ctx_en.language == "English"
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_rag_context_language`
  Expected: FAIL (ValidationError or attribute error)

- [ ] **Step 3: Write minimal implementation**
  Add the `language: str = "Français"` field to `RAGContext` in `backend/core/domain/entities/ai_schemas.py`:
  
  ```python
  class RAGContext(BaseModel):
      # ... existing fields ...
      language: str = "Français"
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_rag_context_language`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/core/domain/entities/ai_schemas.py tests/backend/core/domain/services/rag/processors/test_processors_suite.py
  git commit -m "feat: add language field to RAGContext"
  ```

---

### Task 2: Propagate language parameter in AgenticRAGService & API View

**Files:**
- Modify: `backend/core/domain/services/agentic_rag_service.py`
- Modify: `backend/api/animetix/api/streams.py`
- Test: `tests/backend/core/domain/services/rag/processors/test_processors_suite.py`

- [ ] **Step 1: Write the failing test**
  Add a test to verify `AgenticRAGService.plan_and_solve_stream` accepts a language parameter and sets it in the generated context.
  
  ```python
  def test_agentic_rag_service_propagates_language(monkeypatch):
      from core.domain.services.agentic_rag_service import AgenticRAGService
      from unittest.mock import MagicMock
      
      # Mock dependencies
      mock_engine = MagicMock()
      mock_rag = MagicMock()
      mock_search = MagicMock()
      mock_prompt = MagicMock()
      mock_llm = MagicMock()
      mock_orch = MagicMock()
      
      service = AgenticRAGService(
          inference_engine=mock_engine,
          rag_service=mock_rag,
          web_search=mock_search,
          prompt_manager=mock_prompt,
          llm_service=mock_llm,
          workflow_orchestrator=mock_orch
      )
      
      # Mock semantic router to trigger standard flow
      service.semantic_router.classify = MagicMock(return_value="COMPLEX")
      service._assess_complexity = MagicMock(return_value=(1000, 2))
      service._check_cache = MagicMock(return_value=None)
      service._get_memories = MagicMock(return_value="")
      
      # Intercept run_workflow to verify context language
      def mock_run_workflow(ctx, xai_collector=None):
          assert ctx.language == "English"
          yield from []
      mock_orch.run_workflow.side_effect = mock_run_workflow
      
      # Run stream
      list(service.plan_and_solve_stream("Who is Naruto?", "Anime", language="English"))
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_agentic_rag_service_propagates_language`
  Expected: FAIL (TypeError or assertion failure because language is not accepted or passed down)

- [ ] **Step 3: Write minimal implementation**
  - Update `AgenticRAGService.plan_and_solve` and `plan_and_solve_stream` in `backend/core/domain/services/agentic_rag_service.py` to accept `language: str = "Français"`:
    ```python
    def plan_and_solve(self, query: str, media_type: str, user_id: Optional[str] = None, language: str = "Français") -> str:
        last_answer = ""
        for event in self.plan_and_solve_stream(query, media_type, user_id, language):
            if event['type'] == 'token':
                last_answer += event['content']
            elif event['type'] == 'thought' and "[Synthesizer]" in event['content']:
                last_answer = ""
        return last_answer

    def plan_and_solve_stream(self, query: str, media_type: str, user_id: Optional[str] = None, language: str = "Français") -> Generator[Dict, None, None]:
        # ... and instantiate RAGContext with language ...
        ctx = RAGContext(
            query=query,
            media_type=media_type,
            user_id=user_id,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            memories=self._get_memories(user_id, query),
            current_state=RAGState.PLAN,
            graph_expert=self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert if self.orchestrator and RAGState.GRAPH_EXPLORE in self.orchestrator.processors else None,
            truth_path=user_context,
            language=language
        )
    ```
  - Update `AgenticRAGStreamView` in `backend/api/animetix/api/streams.py` to read the `lang` parameter and session language:
    ```python
        def get(self, request):
            session = get_session_service(request)
            query = request.GET.get('q', '')
            media_type = request.GET.get('media_type') or session.get_current_mode()
            
            lang_param = request.GET.get('lang')
            if lang_param:
                if 'en' in lang_param.lower() or 'eng' in lang_param.lower():
                    language = 'English'
                else:
                    language = 'Français'
            else:
                language = session.get('language', 'Français')
            
            if not query: 
                return JsonResponse({'error': 'No query provided'}, status=400)
                
            def event_stream():
                agent = get_container().agentic.agentic_rag()
                user_id = str(request.user.id) if request.user.is_authenticated else None
                try:
                    for event in agent.plan_and_solve_stream(query, media_type, user_id=user_id, language=language):
                        yield f"data: {json.dumps(event)}\n\n"
            # ...
    ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_agentic_rag_service_propagates_language`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/core/domain/services/agentic_rag_service.py backend/api/animetix/api/streams.py tests/backend/core/domain/services/rag/processors/test_processors_suite.py
  git commit -m "feat: propagate language parameter in AgenticRAGService and AgenticRAGStreamView"
  ```

---

### Task 3: Update Prompts and ResponseSynthesizer

**Files:**
- Modify: `backend/core/domain/services/prompts/prompts.yaml`
- Modify: `backend/core/domain/services/rag/agents/synthesizer.py`
- Modify: `backend/core/domain/services/rag/processors/synthesize_processor.py`
- Test: `tests/backend/core/domain/services/rag/processors/test_processors_suite.py`

- [ ] **Step 1: Write the failing test**
  Add a test to verify `ResponseSynthesizer` generates a prompt using the target language.
  
  ```python
  def test_response_synthesizer_respects_language():
      from core.domain.services.rag.agents import ResponseSynthesizer
      from unittest.mock import MagicMock
      
      mock_engine = MagicMock()
      mock_prompt_mgr = MagicMock()
      mock_prompt_mgr.get_prompt.return_value = ("formatted_prompt", "system_prompt")
      
      synthesizer = ResponseSynthesizer(mock_engine, mock_prompt_mgr)
      list(synthesizer.synthesize_stream("query", "context", language="English"))
      
      mock_prompt_mgr.get_prompt.assert_called_with(
          "synthesizer_final", query="query", context="context", feedback=None, language="English"
      )
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_response_synthesizer_respects_language`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
  - In `backend/core/domain/services/prompts/prompts.yaml`, update `synthesizer_final` and `synthesizer_correction` templates/system prompts to use `{language}`:
    ```yaml
    synthesizer_final:
      template: "RÔLE : Synthétiseur Expert (Synthesizer).\nREQUÊTE : '{query}'\nCONTEXTE VALIDÉ :\n{context}\n\nMISSION : Rédige une réponse précise basées UNIQUEMENT sur le contexte fourni, rédigée en {language}.\nInclus impérativement les noms propres, dates et faits clés trouvés dans le contexte.\n\nSi `thinking_mode` est activé, tu DOIS commencer ta réponse par une balise `<thought>` contenant ton raisonnement détaillé, tes doutes et tes vérifications logiques avant de fournir le JSON final.\n\nRÉPONDS UNIQUEMENT EN JSON :\n{{\n  \"answer\": \"Ta réponse textuelle ici\",\n  \"sources\": [\"source 1\", \"source 2\"],\n  \"confidence\": 0.95\n}}\n"
      system_prompt: Tu es le Synthesizer Animetix. Ta priorité est la précision factuelle. Tu dois répondre en {language}.
    
    synthesizer_correction:
      template: "RÔLE : Synthétiseur Expert (Correction).\nREQUÊTE : '{query}'\nCONTEXTE VALIDÉ :\n{context}\n\nRETOUR DU JUGE (FEEDBACK) :\n{feedback}\n\nMISSION : Rédige une NOUVELLE réponse corrigée, en tenant compte du feedback. Sois extrêmement prudent sur la fidélité au contexte. Rédige ta réponse en {language}.\n\nSi `thinking_mode` est activé, tu DOIS commencer ta réponse par une balise `<thought>` contenant ton raisonnement détaillé, tes doutes et tes vérifications logiques avant de fournir le JSON final.\n\nGénère un dictionnaire JSON :\n{{\n  \"answer\": \"...\",\n  \"sources\": [\"source 1\", \"source 2\"],\n  \"confidence\": 0.98\n}}\n"
      system_prompt: Tu es le Synthesizer Animetix (Mode Auto-Correction). Ta priorité absolue est la fidélité au contexte. Tu dois répondre en {language}.
    ```
  - In `backend/core/domain/services/rag/agents/synthesizer.py`, update `synthesize_stream` to accept and pass `language`:
    ```python
        def synthesize_stream(self, query: str, context: str, thinking_budget: int = 0, thinking_mode: bool = False, correction_feedback: Optional[str] = None, language: str = "Français") -> Generator[str, None, None]:
            prompt_key = "synthesizer_correction" if correction_feedback else "synthesizer_final"
            syn_prompt, syn_sys = self.prompt_manager.get_prompt(prompt_key, query=query, context=context, feedback=correction_feedback, language=language)
            yield from self.inference_engine.stream_generate(
                syn_prompt, 
                syn_sys, 
                thinking_budget=thinking_budget,
                thinking_mode=thinking_mode
            )
    ```
  - In `backend/core/domain/services/rag/processors/synthesize_processor.py`, pass `ctx.language` to `synthesize_stream`:
    ```python
            for token in self.synthesizer.synthesize_stream(
                ctx.query, 
                ctx.truth_path, 
                thinking_budget=ctx.thinking_budget, 
                thinking_mode=ctx.thinking_mode,
                correction_feedback=ctx.correction_feedback,
                language=ctx.language
            ):
    ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_response_synthesizer_respects_language`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/core/domain/services/prompts/prompts.yaml backend/core/domain/services/rag/agents/synthesizer.py backend/core/domain/services/rag/processors/synthesize_processor.py tests/backend/core/domain/services/rag/processors/test_processors_suite.py
  git commit -m "feat: support dynamic language in ResponseSynthesizer and prompts"
  ```

---

### Task 4: Update FallbackRagProcessor

**Files:**
- Modify: `backend/core/domain/services/rag/processors/fallback_rag_processor.py`
- Test: `tests/backend/core/domain/services/rag/processors/test_processors_suite.py`

- [ ] **Step 1: Write the failing test**
  Write a test case `test_fallback_processor_english` verifying that when `ctx.language` is `"English"`, the prompt and system prompt used by `FallbackRagProcessor` are translated to English.
  
  ```python
  def test_fallback_processor_english():
      from core.domain.services.rag.processors.fallback_rag_processor import FallbackRagProcessor
      from core.domain.entities.ai_schemas import RAGContext, RAGState
      from unittest.mock import MagicMock
      
      mock_rag = MagicMock()
      mock_rag.hybrid_search.return_value = [{"title": "Title", "description": "Desc"}]
      mock_engine = MagicMock()
      mock_engine.stream_generate.return_value = ["Answer"]
      
      processor = FallbackRagProcessor(mock_rag, mock_engine, [])
      ctx = RAGContext(query="What is Naruto?", media_type="Anime", language="English")
      
      states = list(processor.process(ctx))
      
      mock_engine.stream_generate.assert_called_once()
      args = mock_engine.stream_generate.call_args[0]
      assert "Answer the following question" in args[0]
      assert "You are an expert assistant" in args[1]
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_fallback_processor_english`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
  In `backend/core/domain/services/rag/processors/fallback_rag_processor.py`, check `ctx.language` and set english instructions:
  
  ```python
      def process(self, ctx: RAGContext) -> Generator[StreamStep, None, RAGState]:
          yield StreamStep(type="thought", content="[Fallback] Exécution d'une recherche hybride standard...").model_dump()
  
          expert_injections = self._get_expert_injections(ctx.query)
          results = self.rag_service.hybrid_search(ctx.query, ctx.media_type)
  
          local_ctx_list = [f"- {r.get('title')}: {r.get('description', '')[:2000]}" for r in results]
          if expert_injections:
              fallback_context = "\n".join([f"- Fait de Repli: {f}" for f in expert_injections] + local_ctx_list)
          else:
              fallback_context = "\n".join(local_ctx_list)
  
          yield StreamStep(type="thought", content="[Fallback] Synthèse de la réponse de secours...").model_dump()
  
          if ctx.language == "English":
              prompt = f"Answer the following question using ONLY the context provided.\nQUESTION: {ctx.query}\nCONTEXT:\n{fallback_context}"
              system = "You are an expert assistant. Be concise and factual. Reply in English."
          else:
              prompt = f"Réponds à la question suivante en utilisant UNIQUEMENT le contexte fourni.\nQUESTION: {ctx.query}\nCONTEXTE:\n{fallback_context}"
              system = "Tu es un assistant expert. Sois concis et factuel. Réponds en Français."
  
          ctx.full_answer = ""
          for token in self.inference_engine.stream_generate(prompt, system):
              ctx.full_answer += token
              yield StreamStep(type="token", content=token).model_dump()
  
          return RAGState.FINALIZE
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/core/domain/services/rag/processors/test_processors_suite.py -k test_fallback_processor_english`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/core/domain/services/rag/processors/fallback_rag_processor.py tests/backend/core/domain/services/rag/processors/test_processors_suite.py
  git commit -m "feat: support English language fallback in FallbackRagProcessor"
  ```

---

### Task 5: Update SFT Dataset Compiler for Bilingual Support

**Files:**
- Modify: `backend/pipeline/mlops/finetuning_dataset.py`
- Test: `tests/backend/pipeline/mlops/test_finetuning_dataset.py`

- [ ] **Step 1: Write the failing test**
  Write a test case in a new or existing test file `tests/backend/pipeline/mlops/test_finetuning_dataset.py` verifying that generated dataset records contain a `"language"` field that is either `"English"` or `"Français"`.
  
  ```python
  def test_bilingual_dataset_generation():
      from pipeline.mlops.finetuning_dataset import make_french_anime_profile, get_display_title
      # Verify that generators accept a language or language keys are written
      # We'll test a mock sample or output keys
      # Details TBD based on final function design
  ```
  Wait! Let's examine if there is an existing test file. Yes, there's `tests/backend/pipeline/mlops/test_finetuning_dataset.py` or similar. Let's look for test files.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/pipeline/mlops/`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
  Modify `backend/pipeline/mlops/finetuning_dataset.py`:
  - Add parallel English templates for anime, manga, and characters profiles.
  - Mix French and English generation 50/50 in the loops.
  - Load and merge English instructions from Alpaca (e.g. from `tatsu-lab/alpaca` or another fallback if offline/mocked).
  - Add `"language": "English"` or `"language": "Français"` to each compiled item.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/pipeline/mlops/`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/pipeline/mlops/finetuning_dataset.py
  git commit -m "feat: update SFT dataset compiler to generate bilingual examples"
  ```

---

### Task 6: Update Expert Model Trainer

**Files:**
- Modify: `backend/pipeline/mlops/train_expert_model.py`
- Test: `tests/backend/pipeline/mlops/test_expert_model.py`

- [ ] **Step 1: Write the failing test**
  Add a test in `tests/backend/pipeline/mlops/test_expert_model.py` checking that the trainer's `process_chatml` formats English examples with the correct English system prompt.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/pipeline/mlops/`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
  Modify `process_chatml` in `backend/pipeline/mlops/train_expert_model.py`:
  ```python
      def process_chatml(item):
          user_content = item["instruction"]
          lang = item.get("language", "Français")
          if lang == "English":
              sys_content = "You are Animetix, an absolute expert in otaku culture, manga, and Japanese anime. You respond in a very comprehensive and precise manner in English."
              if item["input"]:
                  user_content = f"{item['instruction']}\n\nContext: {item['input']}"
          else:
              sys_content = "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des animés japonais. Tu réponds de manière très complète et précise en français."
              if item["input"]:
                  user_content = f"{item['instruction']}\n\nContexte : {item['input']}"
              
          messages = [
              {"role": "system", "content": sys_content},
              {"role": "user", "content": user_content},
              {"role": "assistant", "content": item["output"]}
          ]
          formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
          return {"text": formatted}
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest tests/backend/pipeline/mlops/`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```powershell
  git add backend/pipeline/mlops/train_expert_model.py
  git commit -m "feat: support language-specific system prompt in training formatter"
  ```
