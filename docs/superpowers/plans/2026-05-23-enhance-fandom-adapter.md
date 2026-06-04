# Enhance FandomAdapter with Image Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch `FandomAdapter` to use `action=query` for better efficiency and to extract character image URLs alongside wikitext.

**Architecture:** Update `FandomAdapter` implementation to use the `query` action of MediaWiki API with `pageimages` property. Maintain compatibility with the existing `FandomPort` while adding `image_url` to the return dictionary.

**Tech Stack:** Python, requests, pytest

---

### Task 1: Update FandomAdapter Implementation

**Files:**
- Modify: `backend/adapters/persistence/fandom_adapter.py`

- [ ] **Step 1: Replace `fetch_character_data` method**

Apply the provided implementation which uses `action=query` and `prop=pageimages|revisions`.

- [ ] **Step 2: Verify imports**

Ensure `typing.Dict`, `typing.Any`, `requests`, and `logging` are correctly imported (already present).

### Task 2: Update Tests for FandomAdapter

**Files:**
- Modify: `tests/adapters/test_fandom_adapter.py`

- [ ] **Step 1: Update `test_fetch_character_data_success`**

Update the mock response to match the new `action=query` format and assert `image_url`.

```python
@patch('requests.get')
def test_fetch_character_data_success(mock_get):
    # Mock response from MediaWiki API (action=query format)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": {
            "pages": [
                {
                    "pageid": 123,
                    "title": "Goku",
                    "original": {"source": "https://example.com/goku.jpg"},
                    "revisions": [{"content": "Character info here"}]
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Goku")

    assert data["name"] == "Goku"
    assert data["wikitext"] == "Character info here"
    assert data["image_url"] == "https://example.com/goku.jpg"
```

- [ ] **Step 2: Add test for missing character**

```python
@patch('requests.get')
def test_fetch_character_data_missing(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": {
            "pages": [{"title": "Unknown", "missing": True}]
        }
    }
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Unknown")

    assert data["name"] == "Unknown"
    assert data["wikitext"] == ""
    assert data["image_url"] is None
```

### Task 3: Verification and Commitment

- [ ] **Step 1: Run tests**

Run: `pytest tests/adapters/test_fandom_adapter.py`
Expected: PASS

- [ ] **Step 2: Commit changes**

```bash
git add backend/adapters/persistence/fandom_adapter.py tests/adapters/test_fandom_adapter.py
git commit -m "feat(adapters): enhance FandomAdapter with image extraction"
```
