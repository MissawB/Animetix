# Logging Standardization Design

**Goal:** Standardize Python logging in `backend/pipeline/anime/` by replacing `print()` calls with a structured logger.

## Architecture
Each module will have its own logger instance named `animetix.<module_name>`. This allows for granular control over log levels per module while keeping them under the `animetix` parent logger.

## Changes

### 1. Logger Instantiation
All target files will ensure they have:
```python
import logging
logger = logging.getLogger("animetix." + __name__)
```
If `import logging` exists but the logger name is different (e.g., `animetix`), it will be updated.

### 2. Print Replacements
| Pattern | Replacement |
| :--- | :--- |
| `print(f"❌ ...")` | `logger.error(f"❌ ...")` |
| `print("❌ ...")` | `logger.error("❌ ...")` |
| `print(f"🚀 ...")` | `logger.info(f"🚀 ...")` |
| `print(f"✅ ...")` | `logger.info(f"✅ ...")` |
| `print("...")` | `logger.info("...")` |
| `print(f"⚠️ ...")` | `logger.warning(f"⚠️ ...")` |
| `print("⚠️ ...")` | `logger.warning("⚠️ ...")` |
| `print(f"ℹ️ ...")` | `logger.info(f"ℹ️ ...")` |

### 3. File-specific notes
- `filter_anime.py`, `fetch_themes.py`, `6_generate_sagas.py`: Update logger name only.
- `ingest_anime.py`, `reconcile_drift.py`, `train_vibe_anime.py`, `vectorize_anime.py`: Add `import logging`, setup logger, and replace all `print()`.

## Verification
- `python -m py_compile <file>` to check syntax.
- Test script `tests/scripts/test_logging_setup.py` to verify logger instantiation and hierarchy.
