# Fandom Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a port and adapter to fetch character data from VS Battles Wiki (Fandom).

**Architecture:** Hexagonal Architecture (Ports and Adapters). The port defines the interface in the core layer, and the adapter implements it using the MediaWiki API in the infrastructure layer.

**Tech Stack:** Python, requests (for API calls).

---

### Task 1: Define FandomPort

**Files:**
- Create: `backend/core/ports/fandom_port.py`

- [ ] **Step 1: Write the Port interface**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class FandomPort(ABC):
    @abstractmethod
    def fetch_character_data(self, character_name: str) -> Dict[str, Any]:
        """Fetches character data from VS Battles Wiki."""
        pass
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/ports/fandom_port.py
git commit -m "feat(core): add FandomPort interface"
```

### Task 2: Implement FandomAdapter

**Files:**
- Create: `backend/adapters/persistence/fandom_adapter.py`
- Test: `tests/adapters/test_fandom_adapter.py`

- [ ] **Step 1: Write a failing test for FandomAdapter**

```python
import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.fandom_adapter import FandomAdapter

@patch('requests.get')
def test_fetch_character_data_success(mock_get):
    # Mock response from MediaWiki API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "parse": {
            "wikitext": {
                "*": "Character info here"
            }
        }
    }
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Goku")

    assert data["name"] == "Goku"
    assert "wikitext" in data
    assert data["wikitext"] == "Character info here"
    mock_get.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/adapters/test_fandom_adapter.py`
Expected: FAIL (ModuleNotFoundError: No module named 'adapters.persistence.fandom_adapter')

- [ ] **Step 3: Implement FandomAdapter**

```python
import requests
from typing import Dict, Any
from core.ports.fandom_port import FandomPort

class FandomAdapter(FandomPort):
    def __init__(self):
        self.api_url = "https://vsbattles.fandom.com/api.php"

    def fetch_character_data(self, character_name: str) -> Dict[str, Any]:
        params = {
            "action": "parse",
            "page": character_name,
            "format": "json",
            "prop": "wikitext"
        }
        response = requests.get(self.api_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if "error" in data:
            raise Exception(f"Fandom API Error: {data['error']['info']}")
            
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        
        return {
            "name": character_name,
            "wikitext": wikitext
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/adapters/test_fandom_adapter.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/persistence/fandom_adapter.py tests/adapters/test_fandom_adapter.py
git commit -m "feat(adapters): implement FandomAdapter using MediaWiki API"
```

### Task 3: Register FandomAdapter in Container

**Files:**
- Modify: `backend/api/animetix/containers.py`

- [ ] **Step 1: Import FandomAdapter**

```python
from adapters.persistence.fandom_adapter import FandomAdapter
```

- [ ] **Step 2: Add fandom_adapter property to Container class**

```python
    @property
    def fandom_adapter(self):
        return self._get('fandom_adapter', lambda: FandomAdapter())
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/containers.py
git commit -m "feat(backend): register FandomAdapter in DI container"
```

### Task 4: Final Verification

- [ ] **Step 1: Run all adapter tests**

Run: `pytest tests/adapters/`
Expected: All PASS
