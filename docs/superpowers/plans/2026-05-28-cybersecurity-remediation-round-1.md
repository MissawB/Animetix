# Cybersecurity Remediation Implementation Plan - Round 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate critical security vulnerabilities: RCE in `DynamicToolAgent` and Cypher injection in Neo4j queries.

**Architecture:** We are introducing a multi-layered defense strategy:
1.  **Validator Layer:** Strengthening AST-based validation for generated Python and Cypher code.
2.  **Sandbox Layer:** Hardening the `exec()` environment for dynamic tools.
3.  **Policy Layer:** Enforcing read-only constraints for AI-generated database queries.

**Tech Stack:** Python (AST module), Neo4j (Cypher).

---

### Task 1: Secure DynamicToolAgent (RCE Mitigation)

**Files:**
- Modify: `backend/core/domain/services/dynamic_tool_agent.py`

- [ ] **Step 1: Harden `CodeSafetyValidator`**
  Add more strict checks for `Attribute` access (to prevent `__subclasses__` etc.), `Name` lookups, and `Call` targets.

```python
    def visit_Attribute(self, node: ast.Attribute):
        # Interdire l'accès à TOUS les attributs commençant par _
        if node.attr.startswith("_"):
            self.errors.append(f"Accès à l'attribut privé/interne '{node.attr}' interdit.")
        self.generic_visit(node)
        
    def visit_Name(self, node: ast.Name):
        # Interdire l'accès aux dunders globaux si jamais chargés
        if node.id.startswith("__") and node.id != "__name__":
             self.errors.append(f"Accès à l'identifiant interne '{node.id}' interdit.")
        self.generic_visit(node)
```

- [ ] **Step 2: Restrict `exec()` scope even further**
  Ensure `__builtins__` is a very minimal dict, and NO `globals()` are leaked.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/dynamic_tool_agent.py
git commit -m "security: harden DynamicToolAgent against RCE by restricting AST and exec scope"
```

### Task 2: Secure Neo4j Queries (Injection Mitigation)

**Files:**
- Modify: `backend/pipeline/neo4j_client.py`
- Modify: `backend/adapters/persistence/neo4j_graph_adapter.py`
- Modify: `backend/core/domain/services/rag_workflow_manager.py`

- [ ] **Step 1: Implement `CypherSanitizer` in `Neo4jManager`**
  Add a method to check if a query contains write/drop keywords.

```python
    @staticmethod
    def is_safe_read_query(query: str) -> bool:
        dangerous_keywords = {"DELETE", "DETACH", "DROP", "CREATE", "MERGE", "SET", "REMOVE", "CALL", "LOAD", "CSV", "PERIODIC", "COMMIT"}
        # Check for keywords as whole words, case-insensitive
        import re
        query_upper = query.upper()
        for kw in dangerous_keywords:
            if re.search(rf"\b{kw}\b", query_upper):
                return False
        return True
```

- [ ] **Step 2: Enforce read-only check in `execute_read`**
  Ensure `execute_read` (and `execute_query` when used for read) validates safety.

- [ ] **Step 3: Update `rag_workflow_manager.py` to use `execute_read` for AI queries**
  Change the call from `execute_query` to `execute_read` for LLM-generated Cypher.

- [ ] **Step 4: Commit**

```bash
git add backend/pipeline/neo4j_client.py backend/adapters/persistence/neo4j_graph_adapter.py backend/core/domain/services/rag_workflow_manager.py
git commit -m "security: prevent Cypher injection by enforcing read-only validation on AI-generated queries"
```

### Task 3: Remove Hardcoded Secrets

**Files:**
- Modify: `backend/pipeline/neo4j_client.py`

- [ ] **Step 1: Remove default values for sensitive env vars**
  Change `os.getenv("NEO4J_PASSWORD", "secretpassword")` to `os.getenv("NEO4J_PASSWORD")`.

- [ ] **Step 2: Commit**

```bash
git add backend/pipeline/neo4j_client.py
git commit -m "security: remove hardcoded default credentials for Neo4j"
```
