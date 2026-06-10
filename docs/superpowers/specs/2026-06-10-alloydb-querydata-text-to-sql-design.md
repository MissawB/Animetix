# AlloyDB AI QueryData (Text-to-SQL) Design Spec

This design document outlines the integration of AlloyDB AI natural language query capabilities (`alloydb_ai_nl.get_sql`) into the Animetix persistence layer to simplify and secure catalog access for AI agents. It maintains full fallback emulation using local LLM translation in non-AlloyDB environments (SQLite / standard Postgres).

## User Review Required

> [!IMPORTANT]
> The SQL queries generated (whether via AlloyDB's native Text-to-SQL or via local LLM fallback) will be executed as raw SQL against the database. To guarantee security and prevent unauthorized data access or mutation, a strict double-layer SQL guardrail is proposed to validate the generated queries before they are sent to the cursor.

## Open Questions

No outstanding open questions. We will use the standard LLM engine fallback to translate queries when `ALLOYDB_NL_QUERY_ACTIVE` is `False`.

## Proposed Changes

---

### Configuration & Settings

#### [MODIFY] [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix_project/settings.py)
Add the following settings to control the AlloyDB QueryData feature flags:
```python
ALLOYDB_NL_QUERY_ACTIVE = env.bool('ALLOYDB_NL_QUERY_ACTIVE', default=False)
ALLOYDB_NL_CONFIG_NAME = env('ALLOYDB_NL_CONFIG_NAME', default='animetix_catalog')
```

---

### Core Ports & Adapters

#### [MODIFY] [repository_port.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/repository_port.py)
Declare the new abstract method:
```python
    @abstractmethod
    def query_data_natural_language(self, query: str, llm_service: Optional[Any] = None) -> List[Dict]:
        """Interroge le catalogue en langage naturel (Text-to-SQL) et renvoie les résultats."""
        pass
```

#### [MODIFY] [django_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/django_repository_adapter.py)
Implement `query_data_natural_language` using:
1. Dynamic detection of the `alloydb_ai_nl.get_sql` function.
2. Fallback to `llm_service` if not supported or inactive.
3. Strict execution of the SQL validation utility.
4. Parsing cursor output back into lists of standard dictionaries.

#### [MODIFY] [pgvector_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/pgvector_repository_adapter.py)
Add the stub implementation for `query_data_natural_language` (returns an empty list).

#### [MODIFY] [unified_repository_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/unified_repository_adapter.py)
Delegate `query_data_natural_language` calls directly to `self.django`.

---

### Security Guardrails

#### [NEW] [sql_guard.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/utils/sql_guard.py)
A security utility module that parses the raw generated SQL before running it:
- Checks if the normalized string starts with `SELECT`.
- Checks for mutating keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, etc.).
- Rejects SQL containing comments (`--`, `/*`) or multi-statement delimiters (`;`).
- Disallows all table names other than `animetix_mediaitem` using a dynamic check of all registered Django DB tables.

---

### Verification Plan

### Automated Tests
- Run the new test suite validating native execution, fallback generation, and security blocking:
  `pytest tests/core/test_alloydb_querydata_nl.py -v`

### Manual Verification
- Verify the probe capability against a mock cursor mimicking `alloydb_ai_nl.get_sql`.
