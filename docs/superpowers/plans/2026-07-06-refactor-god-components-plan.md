# Refactor God Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the three frontend pages (ForgePage, SynapticLabPage, and UndercoverRoom) from bloated single-file "God Components" into modular custom hooks and clean presentation subcomponents.

**Architecture:** Logic extraction into hooks in `frontend/src/hooks/`, presentational layout isolation into components in `frontend/src/components/`, and slim orchestration pages.

**Tech Stack:** React, TypeScript, React Query (@tanstack/react-query), Vitest, Tailwind CSS, Lucide icons, Framer Motion.

---

### Task 1: ForgePage Custom Hook Extraction

**Files:**
- Create: `frontend/src/hooks/useForge.ts`
- Test: `frontend/src/hooks/__tests__/useForge.test.ts`

- [ ] **Step 1: Write the hook implementation**

Create the custom hook in `frontend/src/hooks/useForge.ts`:

```typescript
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../store/authStore';
import { startFusion, getFusionStatus, FusionResponse, FusionStatus } from '../api';
import { SearchItem } from '../types';

export const FUSION_COST = 78;

export function useForge() {
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const walletBalance = useAuthStore((s) => s.user?.wallet_balance ?? 0);

  const [itemA, setItemA] = useState<SearchItem | null>(null);
  const [itemB, setItemB] = useState<SearchItem | null>(null);
  const [chaosLevel, setChaosLevel] = useState<number>(50);
  const [balance, setBalance] = useState<number>(50);
  const [artStyle, setArtStyle] = useState<string>('Cyberpunk');
  const [styleDir, setStyleDir] = useState<number>(0);

  const [isGenerating, setIsLoading] = useState<boolean>(false);
  const [fusionData, setFusionData] = useState<FusionResponse | null>(null);
  const [status, setStatus] = useState<FusionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);

  const errLoginRequired = t('games.forge.errors.login_required', 'Connexion requise pour forger une réalité.');
  const errInsufficientBx = t('games.forge.errors.insufficient_bx', { defaultValue: 'Berrix insuffisants — la fusion coûte {{cost}} Bx.', cost: FUSION_COST });

  const handleStartFusion = async () => {
    if (!isAuthenticated) {
      setError(errLoginRequired);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await startFusion({
        title_A: itemA?.title || itemA?.name,
        title_B: itemB?.title || itemB?.name,
        chaos_level: chaosLevel,
        universe_balance: balance,
        art_style: artStyle
      });
      setFusionData(res);
    } catch (err) {
      const httpStatus = (err as { status?: number }).status;
      if (httpStatus === 401 || httpStatus === 403) {
        setError(errLoginRequired);
      } else if (httpStatus === 402) {
        setError(errInsufficientBx);
      } else {
        setError(t('games.forge.errors.reactor_overheat', 'Le réacteur de fusion a surchauffé. Réessayez plus tard.'));
      }
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (fusionData && !status?.completed) {
      interval = setInterval(async () => {
        try {
          const res = await getFusionStatus(fusionData.task_id, fusionData.fusion_id);
          setStatus(res);
          if (res.completed) {
            setIsLoading(false);
            setShowConfetti(true);
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fusionData, status, t]);

  const resetForge = () => {
    setItemA(null);
    setItemB(null);
    setChaosLevel(50);
    setBalance(50);
    setArtStyle('Cyberpunk');
    setIsLoading(false);
    setFusionData(null);
    setStatus(null);
    setError(null);
    setShowConfetti(false);
  };

  return {
    itemA, setItemA,
    itemB, setItemB,
    chaosLevel, setChaosLevel,
    balance, setBalance,
    artStyle, setArtStyle,
    styleDir, setStyleDir,
    isGenerating,
    fusionData,
    status,
    error,
    showConfetti,
    walletBalance,
    isAuthenticated,
    handleStartFusion,
    resetForge
  };
}
```

- [ ] **Step 2: Create unit tests for useForge hook**

Write tests verifying setup, startFusion behavior, and state reset.

- [ ] **Step 3: Run the unit test to verify it passes**

Run: `npx vitest run frontend/src/hooks/__tests__/useForge.test.ts`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useForge.ts frontend/src/hooks/__tests__/useForge.test.ts
git commit -m "feat(forge): extract useForge custom hook"
```

---

### Task 2: Refactor ForgePage Presentational Subcomponents

**Files:**
- Create: `frontend/src/components/forge/ForgeItemSelector.tsx`
- Create: `frontend/src/components/forge/ForgeReactorPanel.tsx`
- Create: `frontend/src/components/forge/ForgeResultDisplay.tsx`
- Modify: `frontend/src/pages/games/ForgePage.tsx`

- [ ] **Step 1: Create ForgeItemSelector component**
Extract the card selectors for itemA & itemB and the search layout.

- [ ] **Step 2: Create ForgeReactorPanel component**
Extract the chaos sliders, balance slider, art styles selector, and simulation log terminal.

- [ ] **Step 3: Create ForgeResultDisplay component**
Extract the final generated imagery, story, video player, share button, and favorite triggers.

- [ ] **Step 4: Rewrite ForgePage.tsx to coordinate elements**
Update `ForgePage.tsx` using `useForge` hook and the newly created presentation components.

- [ ] **Step 5: Run Vitest to check ForgePage tests**

Run: `npx vitest run ForgePage`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/forge/ frontend/src/pages/games/ForgePage.tsx
git commit -m "refactor(forge): decompose ForgePage into presentational subcomponents"
```

---

### Task 3: SynapticLabPage Custom Hook Extraction

**Files:**
- Create: `frontend/src/hooks/useSynapticLab.ts`
- Test: `frontend/src/hooks/__tests__/useSynapticLab.test.ts`

- [ ] **Step 1: Write the hook implementation**

Create hook in `frontend/src/hooks/useSynapticLab.ts`:

```typescript
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../utils/apiClient';
import { UnifiedPlasticityState, PersonalizationFeatures } from '../types';

export function useSynapticLab() {
  const { data: state, isLoading, isError, refetch } = useQuery<UnifiedPlasticityState>({
    queryKey: ['singularity-lab-state'],
    queryFn: () => apiClient('/api/v1/singularity-lab/'),
  });

  const [tauPlus, setTauPlus] = useState(20.0);
  const [tauMinus, setTauMinus] = useState(20.0);
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [manualArchetype, setManualArchetype] = useState('shonen_hero');
  const [intensityMult, setIntensityMult] = useState(1.0);
  const [features, setFeatures] = useState<PersonalizationFeatures>({
    aura: true,
    font: true,
    accent: true,
  });

  const [preConcept, setPreConcept] = useState('');
  const [postConcept, setPostConcept] = useState('');

  const updateConfigMutation = useMutation({
    mutationFn: (config: { tau_plus: number; tau_minus: number }) =>
      apiClient('/api/v1/singularity-lab/config/', { method: 'POST', body: config }),
    onSuccess: () => refetch(),
  });

  const updatePersonalizationMutation = useMutation({
    mutationFn: (settings: any) =>
      apiClient('/api/v1/singularity-lab/personalization/', { method: 'POST', body: settings }),
    onSuccess: () => refetch(),
  });

  const runStdpStepMutation = useMutation({
    mutationFn: (step: { pre_concept: string; post_concept: string }) =>
      apiClient('/api/v1/singularity-lab/stdp-step/', { method: 'POST', body: step }),
    onSuccess: () => refetch(),
  });

  const resetWeightsMutation = useMutation({
    mutationFn: () =>
      apiClient('/api/v1/singularity-lab/reset/', { method: 'POST' }),
    onSuccess: () => refetch(),
  });

  const handleUpdateConfig = () => {
    updateConfigMutation.mutate({ tau_plus: tauPlus, tau_minus: tauMinus });
  };

  const handleUpdatePersonalization = () => {
    updatePersonalizationMutation.mutate({
      mode,
      manual_archetype: manualArchetype,
      intensity_multiplier: intensityMult,
      features,
    });
  };

  const handleRunStdpStep = () => {
    if (!preConcept || !postConcept) return;
    runStdpStepMutation.mutate({ pre_concept: preConcept, post_concept: postConcept });
  };

  const handleResetWeights = () => {
    resetWeightsMutation.mutate();
  };

  return {
    state,
    isLoading,
    isError,
    refetch,
    tauPlus, setTauPlus,
    tauMinus, setTauMinus,
    mode, setMode,
    manualArchetype, setManualArchetype,
    intensityMult, setIntensityMult,
    features, setFeatures,
    preConcept, setPreConcept,
    postConcept, setPostConcept,
    handleUpdateConfig,
    handleUpdatePersonalization,
    handleRunStdpStep,
    handleResetWeights,
    isConfigMutating: updateConfigMutation.isPending,
    isPersonalizationMutating: updatePersonalizationMutation.isPending,
    isStdpMutating: runStdpStepMutation.isPending,
    isResetMutating: resetWeightsMutation.isPending,
    stdpResult: runStdpStepMutation.data,
  };
}
```

- [ ] **Step 2: Create unit tests for useSynapticLab**

- [ ] **Step 3: Run the unit test to verify it passes**

Run: `npx vitest run useSynapticLab`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useSynapticLab.ts frontend/src/hooks/__tests__/useSynapticLab.test.ts
git commit -m "feat(labs): extract useSynapticLab custom hook"
```

---

### Task 4: Refactor SynapticLabPage Presentational Subcomponents

**Files:**
- Create: `frontend/src/components/labs/SynapticConfigPanel.tsx`
- Create: `frontend/src/components/labs/SynapticWeightMatrix.tsx`
- Create: `frontend/src/components/labs/SynapticSimulationPanel.tsx`
- Modify: `frontend/src/pages/labs/SynapticLabPage.tsx`

- [ ] **Step 1: Create SynapticConfigPanel component**
Extract STDP constant config forms and personal customization details.

- [ ] **Step 2: Create SynapticWeightMatrix component**
Extract the interactive canvas/table layout showing synaptic concepts and current weights.

- [ ] **Step 3: Create SynapticSimulationPanel component**
Extract input select tools for stimulation, step executions, and dynamic output alerts.

- [ ] **Step 4: Rewrite SynapticLabPage.tsx**
Use the custom hook and new subcomponents inside the main page component.

- [ ] **Step 5: Run tests for SynapticLabPage**

Run: `npx vitest run SynapticLabPage`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/labs/ frontend/src/pages/labs/SynapticLabPage.tsx
git commit -m "refactor(labs): decompose SynapticLabPage into presentational subcomponents"
```

---

### Task 5: UndercoverRoom Custom Hook Extraction

**Files:**
- Create: `frontend/src/hooks/useUndercoverRoom.ts`
- Test: `frontend/src/hooks/__tests__/useUndercoverRoom.test.ts`

- [ ] **Step 1: Write the hook implementation**

Create hook in `frontend/src/hooks/useUndercoverRoom.ts`:

```typescript
import { useState, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import useSocket from './useSocket';
import { UPlayer, UMsg, UResult } from '../types';

export function useUndercoverRoom() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const [searchParams] = useSearchParams();

  const createVisibility = searchParams.get('visibility') || undefined;
  const extraQuery = useMemo(
    () => (createVisibility ? { visibility: createVisibility } : undefined),
    [createVisibility],
  );

  const { gameState, connected, sendAction } = useSocket(roomCode, 'undercover', extraQuery);
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [guess, setGuess] = useState('');
  const [vote, setVote] = useState<{ round: number; target: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const gs = (gameState || {}) as Record<string, unknown>;
  const players = (gs.players as UPlayer[]) || [];
  const myId = gs.myId as string | undefined;
  const me = players.find((p) => p.id === myId);
  const isHost = !!me?.is_host;
  const state = (gs.state as string) || 'lobby';
  const messages = (gs.messages as UMsg[]) || [];
  const myRole = (gs.private_role as UPlayer) || {};
  const categories = (gs.categories as string[]) || ['Anime'];
  const difficulty = (gs.difficulty as string) || 'Normal';
  const visibility = (gs.visibility as string) || 'private';
  const isPublic = visibility === 'public';
  const numUnder = (gs.num_undercovers as number) || 1;
  const numWhite = (gs.num_mrwhites as number) || 0;
  const round = (gs.round as number) || 0;
  const pendingWhite = gs.pending_white as string | undefined;
  const pendingWhiteName = gs.pending_white_name as string | undefined;
  const result = gs.result as UResult | null;
  const civilWord = gs.civil_word as string | undefined;
  const undercoverWord = gs.undercover_word as string | undefined;

  const joinRoom = () => {
    if (!name.trim()) return;
    sendAction('join', { name });
  };

  const handleStartGame = (cats: string[], diff: string, under: number, white: number) => {
    sendAction('start_game', {
      categories: cats,
      difficulty: diff,
      num_undercovers: under,
      num_mrwhites: white,
    });
  };

  const handleCastVote = (targetId: string) => {
    if (!me?.alive || state !== 'playing') return;
    setVote({ round, target: targetId });
    sendAction('vote', { target: targetId });
  };

  const handleMrWhiteGuess = () => {
    if (!guess.trim() || state !== 'mrwhite_guess') return;
    sendAction('mrwhite_guess', { word: guess });
    setGuess('');
  };

  const handleSendChat = () => {
    if (!chat.trim()) return;
    sendAction('chat', { text: chat });
    setChat('');
  };

  const handleRestart = () => {
    sendAction('restart', {});
    setVote(null);
  };

  const handleCopyRoomCode = () => {
    navigator.clipboard.writeText(roomCode || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return {
    roomCode,
    connected,
    players,
    myId,
    me,
    isHost,
    state,
    messages,
    myRole,
    categories,
    difficulty,
    visibility,
    isPublic,
    numUnder,
    numWhite,
    round,
    pendingWhite,
    pendingWhiteName,
    result,
    civilWord,
    undercoverWord,

    // Local form states
    name, setName,
    chat, setChat,
    guess, setGuess,
    vote, setVote,
    copied,

    // Action Handlers
    joinRoom,
    handleStartGame,
    handleCastVote,
    handleMrWhiteGuess,
    handleSendChat,
    handleRestart,
    handleCopyRoomCode,
  };
}
```

- [ ] **Step 2: Create unit tests for useUndercoverRoom**

- [ ] **Step 3: Run the unit test to verify it passes**

Run: `npx vitest run useUndercoverRoom`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useUndercoverRoom.ts frontend/src/hooks/__tests__/useUndercoverRoom.test.ts
git commit -m "feat(undercover): extract useUndercoverRoom custom hook"
```

---

### Task 6: Refactor UndercoverRoom Presentational Subcomponents

**Files:**
- Create: `frontend/src/components/games/UndercoverJoinForm.tsx`
- Create: `frontend/src/components/games/UndercoverLobbySettings.tsx`
- Create: `frontend/src/components/games/UndercoverGameBoard.tsx`
- Create: `frontend/src/components/games/UndercoverChatPanel.tsx`
- Create: `frontend/src/components/games/UndercoverActionCenter.tsx`
- Modify: `frontend/src/pages/games/UndercoverRoom.tsx`

- [ ] **Step 1: Create UndercoverJoinForm component**
Extract overlay form taking user pseudonym.

- [ ] **Step 2: Create UndercoverLobbySettings component**
Extract game parameters adjustment layout, visibility labels, host crown display, and ready metrics.

- [ ] **Step 3: Create UndercoverGameBoard component**
Extract the player grid UI including badges for alive/dead/voted indicators.

- [ ] **Step 4: Create UndercoverChatPanel component**
Extract socket messaging text lists and chat sending controllers.

- [ ] **Step 5: Create UndercoverActionCenter component**
Extract results, Mr White guessing buttons, and game restart commands.

- [ ] **Step 6: Rewrite UndercoverRoom.tsx**
Bring hook data and presentational pieces together.

- [ ] **Step 7: Run tests for UndercoverRoom**

Run: `npx vitest run UndercoverRoom`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/games/Undercover* frontend/src/pages/games/UndercoverRoom.tsx
git commit -m "refactor(undercover): decompose UndercoverRoom into presentational subcomponents"
```

---

### Task 7: Comprehensive Project Verification

- [ ] **Step 1: Validate TypeScript type definitions**

Run: `npm run check-types`
Expected: Clean build, no compilation errors.

- [ ] **Step 2: Run all frontend unit tests**

Run: `npx vitest run`
Expected: All 611 tests pass successfully.
