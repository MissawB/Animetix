# Design Spec: Gold Set Coverage Analysis & Automated Gap Filling

We will implement a hybrid coverage analysis pipeline and automated query generation to systematically identify and resolve semantic blind spots in our Gold Set.

---

## 1. Architecture & Audit Component

We will create a new administrative script at `backend/scripts/analyze_gold_coverage.py` that connects to:
1. **The Gold Set** (`data/mlops/gold_dataset.json`): Load existing queries, `expected_entities`, and metadata.
2. **Neo4j Database**: Query active entities (`Media`, `Studio`, `Person`) to identify nodes with high connectivity degree that are completely missing from the Gold Set's `expected_entities`.
3. **Chroma Vector Database**: Query the `VectorRecord` Django model to calculate document counts grouped by `genre` and `studio` metadata, and flag under-represented genres/studios (defined as having >10% database representation but <3% Gold Set representation).

---

## 2. Adaptive QA Generation

When the user runs `python backend/scripts/analyze_gold_coverage.py --generate-missing`:
1. **Graph Gaps (Graph Blind Spots)**:
   - For each missing entity, query Neo4j to extract a subgraph (1-hop or 2-hop paths).
   - Format paths as descriptive facts (e.g., *"Media X was produced by Studio Y and created by Person Z"*).
2. **Vector Gaps (Vectorial Blind Spots)**:
   - For each under-represented genre/studio, retrieve up to 3 random document chunks from `VectorRecord`.
3. **LLM QA Synthesis**:
   - Invoke the default dependency injection inference engine (`get_container().inference_engine()`).
   - Prompt the LLM using a structured request model to return one or more Gold Set entries conforming to our evolved schema:
     - `query` (user query)
     - `ground_truth` (detailed fact answer)
     - `expected_entities` (list of named entity strings)
     - `expected_contexts` (list of contexts)
     - `expected_chunks` (list of chunk IDs)
     - `query_type` (`"graph"`, `"thematic"`, etc.)
     - `difficulty` (`"easy"`, `"medium"`, `"hard"`)
     - `multi_turn_history` (`[]`)
4. **Append & Save**:
   - Merge the newly synthesized QA entries back into `data/mlops/gold_dataset.json`.
   - Validate each generated entry against the schema rules before exporting.

---

## 3. Verification & Testing

### Automated Unit Tests
- Create a unit test `tests/mlops/test_gold_coverage_analyzer.py` mocking Neo4j and Chroma connections.
- Verify that the coverage auditor accurately identifies missing entities and under-represented genres, and successfully calls the LLM generator to append formatted QA entries.

### Manual Verification
- Execute `python backend/scripts/analyze_gold_coverage.py --threshold 0.1` locally to print the current Gold Set coverage audit report to stdout.
