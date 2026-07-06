# Design Specification - Refactoring Frontend God Components

**Date:** 2026-07-06  
**Status:** Approved  

This specification outlines the architecture, file organization, and implementation strategy to refactor three large frontend components (God Components) into clean, testable custom hooks and smaller, single-responsibility presentational components.

---

## 1. ForgePage Refactoring (`frontend/src/pages/games/ForgePage.tsx`)

### 1.1 Custom Hook: `frontend/src/hooks/useForge.ts`
Manages the state and API calls for the Reality Forge page.

```typescript
import { useState, useEffect, useMemo } from 'react';
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

### 1.2 Extracted Subcomponents
* **`ForgeItemSelector`** (`frontend/src/components/forge/ForgeItemSelector.tsx`)
  - Inputs: Selected `itemA`, `itemB`, and setters.
  - Responsibility: Render search inputs, autocomplete dropdowns, and card layouts for selected entities.
* **`ForgeReactorPanel`** (`frontend/src/components/forge/ForgeReactorPanel.tsx`)
  - Inputs: Sliders states (`chaosLevel`, `balance`), `artStyle`, setters, reactor progress, active status.
  - Responsibility: Render control adjustments and reactor telemetry logs.
* **`ForgeResultDisplay`** (`frontend/src/components/forge/ForgeResultDisplay.tsx`)
  - Inputs: `fusionData`, `status`, `error`, `resetForge`.
  - Responsibility: Display resulting assets (image, video, scenario text), errors, share/favorite buttons.

---

## 2. SynapticLabPage Refactoring (`frontend/src/pages/labs/SynapticLabPage.tsx`)

### 2.1 Custom Hook: `frontend/src/hooks/useSynapticLab.ts`
Leverages React Query and local state to manage the neural plasticity simulation.

```typescript
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../utils/apiClient';
import { UnifiedPlasticityState, PersonalizationFeatures } from '../types';

export function useSynapticLab() {
  // React Query Fetch Unified State
  const { data: state, isLoading, isError, refetch } = useQuery<UnifiedPlasticityState>({
    queryKey: ['singularity-lab-state'],
    queryFn: () => apiClient('/api/v1/singularity-lab/'),
  });

  // Local Form Config state
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

  // Simulation parameters
  const [preConcept, setPreConcept] = useState('');
  const [postConcept, setPostConcept] = useState('');

  // Mutations
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

### 2.2 Extracted Subcomponents
* **`SynapticConfigPanel`** (`frontend/src/components/labs/SynapticConfigPanel.tsx`)
  - Responsibility: STDP constant adjustments and active archetype configuration settings.
* **`SynapticWeightMatrix`** (`frontend/src/components/labs/SynapticWeightMatrix.tsx`)
  - Responsibility: Interactively display the grid representing conceptual synapse weights.
* **`SynapticSimulationPanel`** (`frontend/src/components/labs/SynapticSimulationPanel.tsx`)
  - Responsibility: Controls to trigger individual STDP pre/post activations and inspect logging.

---

## 3. UndercoverRoom Refactoring (`frontend/src/pages/games/UndercoverRoom.tsx`)

### 3.1 Custom Hook: `frontend/src/hooks/useUndercoverRoom.ts`
Encapsulates room routing, Socket connection, and gameplay logic actions.

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

### 3.2 Extracted Subcomponents
* **`UndercoverJoinForm`** (`frontend/src/components/games/UndercoverJoinForm.tsx`)
  - Responsibility: Simple overlay/card form to accept user pseudonym input.
* **`UndercoverLobbySettings`** (`frontend/src/components/games/UndercoverLobbySettings.tsx`)
  - Responsibility: Room code, game configuration controls for host, and players ready count.
* **`UndercoverGameBoard`** (`frontend/src/components/games/UndercoverGameBoard.tsx`)
  - Responsibility: Visual grid of player status, word metadata, and indicators.
* **`UndercoverChatPanel`** (`frontend/src/components/games/UndercoverChatPanel.tsx`)
  - Responsibility: Scrollable transmission log and chat input box.
* **`UndercoverActionCenter`** (`frontend/src/components/games/UndercoverActionCenter.tsx`)
  - Responsibility: Host command actions, Mr White guess input, voting indicators.

---

## 4. Verification Plan

### 4.1 TypeScript Checks
Verify there are no compilation errors across the newly refactored structures:
```bash
npm run check-types
```

### 4.2 Unit Tests
Verify all unit tests pass:
```bash
npx vitest run
```
