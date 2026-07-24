import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { RotateCcw, ArrowRight, ImageIcon, Loader2 } from 'lucide-react';
import { useCovertest } from '../../features/games/hooks/useCovertest';
import {
  covertestService,
  type CovertestTitle,
} from '../../features/games/services/covertestService';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { normalizeText as norm } from '../../utils/normalizeText';
import { pickFxCombo, fxFilter, type FxCombo } from '../../features/games/utils/covertestFx';
import { CovertestSessionSummary } from './components/CovertestSessionSummary';
import { CovertestAttemptsLog } from './components/CovertestAttemptsLog';
import { CovertestGuessInput } from './components/CovertestGuessInput';

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';
const SHU_CTA =
  'inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-7 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';

const MAX_ATTEMPTS: Record<string, number> = {
  Easy: 6,
  Normal: 4,
  Hard: 3,
  Impossible: 2,
  Tryhard: 3,
};

const CovertestPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, loading, handleGuess, isGuessing, startGame, revealAnswer } = useCovertest();
  const location = useLocation();
  const navigate = useNavigate();
  const cfg = location.state as {
    mode?: 'session' | 'single';
    difficulty?: string;
    length?: number;
    guessVolume?: boolean;
    guessAuthor?: boolean;
    origin?: string;
  } | null;
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
  const [titles, setTitles] = useState<CovertestTitle[]>([]);
  const [suggestions, setSuggestions] = useState<{ title: string; via?: string }[]>([]);
  const [showSug, setShowSug] = useState(false);
  const [loadedUrl, setLoadedUrl] = useState<string | null>(null);
  const [volumeGuess, setVolumeGuess] = useState('');
  const [authorGuess, setAuthorGuess] = useState('');
  const [bonusDone, setBonusDone] = useState(false);
  const [volumeCorrect, setVolumeCorrect] = useState(false);
  const [authorCorrect, setAuthorCorrect] = useState(false);
  const [fxCombo, setFxCombo] = useState<FxCombo>(() => pickFxCombo());
  const [advancing, setAdvancing] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    startGame({ origin })
      .catch(() => {})
      .finally(() => setInitializing(false));
  }, [startGame, origin]);

  useEffect(() => {
    let active = true;
    covertestService
      .getTitles()
      .then((t) => {
        if (active) setTitles(t);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const guesses = gameState?.guesses ?? [];
  const attemptsUsed = guesses.length;
  const won = guesses.some((g) => g.is_correct);
  const over = !!gameState?.game_over;
  const outOfTries = attemptsUsed >= maxAttempts;
  const coverLoaded = !!gameState?.cover_url && loadedUrl === gameState.cover_url;

  useEffect(() => {
    if (gameState && !over && !won && outOfTries) {
      revealAnswer().catch(() => {});
    }
  }, [gameState, over, won, outOfTries, revealAnswer]);

  const winningIdx = guesses.findIndex((g) => g.is_correct);
  const baseScore =
    won && winningIdx >= 0 ? Math.max(5, Math.round(100 * (1 - winningIdx / maxAttempts))) : 0;
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
  const nextCover = async () => {
    resetBonus();
    setFxCombo(pickFxCombo());
    await startGame({ origin }).catch(() => {});
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
      setAuthorCorrect(
        !!g && g.length >= 2 && (want.includes(g) || g.includes(want.split(',')[0].trim())),
      );
    }
    setBonusDone(true);
  };

  const blurPx = over ? 0 : Math.round(4 + Math.max(0, 1 - attemptsUsed / maxAttempts) * 20);
  const fxLevel = over ? 0 : Math.max(0, 1 - attemptsUsed / maxAttempts);
  const coverFilter = tryhard ? fxFilter(fxCombo, fxLevel, blurPx) : `blur(${blurPx}px)`;

  const onChange = (val: string) => {
    setGuess(val);
    const q = norm(val.trim());
    if (q.length < 2) {
      setSuggestions([]);
      setShowSug(false);
      return;
    }
    const starts: { title: string; via?: string }[] = [];
    const incl: { title: string; via?: string }[] = [];
    for (const t of titles) {
      if (norm(t.title).startsWith(q)) {
        starts.push({ title: t.title });
        continue;
      }
      const aliasStart = t.aliases.find((a) => norm(a).startsWith(q));
      if (aliasStart) {
        starts.push({ title: t.title, via: aliasStart });
        continue;
      }
      if (norm(t.title).includes(q)) {
        incl.push({ title: t.title });
        continue;
      }
      const aliasIncl = t.aliases.find((a) => norm(a).includes(q));
      if (aliasIncl) incl.push({ title: t.title, via: aliasIncl });
    }
    const sug = [...starts, ...incl].slice(0, 8);
    setSuggestions(sug);
    setShowSug(sug.length > 0);
  };

  const titleByNorm = useMemo(() => {
    const m = new Map<string, string>();
    for (const t of titles) m.set(norm(t.title), t.title);
    for (const t of titles)
      for (const a of t.aliases) {
        const k = norm(a);
        if (!m.has(k)) m.set(k, t.title);
      }
    return m;
  }, [titles]);
  const guessValid = titleByNorm.has(norm(guess.trim())) || suggestions.length > 0;

  const submit = async (value?: string) => {
    const raw = (value ?? guess).trim();
    if (!raw || isGuessing || over) return;
    const canonical = titleByNorm.get(norm(raw)) ?? suggestions[0]?.title;
    if (!canonical) return;
    setShowSug(false);
    setGuess('');
    setSuggestions([]);
    try {
      await handleGuess({ guess: canonical });
    } catch {
      /* toast already shown */
    }
  };

  const finishRound = async () => {
    setResults((r) => [...r, { score: roundScore, won, secret: gameState?.secret_title }]);
    setTotalScore((t) => t + roundScore);
    if (mode === 'session' && round < sessionLength) {
      setRound((r) => r + 1);
      await nextCover();
    } else if (mode === 'session') {
      setSessionOver(true);
    } else {
      await nextCover();
    }
  };

  const advance = async () => {
    if (advancing) return;
    setAdvancing(true);
    try {
      await (mode === 'session' ? finishRound() : nextCover());
    } finally {
      setAdvancing(false);
    }
  };

  if (initializing || (loading && !gameState)) {
    return (
      <div className="min-h-screen bg-[#0B0C10]">
        <div className="max-w-3xl mx-auto px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (sessionOver) {
    return (
      <CovertestSessionSummary
        sessionLength={sessionLength}
        results={results}
        totalScore={totalScore}
        onNewSession={() => navigate('/covertest/')}
      />
    );
  }

  if (!gameState) return null;

  const isSession = mode === 'session';
  const lastRound = round >= sessionLength;

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-6xl mx-auto px-6 py-12">
        {isSession && (
          <div className="mb-8 flex items-center justify-between gap-4">
            <span className="text-[11px] font-black uppercase tracking-widest text-[#8F94A5]">
              {t('games.covertest.round_progress', {
                defaultValue: 'Manche {{round}}/{{total}}',
                round,
                total: sessionLength,
              })}
            </span>
            <div className="flex-1 h-2 rounded-full bg-[#F4F1E8]/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-[#FDB913] transition-all duration-500"
                style={{ width: `${((round - 1) / sessionLength) * 100}%` }}
              />
            </div>
            <span className="text-[11px] font-black uppercase tracking-widest text-[#FDB913]">
              {t('games.covertest.points_abbr', {
                defaultValue: '{{points}} pts',
                points: totalScore,
              })}
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Cover */}
          <div className="relative group">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl aspect-[2/3] bg-[#0F1016] border border-[#F4F1E8]/10">
              {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
              <img
                key={gameState.cover_url}
                src={gameState.cover_url}
                alt={t('games.covertest.cover_alt', 'Couverture mystère')}
                onLoad={() => setLoadedUrl(gameState.cover_url)}
                className={`w-full h-full object-cover transition-all duration-700 ${coverLoaded ? 'opacity-100' : 'opacity-0'}`}
                style={{ filter: coverFilter, transform: over ? 'scale(1.03)' : 'scale(1.08)' }}
                decoding="async"
              />
              {!coverLoaded && (
                <div className="absolute inset-0 grid place-items-center">
                  <Loader2 className="w-10 h-10 text-[#F4F1E8]/40 animate-spin" />
                </div>
              )}
              {!over && coverLoaded && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="bg-[#0B0C10]/60 backdrop-blur-md px-5 py-3 rounded-full border border-[#F4F1E8]/15 flex items-center gap-2 text-[#F4F1E8]/80">
                    <ImageIcon className="w-5 h-5" />
                    <span className="text-xs font-black uppercase tracking-widest">
                      {t('games.covertest.blurred_cover', 'Couverture floutée')}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Game */}
          <div className={`${PANEL} p-8 md:p-10`}>
            <h2 className="font-manga text-4xl font-black italic uppercase mb-2 tracking-tighter flex items-center gap-3 text-[#F4F1E8]">
              <span className="explore-stamp -rotate-2" aria-hidden>
                隠
              </span>
              COVER <span className="text-[#E8442B]">QUEST</span>
            </h2>

            <div className="flex items-center gap-2 mb-8">
              {Array.from({ length: maxAttempts }).map((_, i) => (
                <span
                  key={i}
                  className={`h-2 flex-1 rounded-full transition-colors ${
                    i < attemptsUsed
                      ? won && i === winningIdx
                        ? 'bg-[#FDB913]'
                        : 'bg-[#E8442B]/70'
                      : 'bg-[#F4F1E8]/10'
                  }`}
                />
              ))}
            </div>

            {!over ? (
              <CovertestGuessInput
                guess={guess}
                onChange={onChange}
                submit={submit}
                suggestions={suggestions}
                showSug={showSug}
                setShowSug={setShowSug}
                guessValid={guessValid}
                isGuessing={isGuessing}
                maxAttempts={maxAttempts}
                attemptsUsed={attemptsUsed}
              />
            ) : bonusPending ? (
              <div className="p-6 rounded-2xl text-center border-2 bg-[#FDB913]/[0.06] border-[#FDB913]/40">
                <p className="font-manga font-black text-2xl italic text-[#FDB913]">
                  {t('games.covertest.found_points', {
                    defaultValue: '🎉 Trouvé ! +{{points}} pts',
                    points: baseScore,
                  })}
                </p>
                <p className="text-lg font-bold mt-2 text-[#F4F1E8]">
                  {t('games.covertest.it_was', "C'était :")}{' '}
                  <span className="text-[#FDB913]">{gameState.secret_title}</span>
                </p>
                <div className="mt-5 pt-5 border-t border-[#F4F1E8]/10 space-y-3 max-w-xs mx-auto text-left">
                  <p className="text-[11px] font-black uppercase tracking-widest text-[#FDB913] text-center">
                    {t('games.covertest.bonus_header', 'Bonus (+30 pts chacun)')}
                  </p>
                  {volumeOn && (
                    <input
                      type="number"
                      value={volumeGuess}
                      onChange={(e) => setVolumeGuess(e.target.value)}
                      placeholder={t('games.covertest.volume_placeholder', 'Numéro de tome')}
                      aria-label={t('games.covertest.volume_placeholder', 'Numéro de tome')}
                      className="w-full p-3 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60"
                    />
                  )}
                  {authorOn && (
                    <input
                      value={authorGuess}
                      onChange={(e) => setAuthorGuess(e.target.value)}
                      placeholder={t('games.covertest.author_placeholder', 'Mangaka / auteur…')}
                      aria-label={t('games.covertest.author_aria', 'Mangaka')}
                      className="w-full p-3 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60"
                    />
                  )}
                  <button onClick={validateBonus} className={`${SHU_CTA} w-full`}>
                    {t('games.covertest.validate_bonus', 'VALIDER LE BONUS')}
                  </button>
                </div>
              </div>
            ) : (
              <div
                className={`p-6 rounded-2xl text-center border-2 ${won ? 'bg-[#FDB913]/[0.06] border-[#FDB913]/40' : 'bg-[#E8442B]/[0.06] border-[#E8442B]/40'}`}
              >
                <p
                  className={`font-manga font-black text-2xl italic ${won ? 'text-[#FDB913]' : 'text-[#E8442B]'}`}
                >
                  {won
                    ? t('games.covertest.found_points', {
                        defaultValue: '🎉 Trouvé ! +{{points}} pts',
                        points: roundScore,
                      })
                    : t('games.covertest.missed', '😵 Raté !')}
                </p>
                <p className="text-lg font-bold mt-2 text-[#F4F1E8]">
                  {t('games.covertest.it_was', "C'était :")}{' '}
                  <span className="text-[#FDB913]">{gameState.secret_title}</span>
                </p>
                {bonusActive && bonusDone && (
                  <div className="mt-2 space-y-1 text-sm font-black uppercase tracking-wide">
                    {volumeOn && (
                      <p className={volumeCorrect ? 'text-[#FDB913]' : 'text-[#E8442B]'}>
                        {volumeCorrect
                          ? t('games.covertest.volume_correct', 'Bon tome ! +30')
                          : t('games.covertest.volume_answer', {
                              defaultValue: 'Tome : n°{{volume}}',
                              volume: gameState.volume,
                            })}
                      </p>
                    )}
                    {authorOn && (
                      <p className={authorCorrect ? 'text-[#FDB913]' : 'text-[#E8442B]'}>
                        {authorCorrect
                          ? t('games.covertest.author_correct', 'Bon mangaka ! +30')
                          : t('games.covertest.author_answer', {
                              defaultValue: 'Mangaka : {{author}}',
                              author: gameState.author,
                            })}
                      </p>
                    )}
                  </div>
                )}
                <button onClick={advance} disabled={advancing} className={`${SHU_CTA} mt-6`}>
                  {isSession ? (
                    <>
                      {lastRound
                        ? t('games.covertest.see_result', 'Voir le résultat')
                        : t('games.covertest.next_round', 'Manche suivante')}{' '}
                      <ArrowRight className="w-5 h-5" />
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-5 h-5" /> {t('games.covertest.replay', 'Rejouer')}
                    </>
                  )}
                </button>
              </div>
            )}

            <CovertestAttemptsLog guesses={guesses} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default CovertestPage;
