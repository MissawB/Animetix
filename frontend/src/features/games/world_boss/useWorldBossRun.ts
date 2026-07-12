import { useCallback, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import soundManager from '../../../utils/SoundManager';

export interface BossQuestion {
  tier: number;
  band: 'A' | 'B' | 'C' | 'D';
  timer: number;
  damage: number;
  limiter_break: boolean;
  streak: number;
  run_damage: number;
  best_tier: number;
  archetype: string;
  prompt: string;
  options: string[];
  image: string | null;
}

export interface BossVerdict {
  correct: boolean;
  late: boolean;
  damage_dealt: number;
  correct_index: number;
  correct_label: string;
  subject: string;
  tier: number;
  run_damage: number;
  best_tier: number;
  limiter_break: boolean;
  streak: number;
  boss: { current_hp: number; total_hp: number; current_phase: number; is_active: boolean };
}

export type RunPhase = 'idle' | 'asking' | 'answering' | 'revealed';

/**
 * The run, end to end. The server holds the answer and the clock; this hook only
 * carries what the player picked — so a timeout is `answer(-1)`, not a client-side
 * verdict.
 */
export const useWorldBossRun = () => {
  const queryClient = useQueryClient();
  const [question, setQuestion] = useState<BossQuestion | null>(null);
  const [verdict, setVerdict] = useState<BossVerdict | null>(null);
  const [phase, setPhase] = useState<RunPhase>('idle');
  // React batches the two setPhase calls from a double-click into a single
  // render, so `phase` in the closure is still 'asking' for both — a ref is
  // the only thing that flips synchronously between them.
  const answeringRef = useRef(false);

  const ask = useMutation({
    mutationFn: () =>
      apiClient('/api/v1/game/world-boss/question/', { method: 'POST', body: '{}' }),
    onSuccess: (data: BossQuestion) => {
      answeringRef.current = false;
      setVerdict(null);
      setQuestion(data);
      setPhase('asking');
    },
  });

  const send = useMutation({
    mutationFn: (index: number) =>
      apiClient('/api/v1/game/world-boss/answer/', {
        method: 'POST',
        body: JSON.stringify({ index }),
      }),
    onSuccess: (data: BossVerdict) => {
      answeringRef.current = false;
      setVerdict(data);
      setPhase('revealed');
      soundManager.play(data.correct ? 'win' : 'loss');
      if (data.limiter_break && data.correct && data.streak === 5) soundManager.play('unlock');
      // The HP bar is shared with the whole community: refresh it now, not in 10 s.
      queryClient.invalidateQueries({ queryKey: ['world-boss', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['world-boss', 'leaderboard'] });
    },
    onError: () => {
      answeringRef.current = false;
      setPhase('asking');
    },
  });

  const answer = useCallback(
    (index: number) => {
      // A double click, or a click racing the timeout, must not post twice.
      if (phase !== 'asking' || answeringRef.current) return;
      answeringRef.current = true;
      setPhase('answering');
      send.mutate(index);
    },
    [phase, send],
  );

  const start = useCallback(() => ask.mutate(), [ask]);

  return {
    question,
    verdict,
    phase,
    start,
    answer,
    next: start,
  };
};
