# Voice Cloning Frontend Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frontend API function and React hook for the new Voice Cloning (RVC) feature.

**Architecture:** Use `apiClient` for backend communication and `TanStack Query` (React Query) for state management and mutations.

**Tech Stack:** TypeScript, React, TanStack Query (React Query).

---

### Task 1: Add `cloneVoice` to API

**Files:**
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Implement `cloneVoice` function**

Add the following function at the end of `frontend/src/api.ts`:

```typescript
// --- Labs API ---
export async function cloneVoice(text: string, audioFile: File, pitch: number): Promise<{ audio_data: string }> {
  const formData = new FormData();
  formData.append('target_text', text);
  formData.append('reference_audio', audioFile);
  formData.append('pitch', pitch.toString());

  return apiClient('/api/v1/labs/voice-cloning/', {
    method: 'POST',
    body: formData,
    headers: {} // Let browser set Content-Type for FormData
  });
}
```

- [ ] **Step 2: Commit API changes**

```bash
git add frontend/src/api.ts
git commit -m "feat(frontend): add cloneVoice to api.ts"
```

### Task 2: Create `useVoiceCloning` hook

**Files:**
- Create: `frontend/src/features/labs/hooks/useVoiceCloning.ts`

- [ ] **Step 1: Implement the hook**

Create the file `frontend/src/features/labs/hooks/useVoiceCloning.ts` with the following content:

```typescript
import { useMutation } from '@tanstack/react-query';
import { cloneVoice } from '../../../api';

export const useVoiceCloning = () => {
  const mutation = useMutation({
    mutationFn: ({ text, audioFile, pitch }: { text: string, audioFile: File, pitch: number }) => 
      cloneVoice(text, audioFile, pitch),
  });

  return {
    clone: mutation.mutateAsync,
    isLoading: mutation.isPending,
    result: mutation.data,
    error: mutation.error
  };
};
```

- [ ] **Step 2: Commit the hook**

```bash
git add frontend/src/features/labs/hooks/useVoiceCloning.ts
git commit -m "feat(frontend): create useVoiceCloning hook"
```

### Task 3: Final Verification

- [ ] **Step 1: Check for compilation errors**

Run: `npm run tsc` in `frontend` directory (if available) or just check file for lint/type errors.

- [ ] **Step 2: Final commit**

If everything is correct, combine commits if necessary or just verify `git status`.
