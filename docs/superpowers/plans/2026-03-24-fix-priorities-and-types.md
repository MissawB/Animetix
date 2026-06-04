# Fix Adapter Priorities and Harden Frontend Typing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorder backend inference adapters and replace `any` types in frontend game pages with strict interfaces.

**Architecture:** Backend uses `dependency-injector` for adapter management. Frontend uses React with TypeScript and XState/React Query for game state management.

**Tech Stack:** Python, dependency-injector, TypeScript, React, XState, React Query.

---

### Task 1: Fix Adapter Priorities (Backend)

**Files:**
- Modify: `backend/api/animetix/containers.py`

- [ ] **Step 1: Reorder adapters in inference_engine**

```python
<<<<
    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            unified_inference_adapter,
            transformers_adapter,
            gguf_adapter,
            moondream_adapter,
            manga_ocr_adapter,
            diffusers_adapter,
            xtts_adapter,
            providers.Factory(
====
    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            unified_inference_adapter,
            transformers_adapter,
            gguf_adapter,
            diffusers_adapter,
            xtts_adapter,
            moondream_adapter,
            manga_ocr_adapter,
            providers.Factory(
>>>>
```

- [ ] **Step 2: Verify syntax**
Run `python -m py_compile backend/api/animetix/containers.py`

- [ ] **Step 3: Commit**
`git add backend/api/animetix/containers.py && git commit -m "refactor: fix inference adapter priorities"`

### Task 2: Harden Frontend Typing - AkinetixPage.tsx

**Files:**
- Modify: `frontend/backend/features/games/AkinetixPage.tsx`

- [ ] **Step 1: Replace any in history.map**

```typescript
<<<<
              {gameState.history.map((item: any, i: number) => (
                <div key={i} className="text-sm opacity-70 mb-2 border-l-2 border-yellow-400 pl-3">
                  <span className="font-bold text-yellow-500">IA :</span> {item.q} <span className="font-black italic ml-2">{item.a}</span>
                </div>
              ))}
====
              {gameState.history.map((item: { q: string; a: string }, i: number) => (
                <div key={i} className="text-sm opacity-70 mb-2 border-l-2 border-yellow-400 pl-3">
                  <span className="font-bold text-yellow-500">IA :</span> {item.q} <span className="font-black italic ml-2">{item.a}</span>
                </div>
              ))}
>>>>
```

- [ ] **Step 2: Commit**
`git add frontend/backend/features/games/AkinetixPage.tsx && git commit -m "feat(frontend): harden typing in AkinetixPage"`

### Task 3: Harden Frontend Typing - BlindtestPage.tsx

**Files:**
- Modify: `frontend/backend/features/games/BlindtestPage.tsx`

- [ ] **Step 1: Replace any in guesses.map**

```typescript
<<<<
            {gameState.guesses.map((g: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-gray-100 dark:border-white/5">
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? <Check className="text-green-500 w-5 h-5" /> : <X className="text-red-500 w-5 h-5" />}
              </div>
            ))}
====
            {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-gray-100 dark:border-white/5">
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? <Check className="text-green-500 w-5 h-5" /> : <X className="text-red-500 w-5 h-5" />}
              </div>
            ))}
>>>>
```

- [ ] **Step 2: Commit**
`git add frontend/backend/features/games/BlindtestPage.tsx && git commit -m "feat(frontend): harden typing in BlindtestPage"`

### Task 4: Harden Frontend Typing - ClassicGamePage.tsx

**Files:**
- Modify: `frontend/backend/features/games/ClassicGamePage.tsx`

- [ ] **Step 1: Replace any in guesses.map**

```typescript
<<<<
                  <div className="space-y-4">
                      {gameState.guesses.map((g: any, i: number) => (
                          <div key={i} className={`p-4 rounded-2xl flex items-center justify-between transition-all ${g.is_correct ? 'bg-green-500 text-white shadow-green-500/20' : 'bg-gray-50 dark:bg-navy-900 border border-gray-100 dark:border-white/5'}`}>
====
                  <div className="space-y-4">
                      {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
                          <div key={i} className={`p-4 rounded-2xl flex items-center justify-between transition-all ${g.is_correct ? 'bg-green-500 text-white shadow-green-500/20' : 'bg-gray-50 dark:bg-navy-900 border border-gray-100 dark:border-white/5'}`}>
>>>>
```

- [ ] **Step 2: Commit**
`git add frontend/backend/features/games/ClassicGamePage.tsx && git commit -m "feat(frontend): harden typing in ClassicGamePage"`

### Task 5: Harden Frontend Typing - CovertestPage.tsx

**Files:**
- Modify: `frontend/backend/features/games/CovertestPage.tsx`

- [ ] **Step 1: Replace any in guesses.map**

```typescript
<<<<
            <div className="mt-12 space-y-3">
              <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-4">Journal des tentatives</h4>
              {gameState.guesses.map((g: any, i: number) => (
                <div key={i} className={`flex items-center justify-between p-4 rounded-2xl border-l-4 transition-all ${g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
====
            <div className="mt-12 space-y-3">
              <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-4">Journal des tentatives</h4>
              {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
                <div key={i} className={`flex items-center justify-between p-4 rounded-2xl border-l-4 transition-all ${g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
>>>>
```

- [ ] **Step 2: Commit**
`git add frontend/backend/features/games/CovertestPage.tsx && git commit -m "feat(frontend): harden typing in CovertestPage"`

### Task 6: Harden Frontend Typing - EmojiPage.tsx

**Files:**
- Modify: `frontend/backend/features/games/EmojiPage.tsx`

- [ ] **Step 1: Replace any in guesses.map**

```typescript
<<<<
        <div className="max-w-2xl mx-auto space-y-4 mt-12">
          <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em] mb-6">Tes tentatives</h4>
          {gameState.guesses.map((g: any, i: number) => (
            <Card key={i} padding="sm" className="flex items-center transition-all hover:scale-[1.02]">
====
        <div className="max-w-2xl mx-auto space-y-4 mt-12">
          <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em] mb-6">Tes tentatives</h4>
          {gameState.guesses.map((g: { title: string; title_en?: string; image: string; is_correct: boolean }, i: number) => (
            <Card key={i} padding="sm" className="flex items-center transition-all hover:scale-[1.02]">
>>>>
```

- [ ] **Step 2: Commit**
`git add frontend/backend/features/games/EmojiPage.tsx && git commit -m "feat(frontend): harden typing in EmojiPage"`

### Task 7: Final Verification

- [ ] **Step 1: Run type checking for frontend**
Run: `cd frontend && npm run type-check` (or `tsc --noEmit`)

- [ ] **Step 2: Run backend tests if available**
Run: `pytest tests/backend/animetix/test_containers.py` (if exists)

---
Plan complete and saved to `docs/superpowers/plans/2025-03-24-fix-priorities-and-types.md`.
Approach: Inline Execution.
