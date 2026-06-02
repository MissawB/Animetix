# Python Import Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update all Python imports in `backend/`, `tests/`, and `scripts/` to reflect the new project structure by replacing `src` with `backend` or `backend.api`.

**Architecture:** Use a robust Python script to perform atomic replacements across all `.py` files in the specified directories, ensuring `src.backend` is processed before `src` to avoid partial replacement bugs.

**Tech Stack:** Python (standard library for file operations and regex).

---

### Task 1: Research and Preparation

**Files:**
- Create: `scripts/verify_imports_refactor.py`

- [ ] **Step 1: Create a verification script**
Create a script that scans `backend/`, `tests/`, and `scripts/` for any remaining `src` imports to be used before and after the refactor.

```python
import os
import re

def check_for_src_imports(directories):
    pattern = re.compile(r'(from|import)\s+backend\.?')
    found = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if pattern.search(line):
                                found.append(f"{path}:{i} - {line.strip()}")
    return found

if __name__ == "__main__":
    dirs = ['backend', 'tests', 'scripts']
    matches = check_for_src_imports(dirs)
    if matches:
        print(f"Found {len(matches)} matches:")
        for m in matches:
            print(m)
    else:
        print("No src imports found.")
```

- [ ] **Step 2: Run the verification script**
Run: `python scripts/verify_imports_refactor.py`
Expected: List of current `src` imports.

### Task 2: Implementation of Refactoring Script

**Files:**
- Create: `scripts/perform_import_refactor.py`

- [ ] **Step 1: Write the refactoring script**
The script will perform the 4 requested transformations in the correct order.

```python
import os
import re

def refactor_imports(directories):
    # Transformation rules in order
    rules = [
        (r'from backend\.backend\.', 'from backend.api.'),
        (r'from backend\.', 'from backend.'),
        (r'import backend\.backend', 'import backend.api'),
        (r'import backend', 'import backend'),
    ]
    
    updated_files_count = 0
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    new_content = content
                    for old, new in rules:
                        new_content = re.sub(old, new, new_content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        updated_files_count += 1
                        print(f"Updated: {path}")
    
    return updated_files_count

if __name__ == "__main__":
    dirs = ['backend', 'tests', 'scripts']
    count = refactor_imports(dirs)
    print(f"Finished. Updated {count} files.")
```

- [ ] **Step 2: Execute the refactoring script**
Run: `python scripts/perform_import_refactor.py`
Expected: "Finished. Updated [N] files." and a list of updated files.

### Task 3: Final Verification

**Files:**
- Modify: `scripts/verify_imports_refactor.py`

- [ ] **Step 1: Run the verification script again**
Run: `python scripts/verify_imports_refactor.py`
Expected: "No src imports found." (except possibly in strings or comments that were correctly ignored or if some edge cases exist).

- [ ] **Step 2: Smoke test a key file**
Check a known file (e.g., `backend/pipeline/characters/combat_data.py`) to ensure replacements look correct.
Run: `grep "backend" backend/pipeline/characters/combat_data.py`
Expected: Imports should now point to `backend.api` or `backend`.

- [ ] **Step 3: Clean up refactor scripts**
Remove the temporary scripts created for the refactor.
Run: `rm scripts/verify_imports_refactor.py scripts/perform_import_refactor.py`
