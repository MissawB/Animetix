# Task 4: Implementing Rate Limiting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement rate limiting using `django-ratelimit` on AI-intensive endpoints to prevent DoS attacks and manage AI costs.

**Architecture:** Apply `@method_decorator(ratelimit(...))` to specific API view classes in `streams.py` and `akinetix.py`.

**Tech Stack:** Django, django-ratelimit

---

### Task 1: Add Rate Limiting to Stream Endpoints

**Files:**
- Modify: `backend/api/animetix/api/streams.py`

- [ ] **Step 1: Add imports and apply rate limiting to EmojiStreamView, ParadoxStreamView, AgenticRAGStreamView, and AniminatorStreamView**

```python
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# Apply to EmojiStreamView
@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class EmojiStreamView(APIView):
    ...

# Apply to ParadoxStreamView
@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class ParadoxStreamView(APIView):
    ...

# Apply to AgenticRAGStreamView
@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class AgenticRAGStreamView(APIView):
    ...

# Apply to AniminatorStreamView
@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class AniminatorStreamView(APIView):
    ...
```

- [ ] **Step 2: Verify syntax**

Run: `python -m py_compile backend/api/animetix/api/streams.py`
Expected: Success

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/streams.py
git commit -m "security: add rate limiting to AI stream endpoints"
```

### Task 2: Add Rate Limiting to Akinetix Game Endpoints

**Files:**
- Modify: `backend/api/animetix/api/games/akinetix.py`

- [ ] **Step 1: Add imports and apply rate limiting to AkinetixGameStartView and AkinetixGameAnswerView**

```python
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# Apply to AkinetixGameStartView
@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='post')
class AkinetixGameStartView(APIView):
    ...

# Apply to AkinetixGameAnswerView
@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='post')
class AkinetixGameAnswerView(APIView):
    ...
```

- [ ] **Step 2: Verify syntax**

Run: `python -m py_compile backend/api/animetix/api/games/akinetix.py`
Expected: Success

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/games/akinetix.py
git commit -m "security: add rate limiting to Akinetix game endpoints"
```
