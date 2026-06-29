import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Send, RotateCcw, ArrowRight, Trophy, ImageIcon, Check, X, ChevronRight } from 'lucide-react';
import { useCovertest } from '../../features/games/hooks/useCovertest';
import { covertestService } from '../../features/games/services/covertestService';
import { Card } from '../../components/ui/Card';
import { CardSkeleton } from '../../components/ui/Skeleton';

const norm = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

const MAX_ATTEMPTS: Record<string, number> = { Easy: 6, Normal: 4, Hard: 3, Impossible: 2, Tryhard: 3 };

// Tryhard: a random distortion stacked on top of the blur, easing off each guess.
type CoverFx = 'invert' | 'grayscale' | 'hue' | 'sepia' | 'noise';
const COVER_FX: CoverFx[] = ['invert', 'grayscale', 'hue', 'sepia', 'noise'];
const pickFx = (): CoverFx => COVER_FX[Math.floor(Math.random() * COVER_FX.length)];
const fxFilter = (fx: CoverFx, level: number, blurPx: number): string => {
  const L = Math.max(0, Math.min(1, level)); // 1 = hardest, 0 = revealed
  const blur = `blur(${blurPx}px)`;
  switch (fx) {
    case 'invert': return `invert(${L.toFixed(2)}) ${blur}`;
    case 'grayscale': return `grayscale(${L.toFixed(2)}) contrast(${(1 + L * 0.3).toFixed(2)}) ${blur}`;
    case 'hue': return `hue-rotate(${Math.round(L * 180)}deg) saturate(${(1 + L * 2).toFixed(2)}) ${blur}`;
    case 'sepia': return `sepia(${L.toFixed(2)}) hue-rotate(${Math.round(L * 40)}deg) ${blur}`;
    case 'noise': return `${blur} contrast(${(1 + L * 0.8).toFixed(2)}) brightness(${(1 - L * 0.25).toFixed(2)})`;
    default: return blur;
  }
};

const CovertestPage: React.FC = () => {
  const { gameState, loading, handleGuess, isGuessing, startGame, starting, revealAnswer } = useCovertest();
  const location = useLocation();
  const navigate = useNavigate();
  const cfg = location.state as { mode?: 'session' | 'single'; difficulty?: string; length?: number; guessVolume?: boolean; guessAuthor?: boolean; origin?: string } | null;
  const mode = cfg?.mode ?? 'single';
  const sessionLength = cfg?.length ?? 1;
  const difficulty = cfg?.difficulty ?? 'Normal';
  const origin = cfg?.origin || undefined;
  const maxAttempts = MAX_ATTEMPTS[difficulty] ?? 4;
  const guessVolume = !!cfg?.guessVolume;
  const guessAuthor = !!cfg?.guessAuthor;
  const tryhard = difficulty === 'Tryhard';

  const [guess, setGuess] = useState('');
  const [round, setRound] = useState(1);
  const [totalScore, setTotalScore] = useState(0);
  const [results, setResults] = useState<{ score: number; won: boolean; secret?: string }[]>([]);
  const [sessionOver, setSessionOver] = useState(false);
  const [titles, setTitles] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSug, setShowSug] = useState(false);
  // Bonus: volume + author guesses
  const [volumeGuess, setVolumeGuess] = useState('');
  const [authorGuess, setAuthorGuess] = useState('');
  const [bonusDone, setBonusDone] = useState(false);
  const [volumeCorrect, setVolumeCorrect] = useState(false);
  const [authorCorrect, setAuthorCorrect] = useState(false);
  const [fx, setFx] = useState<CoverFx>(() => pickFx());
  const started = useRef(false);

  // Fresh cover when the page mounts (new round/session).
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    startGame({ origin }).catch(() => {});
  }, [startGame, origin]);

  // Manga titles for the guess autocomplete (fetched once).
  useEffect(() => {
    let active = true;
    covertestService.getTitles().then((t) => { if (active) setTitles(t); }).catch(() => {});
    return () => { active = false; };
  }, []);

  const guesses = gameState?.guesses ?? [];
  const attemptsUsed = guesses.length;
  const won = guesses.some((g) => g.is_correct);
  const over = !!gameState?.game_over;
  const outOfTries = attemptsUsed >= maxAttempts;

  // Out of tries and not solved → reveal the answer (loss).
  useEffect(() => {
    if (gameState && !over && !won && outOfTries) {
      revealAnswer().catch(() => {});
    }
  }, [gameState, over, won, outOfTries, revealAnswer]);

  const winningIdx = guesses.findIndex((g) => g.is_correct);
  const baseScore = won && winningIdx >= 0
    ? Math.max(5, Math.round(100 * (1 - winningIdx / maxAttempts)))
    : 0;
  // Bonus objectives (only when enabled, won, and the data is available).
  const volumeAvailable = gameState?.volume != null && gameState?.volume !== '';
  const authorAvailable = !!gameState?.author;
  const volumeOn = guessVolume && volumeAvailable;
  const authorOn = guessAuthor && authorAvailable;
  const bonusActive = won && (volumeOn || authorOn);
  const bonusPending = bonusActive && !bonusDone;
  const bonusScore = (volumeOn && volumeCorrect ? 30 : 0) + (authorOn && authorCorrect ? 30 : 0);
  const roundScore = baseScore + bonusScore;

  const resetBonus = () => {
    setBonusDone(false);
    setVolumeCorrect(false);
    setAuthorCorrect(false);
    setVolumeGuess('');
    setAuthorGuess('');
  };
  const nextCover = () => {
    resetBonus();
    setFx(pickFx());
    startGame({ origin }).catch(() => {});
  };

  const validateBonus = () => {
    if (volumeOn) {
      const want = String(gameState?.volume ?? '').replace(/[^0-9]/g, '');
      const got = volumeGuess.replace(/[^0-9]/g, '');
      setVolumeCorrect(!!got && got === want);
    }
    if (authorOn) {
      const g = norm(authorGuess);
      const want = norm(String(gameState?.author ?? ''));
      // Match if the guess overlaps the author string (handles "Name" vs "Name, Other").
      setAuthorCorrect(!!g && g.length >= 2 && (want.includes(g) || g.includes(want.split(',')[0].trim())));
    }
    setBonusDone(true);
  };

  // Blur eases off with each attempt; fully revealed once the round is over.
  const blurPx = over ? 0 : Math.round(4 + Math.max(0, 1 - attemptsUsed / maxAttempts) * 20);
  // Tryhard: random distortion that also eases off, layered on the blur.
  const fxLevel = over ? 0 : Math.max(0, 1 - attemptsUsed / maxAttempts);
  const coverFilter = tryhard ? fxFilter(fx, fxLevel, blurPx) : `blur(${blurPx}px)`;

  const onChange = (val: string) => {
    setGuess(val);
    const q = norm(val.trim());
    if (q.length < 2) { setSuggestions([]); setShowSug(false); return; }
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

  // Only manga that have a cover are guessable, so a guess must resolve to a known
  // title (the autocomplete is built from the same list). Canonicalise before sending.
  const titleByNorm = useMemo(() => {
    const m = new Map<string, string>();
    for (const t of titles) m.set(norm(t), t);
    return m;
  }, [titles]);
  const guessValid = titleByNorm.has(norm(guess.trim()));

  const submit = async (value?: string) => {
    const raw = (value ?? guess).trim();
    if (!raw || isGuessing || over) return;
    const canonical = titleByNorm.get(norm(raw));
    if (!canonical) return; // not a manga with an available cover → not validable
    setShowSug(false);
    setGuess('');
    setSuggestions([]);
    try { await handleGuess({ guess: canonical }); } catch { /* toast already shown */ }
  };

  const finishRound = () => {
    setResults((r) => [...r, { score: roundScore, won, secret: gameState?.secret_title }]);
    setTotalScore((t) => t + roundScore);
    if (mode === 'session' && round < sessionLength) {
      setRound((r) => r + 1);
      nextCover();
    } else if (mode === 'session') {
      setSessionOver(true);
    } else {
      nextCover(); // single: replay a fresh cover
    }
  };

  if (loading && !gameState) {
    return <div className="max-w-3xl mx-auto px-6 py-16"><CardSkeleton /></div>;
  }

  // ── Session summary ──────────────────────────────────────────
  if (sessionOver) {
    const maxScore = sessionLength * 100;
    const wins = results.filter((r) => r.won).length;
    return (
      <div className="max-w-2xl mx-auto px-6 py-20">
        <Card padding="lg" className="text-center">
          <Trophy className="w-14 h-14 text-yellow-400 mx-auto mb-4" />
          <h1 className="text-4xl font-black italic manga-font uppercase text-black dark:text-white">Session terminée</h1>
          <p className="mt-6 text-6xl font-black manga-font text-yellow-500">{totalScore}</p>
          <p className="text-xs font-black uppercase tracking-widest text-gray-400 mt-1">sur {maxScore} points · {wins}/{sessionLength} trouvés</p>
          <div className="mt-8 grid grid-cols-5 sm:grid-cols-10 gap-1.5">
            {results.map((r, i) => (
              <div
                key={i}
                title={`Manche ${i + 1}: ${r.score} pts${r.secret ? ` — ${r.secret}` : ''}`}
                className={`h-8 rounded-md grid place-items-center text-[10px] font-black ${r.won ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-red-500/15 text-red-500'}`}
              >
                {r.score}
              </div>
            ))}
          </div>
          <div className="flex gap-3 justify-center mt-10">
            <button onClick={() => navigate('/covertest/')} className="px-8 py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-wide shadow-xl transition-all hover:scale-105 active:scale-95">
              NOUVELLE SESSION
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  const isSession = mode === 'session';
  const lastRound = round >= sessionLength;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      {/* Session progress */}
      {isSession && (
        <div className="mb-8 flex items-center justify-between gap-4">
          <span className="text-[11px] font-black uppercase tracking-widest text-gray-400">Manche {round}/{sessionLength}</span>
          <div className="flex-1 h-2 rounded-full bg-black/5 dark:bg-white/10 overflow-hidden">
            <div className="h-full rounded-full bg-yellow-400 transition-all duration-500" style={{ width: `${((round - 1) / sessionLength) * 100}%` }} />
          </div>
          <span className="text-[11px] font-black uppercase tracking-widest text-yellow-500">{totalScore} pts</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Cover */}
        <div className="relative group">
          <div className="absolute -inset-4 bg-gradient-to-tr from-yellow-400 to-orange-500 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
          <div className="relative rounded-[2.5rem] overflow-hidden shadow-2xl aspect-[2/3] bg-navy-900">
            <img
              src={gameState.cover_url}
              alt="Couverture mystère"
              className="w-full h-full object-cover transition-all duration-700"
              style={{ filter: coverFilter, transform: over ? 'scale(1.03)' : 'scale(1.08)' }}
              loading="lazy"
              decoding="async"
            />
            {!over && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="bg-black/50 backdrop-blur-md px-5 py-3 rounded-full border-2 border-white/15 flex items-center gap-2 text-white/80">
                  <ImageIcon className="w-5 h-5" />
                  <span className="text-xs font-black uppercase tracking-widest">Couverture floutée</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Game */}
        <Card padding="lg">
          <h2 className="text-4xl font-black italic manga-font mb-2 tracking-tighter uppercase">
            COVER <span className="text-yellow-400">QUEST</span>
          </h2>

          {/* Attempts dots */}
          <div className="flex items-center gap-2 mb-8">
            {Array.from({ length: maxAttempts }).map((_, i) => (
              <span
                key={i}
                className={`h-2 flex-1 rounded-full transition-colors ${
                  i < attemptsUsed ? (won && i === winningIdx ? 'bg-green-500' : 'bg-red-500/70') : 'bg-black/10 dark:bg-white/10'
                }`}
              />
            ))}
          </div>

          {!over ? (
            <div className="space-y-5">
              <div className="relative">
                <input
                  type="text"
                  value={guess}
                  onChange={(e) => onChange(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); submit(); } }}
                  onFocus={() => { if (suggestions.length) setShowSug(true); }}
                  onBlur={() => setTimeout(() => setShowSug(false), 150)}
                  placeholder="Quel manga est-ce ?"
                  aria-label="Titre du manga"
                  autoComplete="off"
                  disabled={isGuessing}
                  className="w-full p-4 rounded-2xl bg-black/[0.03] dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold transition-all placeholder:opacity-30 disabled:opacity-50"
                />
                {showSug && suggestions.length > 0 && (
                  <ul className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-[#0f0f1a] rounded-2xl border border-black/10 dark:border-white/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
                    {suggestions.map((tt) => (
                      <li key={tt}>
                        <button
                          type="button"
                          onMouseDown={(e) => { e.preventDefault(); submit(tt); }}
                          className="w-full text-left px-4 py-3 hover:bg-yellow-400/10 font-bold text-sm truncate transition-colors flex items-center gap-2"
                        >
                          <ChevronRight className="w-3.5 h-3.5 opacity-40 shrink-0" /> {tt}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                onClick={() => submit()}
                disabled={!guessValid || isGuessing}
                title={guess.trim() && !guessValid ? 'Choisis un manga de la liste' : undefined}
                className="w-full py-4 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-wide shadow-xl transition-all hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                <Send className="w-5 h-5" /> {isGuessing ? 'VÉRIFICATION…' : 'DEVINER'}
              </button>
              <p className="text-center text-[10px] font-black uppercase tracking-widest opacity-30">
                {maxAttempts - attemptsUsed} essai{maxAttempts - attemptsUsed > 1 ? 's' : ''} restant{maxAttempts - attemptsUsed > 1 ? 's' : ''} · le flou diminue à chaque essai
              </p>
            </div>
          ) : bonusPending ? (
            <div className="p-6 rounded-2xl text-center border-2 bg-green-500/10 border-green-500">
              <p className="font-black text-2xl italic manga-font text-green-500">🎉 Trouvé ! +{baseScore} pts</p>
              <p className="text-lg font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
              <div className="mt-5 pt-5 border-t border-white/10 space-y-3 max-w-xs mx-auto text-left">
                <p className="text-[11px] font-black uppercase tracking-widest text-yellow-500 text-center">Bonus (+30 pts chacun)</p>
                {volumeOn && (
                  <input
                    type="number"
                    value={volumeGuess}
                    onChange={(e) => setVolumeGuess(e.target.value)}
                    placeholder="Numéro de tome"
                    aria-label="Numéro de tome"
                    className="w-full p-3 rounded-xl bg-black/[0.04] dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  />
                )}
                {authorOn && (
                  <input
                    value={authorGuess}
                    onChange={(e) => setAuthorGuess(e.target.value)}
                    placeholder="Mangaka / auteur…"
                    aria-label="Mangaka"
                    className="w-full p-3 rounded-xl bg-black/[0.04] dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  />
                )}
                <button onClick={validateBonus} className="w-full py-3 rounded-xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic">VALIDER LE BONUS</button>
              </div>
            </div>
          ) : (
            <div className={`p-6 rounded-2xl text-center border-2 ${won ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
              <p className={`font-black text-2xl italic manga-font ${won ? 'text-green-500' : 'text-red-500'}`}>
                {won ? `🎉 Trouvé ! +${roundScore} pts` : '😵 Raté !'}
              </p>
              <p className="text-lg font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
              {bonusActive && bonusDone && (
                <div className="mt-2 space-y-1 text-sm font-black uppercase tracking-wide">
                  {volumeOn && <p className={volumeCorrect ? 'text-green-500' : 'text-red-400'}>{volumeCorrect ? 'Bon tome ! +30' : `Tome : n°${gameState.volume}`}</p>}
                  {authorOn && <p className={authorCorrect ? 'text-green-500' : 'text-red-400'}>{authorCorrect ? 'Bon mangaka ! +30' : `Mangaka : ${gameState.author}`}</p>}
                </div>
              )}
              <button
                onClick={() => (isSession ? finishRound() : nextCover())}
                disabled={starting}
                className="mt-6 inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-wide shadow-xl transition-all hover:scale-105 active:scale-95 disabled:opacity-60"
              >
                {isSession
                  ? (<>{lastRound ? 'Voir le résultat' : 'Manche suivante'} <ArrowRight className="w-5 h-5" /></>)
                  : (<><RotateCcw className="w-5 h-5" /> Rejouer</>)}
              </button>
            </div>
          )}

          {/* Journal */}
          <div className="mt-10 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-2">Journal des tentatives</h4>
            {guesses.length === 0 && <p className="text-center py-6 opacity-20 italic text-sm">Aucune tentative pour le moment.</p>}
            {guesses.map((g, i) => (
              <div key={i} className={`flex items-center gap-3 p-3 rounded-2xl border-l-4 ${g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
                {g.image
                  ? <img src={g.image} alt="" className="w-9 h-12 object-cover rounded-lg shrink-0" loading="lazy" />
                  : <span className="w-9 h-12 rounded-lg bg-black/10 dark:bg-white/10 shrink-0" />}
                <span className="font-bold flex-grow truncate">{g.title}</span>
                <span className={`shrink-0 grid place-items-center w-7 h-7 rounded-full ${g.is_correct ? 'bg-green-500' : 'bg-red-500'} text-white`}>
                  {g.is_correct ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default CovertestPage;
