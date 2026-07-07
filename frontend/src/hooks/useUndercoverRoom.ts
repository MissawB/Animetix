import { useState, useMemo, useEffect } from 'react';
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

  const maxThreats = Math.max(1, Math.floor((players.length - 1) / 2));
  const under = Math.min(numUnder, Math.max(1, maxThreats - numWhite));
  const white = Math.min(numWhite, Math.max(0, maxThreats - under));
  const civilsCount = Math.max(0, players.length - under - white);
  const voteTarget = vote && vote.round === round ? vote.target : null;

  const maxUnderSlider = Math.max(1, maxThreats - white);
  const maxWhiteSlider = Math.max(0, maxThreats - under);

  const submitName = () => {
    if (name.trim()) {
      sendAction('set_name', { name: name.trim() });
    }
  };

  const castVote = (id: string) => {
    const target = players.find((p) => p.id === id);
    if (state !== 'playing' || id === myId || !me?.alive || target?.alive === false) return;
    setVote({ round, target: id });
    sendAction('vote', { voted_for: id });
  };

  const submitGuess = (e: React.FormEvent) => {
    e.preventDefault();
    if (guess.trim()) {
      sendAction('mrwhite_guess', { guess: guess.trim() });
      setGuess('');
    }
  };

  const sendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (chat.trim()) {
      sendAction('chat', { message: chat.trim() });
      setChat('');
    }
  };

  const copyCode = () => {
    const code = (roomCode || '').toUpperCase();
    navigator.clipboard?.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const applySettings = (patch: Record<string, unknown>) => {
    sendAction('set_settings', {
      categories,
      difficulty,
      num_undercovers: under,
      num_mrwhites: white,
      visibility,
      ...patch,
    });
  };

  const toggleCategory = (key: string) => {
    const next = categories.includes(key)
      ? categories.filter((c) => c !== key)
      : [...categories, key];
    applySettings({ categories: next });
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
    maxThreats,
    under,
    white,
    civilsCount,
    voteTarget,
    maxUnderSlider,
    maxWhiteSlider,

    // Local form states
    name, setName,
    chat, setChat,
    guess, setGuess,
    vote, setVote,
    copied,

    // Handlers
    submitName,
    castVote,
    submitGuess,
    sendChat,
    copyCode,
    applySettings,
    toggleCategory,
    sendAction,
  };
}
