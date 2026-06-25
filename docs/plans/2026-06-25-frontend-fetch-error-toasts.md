# Frontend Fetch Failure Toasts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface a user-visible failure toast on the offline chapter-download path and on both MangaVoicePage failure paths, mirroring the existing AudioLabPage pattern.

**Architecture:** Use the existing `useToastStore.getState().addToast(message, 'error')` pattern at the failure points: the `useChapterDownload` hook's `catch` (offline path) and MangaVoicePage's two handlers. The raw fetches and the pure `offlineLibrary` service are unchanged.

**Tech Stack:** React + TypeScript, Vitest + @testing-library/react, Zustand toast store.

**Spec:** [docs/specs/2026-06-25-frontend-fetch-error-toasts-design.md](../specs/2026-06-25-frontend-fetch-error-toasts-design.md)

## Global Constraints

- Toast API: `useToastStore.getState().addToast(message: string, type?: 'error' | 'info' | 'success')`. Always pass `'error'` for these failures.
- Keep every existing `console.error` line (developer diagnostics) alongside the new toast.
- Do NOT change `api.ts` / `downloadDataset` / `OpenDataPage` (already harmonized), the raw fetches, or the `offlineLibrary` service.
- Reuse AudioLabPage's exact French string for sample-load failure: `"Échec du chargement de l'échantillon vocal."`. Generation failure string: `"Échec de la génération de la voix."`. Offline failure: the caught error's `.message`, falling back to `"Échec du téléchargement."`.
- Toast-store import path from `frontend/src/features/manga-reader/offline/`: `../../../store/toastStore`. From `frontend/src/pages/labs/`: `../../store/toastStore`.
- Run all frontend commands from the `frontend/` directory.

---

### Task 1: Offline download failure toast (useChapterDownload hook)

**Files:**
- Modify: `frontend/src/features/manga-reader/offline/useChapterDownload.ts` (the `catch` in `download`, ~lines 50-54; plus an import)
- Test: `frontend/src/features/manga-reader/offline/useChapterDownload.test.ts` (add one test + an import)

**Interfaces:**
- Consumes: `useToastStore` from `frontend/src/store/toastStore.ts` (`getState().addToast(message, type)`); `lib.OfflineQuotaError` (message contains "stockage").
- Produces: no new exports; the hook now calls `addToast(msg, 'error')` on download failure.

- [ ] **Step 1: Write the failing test**

In `frontend/src/features/manga-reader/offline/useChapterDownload.test.ts`, add this import after the existing `import * as lib from './offlineLibrary';` (line 4):

```ts
import { useToastStore } from '../../../store/toastStore';
```

Then add this test inside the `describe('useChapterDownload', ...)` block, after the existing `'sets error status with message on failure'` test (after line 50):

```ts
  it('toasts an error on download failure', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(lib, 'downloadChapter').mockRejectedValue(new lib.OfflineQuotaError());
    const addToast = vi
      .spyOn(useToastStore.getState(), 'addToast')
      .mockImplementation(() => {});
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('idle'));
    await act(async () => {
      await result.current.download();
    });
    expect(addToast).toHaveBeenCalledWith(expect.stringContaining('stockage'), 'error');
  });
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `frontend/`): `npx vitest run src/features/manga-reader/offline/useChapterDownload.test.ts`
Expected: the new test FAILS — `addToast` was not called (the hook does not toast yet). The other 5 tests still pass.
(If vitest errors that a project must be selected, append `--project unit` to the command.)

- [ ] **Step 3: Implement the toast in the hook**

In `frontend/src/features/manga-reader/offline/useChapterDownload.ts`, add this import after the existing import block (after line 8, the `} from './offlineLibrary';` line):

```ts
import { useToastStore } from '../../../store/toastStore';
```

Then change the `catch` in `download` (currently):

```ts
    } catch (err) {
      if (!mounted.current) return;
      setError(err instanceof Error ? err.message : 'Échec du téléchargement.');
      setStatus('error');
    }
```

to:

```ts
    } catch (err) {
      if (!mounted.current) return;
      const msg = err instanceof Error ? err.message : 'Échec du téléchargement.';
      setError(msg);
      useToastStore.getState().addToast(msg, 'error');
      setStatus('error');
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run (from `frontend/`): `npx vitest run src/features/manga-reader/offline/useChapterDownload.test.ts`
Expected: all 6 tests PASS (the new toast test and the original 5).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/manga-reader/offline/useChapterDownload.ts frontend/src/features/manga-reader/offline/useChapterDownload.test.ts
git commit -m "feat(frontend): toast on offline chapter download failure"
```

---

### Task 2: MangaVoicePage failure toasts (both paths)

**Files:**
- Modify: `frontend/src/pages/labs/MangaVoicePage.tsx` (an import; `handleSelectProfile` ~lines 53-70; `handleGenerate` `catch` ~lines 88-92)

**Interfaces:**
- Consumes: `useToastStore` from `frontend/src/store/toastStore.ts`.
- Produces: no new exports; both handlers now toast on failure.

- [ ] **Step 1: Add the toast-store import**

In `frontend/src/pages/labs/MangaVoicePage.tsx`, add this import alongside the existing imports near the top of the file (place it after the other relative imports, e.g. just before the component definition):

```ts
import { useToastStore } from '../../store/toastStore';
```

- [ ] **Step 2: Toast on sample-load failure in `handleSelectProfile`**

Replace the existing `try { ... } catch { ... } finally { ... }` body of `handleSelectProfile` (currently):

```ts
    try {
      const resp = await fetch(profile.sample_url);
      if (resp.ok) {
        const blob = await resp.blob();
        const file = new File([blob], `${profile.name}_sample.wav`, { type: 'audio/wav' });
        setRefAudio(file);
      }
    } catch (err) {
      console.error("Failed to load reference audio from profile:", err);
    } finally {
      setLoadingAudio(false);
    }
```

with:

```ts
    try {
      const resp = await fetch(profile.sample_url);
      if (resp.ok) {
        const blob = await resp.blob();
        const file = new File([blob], `${profile.name}_sample.wav`, { type: 'audio/wav' });
        setRefAudio(file);
      } else {
        useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
      }
    } catch (err) {
      console.error("Failed to load reference audio from profile:", err);
      useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
    } finally {
      setLoadingAudio(false);
    }
```

- [ ] **Step 3: Toast on generation failure in `handleGenerate`**

Replace the `catch` of `handleGenerate` (currently):

```ts
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
```

with:

```ts
    } catch (err) {
      console.error(err);
      useToastStore.getState().addToast('Échec de la génération de la voix.', 'error');
    } finally {
      setLoading(false);
    }
```

- [ ] **Step 4: Typecheck and lint the change**

Run (from `frontend/`):
- `npx tsc --noEmit`
- `npx eslint src/pages/labs/MangaVoicePage.tsx`

Expected: both pass with no errors. (No component test exists for MangaVoicePage, matching the AudioLabPage reference; typecheck + lint are the gate for this file.)

- [ ] **Step 5: Run the offline regression test + commit**

Run (from `frontend/`): `npx vitest run src/features/manga-reader/offline/useChapterDownload.test.ts`
Expected: 6 passing (confirms Task 1 still green).

```bash
git add frontend/src/pages/labs/MangaVoicePage.tsx
git commit -m "feat(frontend): toast on MangaVoice sample-load and generation failures"
```

---

## Self-Review

**Spec coverage:**
- Offline path toast in `useChapterDownload` hook → Task 1. ✓
- MangaVoicePage `handleSelectProfile` (catch + `!resp.ok` else) → Task 2 Step 2. ✓
- MangaVoicePage `handleGenerate` catch → Task 2 Step 3. ✓
- `api.ts:357` untouched (already harmonized) → not in any task, per spec non-goals. ✓
- TDD for the hook (extend hook test) → Task 1. ✓
- MangaVoicePage verified by typecheck/lint (no harness) → Task 2 Step 4. ✓
- `console.error` lines kept → Tasks show them retained. ✓
- Exact French copy reused → strings literal in both tasks. ✓

**Placeholder scan:** none — every edit shows full before/after code; commands and expected outputs are literal.

**Type/name consistency:** `useToastStore.getState().addToast(msg, 'error')` used identically in both tasks; import paths match the file locations (`../../../store/toastStore` for the hook/test, `../../store/toastStore` for MangaVoicePage); the offline message variable `msg` is the resolved error string asserted in the Task 1 test via `expect.stringContaining('stockage')`.
