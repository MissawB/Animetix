import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Play, Pause, Check, X, Music, SlidersHorizontal } from 'lucide-react';
import { useBlindtestStore } from '../../features/games/stores/blindtestStore';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

const BlindtestPage: React.FC = () => {
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useBlindtestStore();
  const location = useLocation();
  const launchState = location.state as { type?: 'OP' | 'ED'; difficulty?: string } | null;
  const launchType = launchState?.type;
  const launchDifficulty = launchState?.difficulty;
  const [guess, setGuess] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState(false);
  const mediaRef = useRef<HTMLVideoElement>(null);

  // Start the format/difficulty chosen on the config page; otherwise resume / auto-start.
  useEffect(() => {
    if (launchType) restartGame(launchType, launchDifficulty);
    else loadGame();
  }, [launchType, launchDifficulty, loadGame, restartGame]);

  const onSubmit = async () => {
    submitGuess(guess);
    setGuess('');
  };

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
  const replay = () => restartGame(currentMode, gameState.difficulty);

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* LECTEUR */}
        <Card padding="md">
          {gameState.gameOver ? (
            <video src={gameState.video_url} controls className="w-full rounded-3xl shadow-lg" aria-label="Lecteur vidéo de l'extrait">
              <track kind="captions" />
            </video>
          ) : (
            <div className="flex flex-col items-center py-8">
              {/* Current format + back to config */}
              <div className="flex items-center gap-3 mb-10">
                <span className="px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[11px] font-black uppercase tracking-widest">
                  {currentMode === 'OP' ? 'Opening' : 'Ending'}
                </span>
                <Link
                  to="/blindtest/"
                  className="inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-widest text-gray-500 hover:text-black dark:hover:text-white no-underline transition-colors"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" /> Changer
                </Link>
              </div>

              {/* Spinning vinyl */}
              <button onClick={togglePlay} aria-label={isPlaying ? 'Mettre en pause' : 'Lancer la lecture'} className="group relative outline-none">
                <div
                  className={`relative w-60 h-60 rounded-full grid place-items-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] ${
                    isPlaying ? 'motion-safe:animate-[spin_4s_linear_infinite]' : ''
                  }`}
                  style={{
                    background:
                      'repeating-radial-gradient(circle at center, #0d0d12 0 3px, #1b1b24 3px 6px)',
                  }}
                >
                  {/* light sheen */}
                  <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/5 to-white/15 pointer-events-none" />
                  {/* center label */}
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-300 to-orange-500 grid place-items-center border-4 border-black/40 shadow-inner">
                    <Music className="w-9 h-9 text-black/80" />
                  </div>
                  {/* spindle hole */}
                  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-[#0f0f1a] border border-white/20" />
                </div>
                {/* play / pause overlay */}
                <span className="absolute inset-0 grid place-items-center pointer-events-none">
                  <span className="bg-black/60 backdrop-blur-sm text-white p-5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8 fill-current" />}
                  </span>
                </span>
              </button>

              <p className="mt-8 font-bold text-gray-500 uppercase tracking-widest text-xs">
                {isPlaying ? 'Lecture en cours…' : "Cliquez sur le disque pour écouter"}
              </p>
              {typeof gameState.attemptsLeft === 'number' && (
                <p className="mt-2 text-[11px] font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
                  {gameState.attemptsLeft} tentative{gameState.attemptsLeft > 1 ? 's' : ''} restante{gameState.attemptsLeft > 1 ? 's' : ''}
                </p>
              )}

              {/* Audio source — the video stays hidden so the anime isn't revealed. */}
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
              <input
                type="text"
                value={guess}
                onChange={(e) => setGuess(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && guess.trim()) onSubmit(); }}
                className="w-full p-4 rounded-2xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                placeholder="Titre de l'animé..."
                aria-label="Titre de l'animé"
              />
              <Button variant="primary" fullWidth onClick={onSubmit}>
                VALIDER MA RÉPONSE
              </Button>
            </div>
          ) : lost ? (
            <div className="bg-red-500/10 border-2 border-red-500 p-6 rounded-2xl text-center">
                <p className="text-red-500 font-black text-2xl">😵 PERDU !</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                <Button variant="danger" className="mt-6" onClick={replay}>
                    REJOUER
                </Button>
            </div>
          ) : (
            <div className="bg-green-500/10 border-2 border-green-500 p-6 rounded-2xl text-center">
                <p className="text-green-500 font-black text-2xl animate-bounce">🎉 BIEN JOUÉ !</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                <Button variant="success" className="mt-6" onClick={replay}>
                    REJOUER
                </Button>
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
