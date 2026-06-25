# Design — Harmonize failure toasts on raw-`fetch` sites

**Date:** 2026-06-25
**Status:** Approved
**TODO source:** "Frontend — `fetch()` brut : reliquat optionnel — Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357] (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin)." ([TODO.md](../../TODO.md))

## Problem

Three raw-`fetch` failure paths only `console.error` (or render an inline icon) instead of surfacing a
user-visible toast, unlike the reference `AudioLabPage` which already does
`useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error')` on its raw
fetch failure ([AudioLabPage.tsx:122-138](../../frontend/src/pages/labs/AudioLabPage.tsx)). The raw
fetches themselves are intentional (binary assets / cross-origin) and stay; only the error UX is
harmonized.

## Current state (verified)

- **`MangaVoicePage`** — `handleSelectProfile` raw-fetches `profile.sample_url`; on `catch` it only
  `console.error`s, and on `!resp.ok` it silently does nothing
  ([MangaVoicePage.tsx:58-69](../../frontend/src/pages/labs/MangaVoicePage.tsx#L58-L69)).
  `handleGenerate` calls `apiClient(...)` and its `catch` only `console.error`s
  ([:72-93](../../frontend/src/pages/labs/MangaVoicePage.tsx#L72-L93)). No toast import today.
- **`offlineLibrary`** — `downloadChapter` raw-fetches each page and throws on failure (rolling back),
  including a specific `OfflineQuotaError`
  ([offlineLibrary.ts:102-149](../../frontend/src/features/manga-reader/offline/offlineLibrary.ts#L102-L149)).
  The consumer hook `useChapterDownload.download` catches and sets `status='error'` + `error`
  ([useChapterDownload.ts:40-55](../../frontend/src/features/manga-reader/offline/useChapterDownload.ts#L40-L55));
  `ChapterDownloadButton` renders only an inline `AlertCircle` + `title={error}` tooltip — no toast.
- **`api.ts:357` (`downloadDataset`)** — its only caller `OpenDataPage.handleDownload` ALREADY toasts
  on failure (`addToast("Échec du téléchargement de ${dataset.name}.", "error")`,
  [OpenDataPage.tsx:38-40](../../frontend/src/pages/social/OpenDataPage.tsx#L38-L40)). Already harmonized.
- Toast API: `useToastStore.getState().addToast(message: string, type: 'error' | 'info' | 'success')`.

## Goals / non-goals

**Goals**
1. Surface a failure toast on the offline chapter-download path and on both MangaVoicePage failure
   paths, matching the AudioLabPage pattern and French copy style.
2. Keep the raw fetches and the pure `offlineLibrary` service unchanged.

**Non-goals**
- Touch `api.ts`/`downloadDataset`/`OpenDataPage` — already harmonized (out of scope, confirmed).
- Replace any raw fetch with `apiClient` (the raw fetches are intentional).
- Add toasts inside the pure `offlineLibrary` service (keep it UI-agnostic).
- A new MangaVoicePage component test (none exists; the reference AudioLabPage has none either —
  verified via typecheck/lint/build instead).

## Design

### 1. `useChapterDownload.ts`
Import `useToastStore`. In `download()`'s `catch`, fire the toast reusing the resolved message so the
specific `OfflineQuotaError` text is surfaced:

```ts
} catch (err) {
  if (!mounted.current) return;
  const msg = err instanceof Error ? err.message : 'Échec du téléchargement.';
  setError(msg);
  useToastStore.getState().addToast(msg, 'error');
  setStatus('error');
}
```

`ChapterDownloadButton` and `offlineLibrary` are unchanged.

### 2. `MangaVoicePage.tsx`
Import `useToastStore`. Add toasts on both paths:

- `handleSelectProfile` — toast in `catch` AND add an `else` for `!resp.ok`, both with
  `"Échec du chargement de l'échantillon vocal."` (identical text to AudioLabPage):

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

- `handleGenerate` — toast in `catch` with `"Échec de la génération de la voix."`:

```ts
} catch (err) {
  console.error(err);
  useToastStore.getState().addToast('Échec de la génération de la voix.', 'error');
} finally {
  setLoading(false);
}
```

`console.error` lines are kept (developer diagnostics) alongside the new user-facing toast.

## Error handling / copy

- Use `'error'` toast type throughout.
- Reuse AudioLabPage's exact string for sample-load failure; new strings for generation
  (`"Échec de la génération de la voix."`) and offline (the caught error's `.message`, falling back to
  `"Échec du téléchargement."`).

## Testing

- **TDD (hook):** extend the existing error-path test
  ([useChapterDownload.test.ts:40-50](../../frontend/src/features/manga-reader/offline/useChapterDownload.test.ts#L40-L50))
  to also assert `useToastStore.getState().addToast` was called with `'error'` on a rejected
  `downloadChapter` (mock/spy the store). The test already mocks `downloadChapter` to reject with
  `OfflineQuotaError`, so the assertion also confirms the specific message is toasted.
- **MangaVoicePage:** no new component test (no harness exists; mirrors the untested-by-inspection
  AudioLabPage reference). Verify via `tsc` typecheck, lint, and the frontend build.
- Run the existing frontend test suite as the regression gate.

## Risks / mitigations

- **Risk:** double-toast on the offline path if a future consumer also toasts. *Mitigation:* the hook
  is the single agreed source; `ChapterDownloadButton` only renders inline state.
- **Risk:** the hook test needs the toast store mocked without breaking the existing assertions.
  *Mitigation:* spy on `useToastStore.getState` / `addToast`; keep the existing status/message
  assertions intact.

## Out of scope / follow-up

- `api.ts` / `OpenDataPage` (already harmonized).
- Any broader migration of raw fetches to `apiClient`.
