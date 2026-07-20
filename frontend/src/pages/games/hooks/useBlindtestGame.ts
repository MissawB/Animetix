import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useBlindtestStore } from '../../../features/games/stores/blindtestStore';
import { blindtestService } from '../../../features/games/services/blindtestService';
import { normalizeText } from '../../../utils/normalizeText';

// Local binding used across the hook; also re-exported under its historical
// name for any consumer that imported `norm` from here.
const norm = normalizeText;
export { norm };

export type HintType = 'invert' | 'blur' | 'grayscale' | 'hue' | 'noise';
export const HINT_TYPES: HintType[] = ['invert', 'blur', 'grayscale', 'hue', 'noise'];
export const SCORE_TIERS = [100, 50, 25, 10, 0];
export const PLAYABLE_LOCALES = ['ja', 'fr'];

export const pickHint = (): HintType => HINT_TYPES[Math.floor(Math.random() * HINT_TYPES.length)];

export const useBlindtestGame = () => {
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useBlindtestStore();
  const location = useLocation();
  const navigate = useNavigate();

  const cfg = location.state as {
    mode?: 'session' | 'single';
    type?: 'OP' | 'ED';
    difficulty?: string;
    length?: number;
    hints?: boolean;
    guessArtist?: boolean;
    guessSequence?: boolean;
  } | null;

  const mode = cfg?.mode ?? 'single';
  const sessionLength = cfg?.length ?? 1;
  const hintsEnabled = cfg?.hints ?? false;
  const guessArtist = cfg?.guessArtist ?? false;
  const guessSequence = cfg?.guessSequence ?? false;
  const launchType = cfg?.type;
  const launchDifficulty = cfg?.difficulty;

  const [guess, setGuess] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [round, setRound] = useState(1);
  const [totalScore, setTotalScore] = useState(0);
  const [results, setResults] = useState<{ score: number; won: boolean; secret?: string }[]>([]);
  const [sessionOver, setSessionOver] = useState(false);
  const [hintType, setHintType] = useState<HintType>(() => pickHint());
  const [aspect, setAspect] = useState(16 / 9);
  const [titles, setTitles] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSug, setShowSug] = useState(false);

  // Bonus objectives (singer / opening number)
  const [artistGuess, setArtistGuess] = useState('');
  const [seqGuess, setSeqGuess] = useState('');
  const [bonusDone, setBonusDone] = useState(false);
  const [artistCorrect, setArtistCorrect] = useState(false);
  const [seqCorrect, setSeqCorrect] = useState(false);
  const mediaRef = useRef<HTMLVideoElement>(null);

  // Start the chosen format/difficulty; otherwise resume / auto-start.
  useEffect(() => {
    if (launchType) restartGame(launchType, launchDifficulty);
    else loadGame();
  }, [launchType, launchDifficulty, loadGame, restartGame]);

  // Anime titles for the guess autocomplete (fetched once).
  useEffect(() => {
    let active = true;
    blindtestService
      .getTitles()
      .then((t: string[]) => {
        if (active) setTitles(t);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const onSubmit = (value?: string) => {
    const g = (value ?? guess).trim();
    if (!g) return;
    submitGuess(g);
    setGuess('');
    setSuggestions([]);
    setShowSug(false);
  };

  const onGuessChange = (val: string) => {
    setGuess(val);
    const q = norm(val.trim());
    if (q.length < 2) {
      setSuggestions([]);
      setShowSug(false);
      return;
    }
    const starts: string[] = [];
    const incl: string[] = [];
    for (const t of titles) {
      const n = norm(t);
      if (n.startsWith(q)) starts.push(t);
      else if (n.includes(q)) incl.push(t);
      if (starts.length >= 8) break;
    }
    const sug = [...starts, ...incl].slice(0, 8);
    setSuggestions(sug);
    setShowSug(sug.length > 0);
  };

  const pick = (title: string) => onSubmit(title);

  const togglePlay = () => {
    const el = mediaRef.current;
    if (!el) return;
    if (el.paused) el.play().catch(() => {});
    else el.pause();
  };

  const currentMode: 'OP' | 'ED' = gameState?.theme_type === 'ED' ? 'ED' : 'OP';
  const lost = gameState?.gameOver && gameState?.won === false;
  const maxAttempts = gameState?.maxAttempts ?? 4;
  const used = gameState?.guesses.length ?? 0;
  // Visual hint only after the first guess; round always opens on the vinyl.
  const showVisual = hintsEnabled && !gameState?.gameOver && used >= 1;
  const hintSteps = Math.max(1, maxAttempts - 1);
  const hintLevel = used >= 1 ? Math.max(0, 1 - (used - 1) / hintSteps) : 1;
  const correctIdx =
    gameState?.guesses.findIndex((g: { is_correct: boolean }) => g.is_correct) ?? -1;
  const baseScore = gameState?.won && correctIdx >= 0 ? (SCORE_TIERS[correctIdx] ?? 0) : 0;

  // Bonus objectives — only when won and the data is available for this theme.
  const artistAvailable = !!(gameState?.artists && gameState?.artists.length);
  const sequenceAvailable = gameState?.sequence != null && gameState?.sequence !== '';
  const bonusArtistOn = guessArtist && artistAvailable;
  const bonusSeqOn = guessSequence && sequenceAvailable;
  const bonusEnabled = !!gameState?.won && (bonusArtistOn || bonusSeqOn);
  const bonusPending = bonusEnabled && !bonusDone;
  const bonusScore =
    (bonusArtistOn && artistCorrect ? 25 : 0) + (bonusSeqOn && seqCorrect ? 25 : 0);
  const roundScore = baseScore + bonusScore;

  const resetBonus = () => {
    setBonusDone(false);
    setArtistCorrect(false);
    setSeqCorrect(false);
    setArtistGuess('');
    setSeqGuess('');
  };

  const validateBonus = () => {
    if (bonusArtistOn && gameState) {
      const g = norm(artistGuess);
      setArtistCorrect(
        !!g &&
          (gameState.artists ?? []).some((a: string) => {
            const n = norm(a);
            return n.includes(g) || g.includes(n);
          }),
      );
    }
    if (bonusSeqOn && gameState) {
      const want = String(gameState.sequence ?? '').replace(/[^0-9]/g, '');
      const got = seqGuess.replace(/[^0-9]/g, '');
      setSeqCorrect(!!got && got === want);
    }
    setBonusDone(true);
  };

  const replay = () => {
    resetBonus();
    restartGame(currentMode, gameState?.difficulty);
  };

  const finishRound = () => {
    setResults((r) => [
      ...r,
      { score: roundScore, won: !!gameState?.won, secret: gameState?.secret_title },
    ]);
    setTotalScore((t) => t + roundScore);
    if (round >= sessionLength) {
      setSessionOver(true);
    } else {
      setRound((r) => r + 1);
      setHintType(pickHint());
      resetBonus();
      restartGame(launchType ?? currentMode, launchDifficulty ?? gameState?.difficulty);
    }
  };

  return {
    // State / derived states
    gameState,
    isLoading,
    error,
    mode,
    sessionLength,
    hintsEnabled,
    guessArtist,
    guessSequence,
    currentMode,
    lost,
    maxAttempts,
    used,
    showVisual,
    hintLevel,
    hintType,
    setHintType,
    aspect,
    setAspect,
    correctIdx,
    baseScore,
    round,
    totalScore,
    results,
    sessionOver,
    guess,
    setGuess,
    isPlaying,
    setIsPlaying,
    suggestions,
    showSug,
    setShowSug,
    artistGuess,
    setArtistGuess,
    seqGuess,
    setSeqGuess,
    bonusDone,
    artistCorrect,
    seqCorrect,
    bonusArtistOn,
    bonusSeqOn,
    bonusEnabled,
    bonusPending,
    bonusScore,
    roundScore,
    lastRound: round >= sessionLength,
    mediaRef,
    // Actions
    onSubmit,
    onGuessChange,
    pick,
    togglePlay,
    validateBonus,
    finishRound,
    replay,
    navigate,
    restartGame,
  };
};
