# GEMINI - Animetix Project Mandates

This file defines the absolute rules and technical constraints of the workspace.

> [!IMPORTANT]
> Specific instructions are available for sub-domains:
> - [Backend Mandates](../backend/GEMINI.md)
> - [Frontend Mandates](../frontend/GEMINI.md)

## 🏗️ Hexagonal Architecture (Ports & Adapters)
All modifications must strictly respect the separation of layers:

- **Domain (Core):** `backend/core/domain/`. Pure business logic, without external dependencies.
    - *Entities:* Use `Pydantic` for structure validation (`ai_schemas.py`).
    - *Services:* High-level logic. Do not use `print()`, use the standard `logging` module.
- **Ports (Interfaces):** `backend/core/ports/`. Abstract boundary definitions for external capabilities.
- **Adapters (Infrastructure):` `backend/adapters/`. Concrete infrastructure implementations.
    - *Persistence:* `UnifiedRepositoryAdapter` (Vertex AI Vector Search / pgvector).
    - *Inference:* `FallbackInferenceAdapter` (LLM Resilience + Streaming).
- **Presentation (Driving):** `backend/api/`. Headless Django API. Input validation via `Django Forms` is mandatory for user inputs.

## 📝 Code & AI Standards
- **Typing:** Python 3.10+. Strict type annotations are mandatory on all functions.
- **Logging:** Named loggers (`animetix.rag`). Levels: `info`, `warning`, `error`.
- **Prompts:** ZERO hardcoded prompts. Exclusively use `PromptManager` (YAML files).
- **Security:** Systematically sanitize LLM outputs with the `sanitize_ai` filter.

### Code Quality & Style
- **Linters:**
    - **Python:** `ruff check . --fix` (for auto-formatting and linting)
    - **TypeScript/JavaScript:** `eslint --fix` (for linting)
- **Formatters:**
    - **Python:** `ruff format .` (for auto-formatting)
    - **TypeScript/JavaScript:** `prettier --write .` (for auto-formatting)



## 🚀 Workspace & MLOps Specifics
- **Pipeline:** Automated synchronization commands and scheduled tasks (Django management commands). Automated Neo4j synchronization.
- **Observability:** 
    - Systematic tracking of tokens/costs via `UsagePort`.
    - RAG evaluation via `Ragas` (Faithfulness, Relevance).
- **SOTA Search:** Before choosing or updating a model, use the `huggingface-best` skill to identify the current best candidate.
- **Performance:** DB-side pagination (`limit`/`offset`). HNSW index for vector representations.

### Dependency Management
- **Tooling:** Use `pip-compile` for Python dependency management.
- **Virtual Environments:** Always work within a virtual environment.
- **Update Process:**
    1. Activate your virtual environment.
    2. Modify `requirements.in` (add/remove/update packages).
    3. Run `pip-compile requirements.in` to generate `requirements.txt`.
    4. Install/update dependencies with `pip install -r requirements.txt`.

### Git Workflow & Version Control
- **Branching Strategy:**
    - Use `feature/` branches for new features (e.g., `feature/add-user-auth`).
    - Use `bugfix/` branches for bug fixes (e.g., `bugfix/fix-login-error`).
    - Use `hotfix/` branches for critical production issues.
    - Always branch off `main` and merge back into `main` via Pull Requests.
- **Commit Message Conventions:**
    - Follow Conventional Commits specification for clear and automated changelogs.
    - Format: `<type>(<scope>): <subject>`
    - Example: `feat(auth): add user registration endpoint`
    - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
    - Scope: Optional, specifies the part of the codebase affected.

## 🛠️ Intervention Workflow
When addressing tasks or issues, follow this structured workflow:

1.  **Research & Analysis:**
    *   **Objective:** Fully understand the problem, its scope, and potential impact.
    *   **Tools:** Use `grep_search` to locate relevant code, `read_file` for in-depth understanding, `git blame` for historical context, and `codebase_investigator` for architectural mapping on complex issues.
    *   **Output:** Clearly define the affected Domain, Port, and Adapter layers. Identify all dependencies.

2.  **Strategic Planning:**
    *   **Objective:** Develop a compliant and efficient solution plan.
    *   **Criteria:** Justify how the proposed changes maintain hexagonal architecture integrity, adhere to strict typing, and align with project standards. Consider idempotency, backward compatibility, and potential side effects.
    *   **Escalation:** If the problem is complex, impacts multiple core systems, or requires significant architectural changes, escalate by providing a detailed `brainstorming` or `writing-plans` skill output to the user for review before proceeding to execution.

3.  **Surgical Execution & Testing:**
    *   **Objective:** Implement the changes and ensure their correctness and robustness.
    *   **Approach:** Perform surgical modifications to minimize blast radius. Always follow `test-driven-development` principles where applicable.
    *   **Tools:** Use `write_file` and `replace` for code modifications.
    *   **Tests:** Add comprehensive unit, integration, and end-to-end tests in the `tests/` directory to cover new functionality and guard against regressions.

4.  **Validation & Verification:**
    *   **Objective:** Confirm the changes work as expected and do not introduce new issues.
    *   **Tools:**
        *   Run `pytest` with relevant flags:
            *   **Unit Tests:** `pytest tests/unit/`
            *   **Integration Tests:** `pytest tests/integration/` (or `pytest tests/integration --mark=slow` for marked tests)
            *   **End-to-End Tests:** `pytest tests/e2e/`
        *   Verify layer boundaries and architectural compliance by reviewing code changes and running relevant system checks.
        *   Utilize `verification-before-completion` skill to ensure all checks pass.
    *   **Criteria:** Ensure all tests pass, linting checks are clean, and the solution adheres to performance and security standards.

5.  **Finalization & Documentation:**
    *   **Objective:** Prepare the changes for review and deployment.
    *   **Steps:** Document any significant architectural decisions or changes in `docs/ARCHITECTURE.md` or relevant `GEMINI.md` files. Ensure all new configurations or dependencies are noted. Prepare for a code review using the `requesting-code-review` skill.
