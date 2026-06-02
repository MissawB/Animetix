# Design: Standardize Python Logging in Pipeline

## 1. Overview
The goal is to replace all `print()` statements in the pipeline scripts with a standardized logging system using the `animetix` logger. This ensures better traceability, control over log levels, and consistency across the project.

## 2. Architecture
Each script in the target directories will be updated to:
1.  Import the `logging` module.
2.  Initialize the logger: `logger = logging.getLogger('animetix')`.
3.  Replace `print(...)` calls with `logger.info(...)`, `logger.error(...)`, or `logger.warning(...)` based on the context.

## 3. Implementation Details

### 3.1 Logger Initialization
Place the following block after the imports:
```python
import logging
logger = logging.getLogger('animetix')
```

### 3.2 Log Level Mapping
- **INFO**: General status, progress, start/end messages, and emojis indicating success (✅), starting (🚀), or info (ℹ️, 📊).
- **WARNING**: Warning messages (⚠️).
- **ERROR**: Error messages (❌).
- **EXCEPTION**: Inside `except` blocks where we want to capture the stack trace.

### 3.3 Error Handling Improvements
- Replace `except: pass` with `logger.exception("An error occurred")` or `logger.warning(f"Caught error: {e}")`.
- Ensure all exceptions that were previously silently ignored or just printed are now properly logged.

## 4. Scope
Target directories:
- `backend/pipeline/anime/`
- `backend/pipeline/characters/`
- `backend/pipeline/movies/`

## 5. Verification
- Run a subset of scripts to ensure logging output is correct.
- Verify that no `print()` statements remain in the target files using `grep`.
