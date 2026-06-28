import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Play, Pause, Check, X, Music, Trophy, ArrowRight } from 'lucide-react';
import { useBlindtestStore } from '../../features/games/stores/blindtestStore';
import { blindtestService } from '../../features/games/services/blindtestService';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

const norm = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

type HintType = 'invert' | 'blur' | 'grayscale' | 'hue' | 'noise';
const HINT_TYPES: HintType[] = ['invert', 'blur', 'grayscale', 'hue', 'noise'];
const SCORE_TIERS = [100, 50, 25, 10, 0];

const pickHint = (): HintType => HINT_TYPES[Math.floor(Math.random() * HINT_TYPES.length)];

// The colour/noise effect stays on at all times (the clip is never shown clean);
// only the blur eases off with each guess so the image "se précise".
const filterFor = (type: HintType, level: number): string => {
  const L = Math.max(0, Math.min(1, level));
  const blur = `blur(${(3 + L * 13).toFixed(1)}px)`;
  switch (type) {
    case 'invert': return `invert(1) ${blur}`;
    case 'grayscale': return `grayscale(1) contrast(1.15) ${blur}`;
    case 'hue': return `hue-rotate(160deg) saturate(2.5) ${blur}`;
    case 'blur': return `blur(${(6 + L * 18).toFixed(1)}px)`;
    case 'noise': return `${blur} brightness(0.9)`;
    default: return blur;
  }
};

const BonusRecap: React.FC<{
  bonusArtistOn: boolean; bonusSeqOn: boolean;
  artistCorrect: boolean; seqCorrect: boolean;
  artists?: string[]; sequence?: number | string; type: 'OP' | 'ED';
}> = ({ bonusArtistOn, bonusSeqOn, artistCorrect, seqCorrect, artists, sequence, type }) => (
  <div className="mt-3 space-y-1 text-sm font-black uppercase tracking-wide">
    {bonusArtistOn && (
      <p className={artistCorrect ? 'text-green-500' : 'text-red-400'}>
        {artistCorrect ? 'Chanteur ✓ +25' : `Chanteur : ${(artists ?? []).join(', ')}`}
      </p>
    )}
    {bonusSeqOn && (
      <p className={seqCorrect ? 'text-green-500' : 'text-red-400'}>
        {seqCorrect ? 'Numéro ✓ +25' : `C'était ${type} n°${sequence}`}
      </p>
    )}
  </div>
);

const BlindtestPage: React.FC = () => {
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useBlindtestStore();
  const location = useLocation();
  const navigate = useNavigate();
  const cfg = location.state as { mode?: 'session' | 'single'; type?: 'OP' | 'ED'; difficulty?: string; length?: number; hints?: boolean; guessArtist?: boolean; guessSequence?: boolean } | null;
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
    blindtestService.getTitles().then((t) => { if (active) setTitles(t); }).catch(() => {});
    return () => { active = false; };
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

  const pick = (title: string) => onSubmit(title);

  const togglePlay = () => {
    const el = mediaRef.current;
    if (!el) return;
    if (el.paused) el.play().catch(() => {});
    else el.pause();
  };

  if (isLoading) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-widest">Récupération de l'audio...</div>;

  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
           <h2 className="text-2xl font-black text-red-500 mb-4 italic">SIGNAL PERDU</h2>
           <p className="mb-8 opacity-60 font-bold">{error}</p>
           <Button variant="danger" onClick={() => restartGame()}>RECONNEXION</Button>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  const currentMode: 'OP' | 'ED' = gameState.theme_type === 'ED' ? 'ED' : 'OP';
  const lost = gameState.gameOver && gameState.won === false;
  const maxAttempts = gameState.maxAttempts ?? 4;
  const used = gameState.guesses.length;
  // Visual hint only after the first guess; round always opens on the vinyl.
  const showVisual = hintsEnabled && !gameState.gameOver && used >= 1;
  const hintSteps = Math.max(1, maxAttempts - 1);
  const hintLevel = used >= 1 ? Math.max(0, 1 - (used - 1) / hintSteps) : 1;
  const correctIdx = gameState.guesses.findIndex((g) => g.is_correct);
  const baseScore = gameState.won && correctIdx >= 0 ? (SCORE_TIERS[correctIdx] ?? 0) : 0;

  // Bonus objectives — only when won and the data is available for this theme.
  const artistAvailable = !!(gameState.artists && gameState.artists.length);
  const sequenceAvailable = gameState.sequence != null && gameState.sequence !== '';
  const bonusArtistOn = guessArtist && artistAvailable;
  const bonusSeqOn = guessSequence && sequenceAvailable;
  const bonusEnabled = !!gameState.won && (bonusArtistOn || bonusSeqOn);
  const bonusPending = bonusEnabled && !bonusDone;
  const bonusScore = (bonusArtistOn && artistCorrect ? 25 : 0) + (bonusSeqOn && seqCorrect ? 25 : 0);
  const roundScore = baseScore + bonusScore;

  const resetBonus = () => {
    setBonusDone(false); setArtistCorrect(false); setSeqCorrect(false);
    setArtistGuess(''); setSeqGuess('');
  };
  const validateBonus = () => {
    if (bonusArtistOn) {
      const g = norm(artistGuess);
      setArtistCorrect(!!g && (gameState.artists ?? []).some((a) => { const n = norm(a); return n.includes(g) || g.includes(n); }));
    }
    if (bonusSeqOn) {
      const want = String(gameState.sequence ?? '').replace(/[^0-9]/g, '');
      const got = seqGuess.replace(/[^0-9]/g, '');
      setSeqCorrect(!!got && got === want);
    }
    setBonusDone(true);
  };

  const replay = () => { resetBonus(); restartGame(currentMode, gameState.difficulty); };

  const finishRound = () => {
    setResults((r) => [...r, { score: roundScore, won: !!gameState.won, secret: gameState.secret_title }]);
    setTotalScore((t) => t + roundScore);
    if (round >= sessionLength) {
      setSessionOver(true);
    } else {
      setRound((r) => r + 1);
      setHintType(pickHint());
      resetBonus();
      restartGame(launchType ?? currentMode, launchDifficulty ?? gameState.difficulty);
    }
  };

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
                className={`h-8 rounded-md grid place-items-center text-[10px] font-black ${
                  r.won ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-red-500/15 text-red-500'
                }`}
              >
                {r.score}
              </div>
            ))}
          </div>

          <div className="flex gap-3 justify-center mt-10">
            <Button variant="primary" onClick={() => navigate('/blindtest/')}>NOUVELLE SESSION</Button>
          </div>
        </Card>
      </div>
    );
  }

  const isSession = mode === 'session';
  const lastRound = round >= sessionLength;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      {/* Session progress */}
      {isSession && (
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-black uppercase tracking-widest text-gray-500 dark:text-gray-400">
              Manche {round} / {sessionLength}
            </span>
            <span className="text-xs font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
              {totalScore} pts
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-black/10 dark:bg-white/10 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 transition-all" style={{ width: `${((round - 1) / sessionLength) * 100}%` }} />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* LECTEUR */}
        <Card padding="md">
          {gameState.gameOver ? (
            <video src={gameState.video_url} controls className="w-full rounded-3xl shadow-lg" aria-label="Lecteur vidéo de l'extrait">
              <track kind="captions" />
            </video>
          ) : (
            <div className="flex flex-col items-center py-8">
              {/* Current format */}
              <div className="mb-8">
                <span className="px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[11px] font-black uppercase tracking-widest">
                  {currentMode === 'OP' ? 'Opening' : 'Ending'}
                </span>
              </div>

              {hintsEnabled ? (
                /* One persistent media element (audio stays continuous). The vinyl
                   covers it until the first guess; afterwards the clip is revealed
                   distorted — colour effect always on, blur easing each guess. */
                <div
                  className="relative w-full max-w-lg rounded-3xl overflow-hidden shadow-2xl bg-[#0d0d12]"
                  style={{ aspectRatio: String(aspect) }}
                >
                  <video
                    ref={mediaRef}
                    src={gameState.video_url}
                    className={`w-full h-full object-cover transition-all duration-500 ${showVisual ? 'opacity-100' : 'opacity-0'}`}
                    style={{ filter: showVisual ? filterFor(hintType, hintLevel) : 'none' }}
                    preload="auto"
                    aria-label="Indice visuel du générique"
                    onLoadedMetadata={(e) => {
                      const el = e.currentTarget;
                      if (el.videoWidth && el.videoHeight) setAspect(el.videoWidth / el.videoHeight);
                    }}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onEnded={() => setIsPlaying(false)}
                    onEmptied={() => setIsPlaying(false)}
                  >
                    <track kind="captions" />
                  </video>

                  {showVisual && hintType === 'noise' && (
                    <div
                      className="absolute inset-0 mix-blend-overlay pointer-events-none"
                      style={{ backgroundImage: "url('/static/img/noise.png')", opacity: 0.4 + hintLevel * 0.5 }}
                    />
                  )}

                  {!showVisual && (
                    <div className="absolute inset-0 grid place-items-center">
                      <div
                        className={`relative w-44 h-44 rounded-full grid place-items-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] ${isPlaying ? 'motion-safe:animate-[spin_4s_linear_infinite]' : ''}`}
                        style={{ background: 'repeating-radial-gradient(circle at center, #0d0d12 0 3px, #1b1b24 3px 6px)' }}
                      >
                        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/5 to-white/15" />
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-300 to-orange-500 grid place-items-center border-4 border-black/40 shadow-inner">
                          <Music className="w-6 h-6 text-black/80" />
                        </div>
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-[#0f0f1a] border border-white/20" />
                      </div>
                    </div>
                  )}

                  <button
                    onClick={togglePlay}
                    aria-label={isPlaying ? 'Mettre en pause' : 'Lancer la lecture'}
                    className="absolute inset-0 grid place-items-center group outline-none"
                  >
                    <span className="bg-black/60 backdrop-blur-sm text-white p-4 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      {isPlaying ? <Pause className="w-7 h-7" /> : <Play className="w-7 h-7 fill-current" />}
                    </span>
                  </button>
                </div>
              ) : (
                /* Vinyl disc — audio only (hints disabled) */
                <button onClick={togglePlay} aria-label={isPlaying ? 'Mettre en pause' : 'Lancer la lecture'} className="group relative outline-none">
                  <div
                    className={`relative w-60 h-60 rounded-full grid place-items-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] ${isPlaying ? 'motion-safe:animate-[spin_4s_linear_infinite]' : ''}`}
                    style={{ background: 'repeating-radial-gradient(circle at center, #0d0d12 0 3px, #1b1b24 3px 6px)' }}
                  >
                    <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/5 to-white/15 pointer-events-none" />
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-300 to-orange-500 grid place-items-center border-4 border-black/40 shadow-inner">
                      <Music className="w-9 h-9 text-black/80" />
                    </div>
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-[#0f0f1a] border border-white/20" />
                  </div>
                  <span className="absolute inset-0 grid place-items-center pointer-events-none">
                    <span className="bg-black/60 backdrop-blur-sm text-white p-5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8 fill-current" />}
                    </span>
                  </span>
                  <video
                    ref={mediaRef}
                    src={gameState.video_url}
                    className="hidden"
                    preload="auto"
                    aria-label="Extrait audio du blind test"
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onEnded={() => setIsPlaying(false)}
                    onEmptied={() => setIsPlaying(false)}
                  >
                    <track kind="captions" />
                  </video>
                </button>
              )}

              <p className="mt-8 font-bold text-gray-500 uppercase tracking-widest text-xs">
                {isPlaying ? 'Lecture en cours…' : hintsEnabled ? 'Clique pour écouter — le visuel se précise à chaque essai' : 'Cliquez sur le disque pour écouter'}
              </p>
              {typeof gameState.attemptsLeft === 'number' && (
                <p className="mt-2 text-[11px] font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
                  {gameState.attemptsLeft} tentative{gameState.attemptsLeft > 1 ? 's' : ''} restante{gameState.attemptsLeft > 1 ? 's' : ''}
                </p>
              )}
            </div>
          )}
        </Card>

        {/* JEU */}
        <Card padding="lg">
          <h2 className="text-3xl font-black mb-8 flex items-center gap-3 italic">
              <Music className="w-8 h-8 text-yellow-400" /> DÉCOUVREZ L'ANIMÉ
          </h2>
          {!gameState.gameOver ? (
            <div className="space-y-6">
              <div className="relative">
                <input
                  type="text"
                  value={guess}
                  onChange={(e) => onGuessChange(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && guess.trim()) { setShowSug(false); onSubmit(); } }}
                  onFocus={() => { if (suggestions.length) setShowSug(true); }}
                  onBlur={() => setTimeout(() => setShowSug(false), 150)}
                  className="w-full p-4 rounded-2xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  placeholder="Titre de l'animé..."
                  aria-label="Titre de l'animé"
                  autoComplete="off"
                />
                {showSug && suggestions.length > 0 && (
                  <ul className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-[#0f0f1a] rounded-2xl border border-gray-100 dark:border-white/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
                    {suggestions.map((tt) => (
                      <li key={tt}>
                        <button
                          type="button"
                          onMouseDown={(e) => { e.preventDefault(); pick(tt); }}
                          className="w-full text-left px-4 py-3 hover:bg-yellow-400/10 font-bold text-sm text-black dark:text-white truncate transition-colors"
                        >
                          {tt}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <Button variant="primary" fullWidth onClick={() => onSubmit()}>
                VALIDER MA RÉPONSE
              </Button>
            </div>
          ) : bonusPending ? (
            <div className="p-6 rounded-2xl text-center border-2 bg-green-500/10 border-green-500">
              <p className="font-black text-2xl text-green-500">🎉 Trouvé ! +{baseScore} pts</p>
              <p className="text-lg font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
              <div className="mt-5 pt-5 border-t border-white/10 space-y-3 text-left max-w-sm mx-auto">
                <p className="text-[11px] font-black uppercase tracking-widest text-yellow-500 text-center">Bonus (+25 pts chacun)</p>
                {bonusArtistOn && (
                  <input
                    value={artistGuess}
                    onChange={(e) => setArtistGuess(e.target.value)}
                    placeholder="Chanteur / interprète…"
                    aria-label="Chanteur"
                    className="w-full p-3 rounded-xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  />
                )}
                {bonusSeqOn && (
                  <input
                    type="number"
                    value={seqGuess}
                    onChange={(e) => setSeqGuess(e.target.value)}
                    placeholder={`Numéro d'${currentMode === 'ED' ? 'ending' : 'opening'} (ex: 1)`}
                    aria-label="Numéro d'opening"
                    className="w-full p-3 rounded-xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  />
                )}
                <Button variant="primary" fullWidth onClick={validateBonus}>VALIDER LE BONUS</Button>
              </div>
            </div>
          ) : isSession ? (
            <div className={`p-6 rounded-2xl text-center border-2 ${gameState.won ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
              <p className={`font-black text-2xl ${gameState.won ? 'text-green-500' : 'text-red-500'}`}>
                {gameState.won ? `🎉 +${roundScore} pts` : '😵 Manche perdue'}
              </p>
              <p className="text-lg font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
              {bonusEnabled && bonusDone && <BonusRecap {...{ bonusArtistOn, bonusSeqOn, artistCorrect, seqCorrect, artists: gameState.artists, sequence: gameState.sequence, type: currentMode }} />}
              <Button variant="primary" className="mt-6" onClick={finishRound}>
                {lastRound ? 'VOIR LE RÉSULTAT' : 'MANCHE SUIVANTE'} <ArrowRight className="w-5 h-5" />
              </Button>
            </div>
          ) : lost ? (
            <div className="bg-red-500/10 border-2 border-red-500 p-6 rounded-2xl text-center">
                <p className="text-red-500 font-black text-2xl">😵 PERDU !</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                <Button variant="danger" className="mt-6" onClick={replay}>REJOUER</Button>
            </div>
          ) : (
            <div className="bg-green-500/10 border-2 border-green-500 p-6 rounded-2xl text-center">
                <p className="text-green-500 font-black text-2xl animate-bounce">🎉 BIEN JOUÉ !{bonusScore > 0 ? ` +${bonusScore} bonus` : ''}</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                {bonusEnabled && bonusDone && <BonusRecap {...{ bonusArtistOn, bonusSeqOn, artistCorrect, seqCorrect, artists: gameState.artists, sequence: gameState.sequence, type: currentMode }} />}
                <Button variant="success" className="mt-6" onClick={replay}>REJOUER</Button>
            </div>
          )}

          <div className="mt-10 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-widest">Tentatives précédentes</h4>
            {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-gray-100 dark:border-white/5">
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? <Check className="text-green-500 w-5 h-5" /> : <X className="text-red-500 w-5 h-5" />}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default BlindtestPage;
