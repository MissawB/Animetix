import { useState, useEffect, useCallback } from 'react';
import { startClassicGame, getClassicGameState, guessClassicGame, revealClassicGame } from '../api';
import { SearchBar } from './SearchBar';
import { Trophy, Swords, RotateCcw, Eye, ChevronRight, Zap, Star, AlertCircle } from 'lucide-react';

const DIFFICULTY_OPTIONS = [
  { id: 'easy', label: 'Facile', color: 'text-anime-success', description: '15 tentatives' },
  { id: 'normal', label: 'Normal', color: 'text-anime-gold', description: '10 tentatives' },
  { id: 'hard', label: 'Difficile', color: 'text-anime-error', description: '5 tentatives' },
];

const MEDIA_OPTIONS = [
  { id: 'anime', label: '🎌 Anime' },
  { id: 'manga', label: '📚 Manga' },
  { id: 'game', label: '🎮 Jeu Vidéo' },
];

function AttemptRow({ attempt, index }) {
  const statusClass = {
    correct: 'badge-correct',
    wrong: 'badge-wrong',
    partial: 'badge-partial',
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-anime-border/50 animate-slide-up">
      <span className="text-black/30 dark:text-anime-light-text dark:text-anime-dark-text/30 text-xs w-5 text-right">{index + 1}.</span>
      <span className="flex-1 text-sm text-black/80 dark:text-anime-light-text dark:text-anime-dark-text/80 font-medium">{attempt.guess}</span>
      <div className="flex flex-wrap gap-1.5">
        {attempt.result?.hints?.map((hint, i) => (
          <span key={i} className={`badge ${statusClass[hint.status] || 'badge bg-white/10 text-black/60 dark:text-anime-light-text dark:text-anime-dark-text/60'}`}>
            {hint.attribute}: {hint.value}
          </span>
        ))}
        {attempt.result?.is_correct && (
          <span className="badge badge-correct">
            <Trophy className="w-3 h-3" /> Correct !
          </span>
        )}
      </div>
    </div>
  );
}

function StartScreen({ onStart }) {
  const [mediaType, setMediaType] = useState('anime');
  const [difficulty, setDifficulty] = useState('normal');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await onStart(mediaType, difficulty);
    } catch (e) {
      setError("Impossible de démarrer la partie. Vérifiez que le serveur Django est lancé.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-8 animate-slide-up">
      <div className="text-center">
        <div className="text-5xl mb-3">🎌</div>
        <h2 className="text-2xl font-bold text-anime-light-text dark:text-anime-dark-text mb-2">Mode Classic</h2>
        <p className="text-black/50 dark:text-anime-light-text dark:text-anime-dark-text/50 text-sm max-w-sm">
          Devinez le titre mystère en soumettant des propositions. 
          Les indices vous guident pas à pas.
        </p>
      </div>

      <div className="glass-card p-6 w-full max-w-md space-y-6">
        {/* Media Type Selection */}
        <div>
          <label className="text-xs font-semibold text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider mb-3 block">
            Catégorie
          </label>
          <div className="grid grid-cols-3 gap-2">
            {MEDIA_OPTIONS.map(opt => (
              <button
                key={opt.id}
                id={`media-${opt.id}`}
                onClick={() => setMediaType(opt.id)}
                className={`py-2.5 px-3 rounded-xl text-sm font-medium border transition-all duration-200 ${
                  mediaType === opt.id
                    ? 'border-anime-purple bg-anime-purple/20 text-anime-light-text dark:text-anime-dark-text'
                    : 'border-anime-border bg-transparent text-black/50 dark:text-anime-light-text dark:text-anime-dark-text/50 hover:border-anime-border/80 hover:text-anime-light-text dark:text-anime-dark-text/70'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Difficulty Selection */}
        <div>
          <label className="text-xs font-semibold text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider mb-3 block">
            Difficulté
          </label>
          <div className="space-y-2">
            {DIFFICULTY_OPTIONS.map(opt => (
              <button
                key={opt.id}
                id={`difficulty-${opt.id}`}
                onClick={() => setDifficulty(opt.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all duration-200 ${
                  difficulty === opt.id
                    ? 'border-anime-purple bg-anime-purple/20'
                    : 'border-anime-border bg-transparent hover:border-anime-border/80'
                }`}
              >
                <span className={`font-medium ${opt.color}`}>{opt.label}</span>
                <span className="text-xs text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40">{opt.description}</span>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-anime-error text-sm bg-anime-error/10 border border-anime-error/20 rounded-xl p-3">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <button
          id="start-game-btn"
          onClick={handleStart}
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center gap-2 animate-pulse-glow"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Chargement...
            </>
          ) : (
            <>
              <Swords className="w-5 h-5" />
              Démarrer la partie
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export function ClassicGame() {
  const [phase, setPhase] = useState('start'); // start | playing | won | lost
  const [sessionId, setSessionId] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [isGuessing, setIsGuessing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGuess, setSelectedGuess] = useState(null);
  const [revealedAnswer, setRevealedAnswer] = useState(null);

  const handleStart = useCallback(async (mediaType, difficulty) => {
    const data = await startClassicGame(mediaType, difficulty);
    setSessionId(data.session_id);
    setGameState(data);
    setAttempts([]);
    setPhase('playing');
    setError(null);
  }, []);

  const handleGuess = useCallback(async () => {
    if (!selectedGuess || isGuessing) return;
    setIsGuessing(true);
    setError(null);
    try {
      const data = await guessClassicGame(sessionId, selectedGuess.title || selectedGuess.name);
      const newAttempt = {
        guess: selectedGuess.title || selectedGuess.name,
        result: data,
      };
      setAttempts(prev => [...prev, newAttempt]);
      setSelectedGuess(null);
      setGameState(data.game_state || data);

      if (data.is_correct || data.won) {
        setPhase('won');
      } else if (data.game_over || data.lost) {
        setPhase('lost');
      }
    } catch (e) {
      setError("Erreur lors de la soumission. Réessayez.");
    } finally {
      setIsGuessing(false);
    }
  }, [selectedGuess, sessionId, isGuessing]);

  const handleReveal = useCallback(async () => {
    try {
      const data = await revealClassicGame(sessionId);
      setRevealedAnswer(data.answer || data.title);
      setPhase('lost');
    } catch {
      setError("Impossible de révéler la réponse.");
    }
  }, [sessionId]);

  const handleRestart = () => {
    setPhase('start');
    setSessionId(null);
    setGameState(null);
    setAttempts([]);
    setError(null);
    setSelectedGuess(null);
    setRevealedAnswer(null);
  };

  const maxAttempts = gameState?.max_attempts || 10;
  const attemptsLeft = maxAttempts - attempts.length;

  if (phase === 'start') {
    return <StartScreen onStart={handleStart} />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header Stats */}
      <div className="glass-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <p className="text-xs text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider">Essais</p>
            <p className="text-2xl font-bold text-anime-light-text dark:text-anime-dark-text">{attempts.length}<span className="text-black/30 dark:text-anime-light-text dark:text-anime-dark-text/30 text-base">/{maxAttempts}</span></p>
          </div>
          <div className="w-px h-10 bg-anime-border" />
          <div className="text-center">
            <p className="text-xs text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider">Restants</p>
            <p className={`text-2xl font-bold ${attemptsLeft <= 2 ? 'text-anime-error' : attemptsLeft <= 4 ? 'text-anime-gold' : 'text-anime-success'}`}>
              {attemptsLeft}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {phase === 'playing' && (
            <button
              id="reveal-btn"
              onClick={handleReveal}
              className="btn-secondary flex items-center gap-1.5 text-sm"
            >
              <Eye className="w-4 h-4" />
              Révéler
            </button>
          )}
          <button
            id="restart-btn"
            onClick={handleRestart}
            className="btn-secondary flex items-center gap-1.5 text-sm"
          >
            <RotateCcw className="w-4 h-4" />
            Nouvelle partie
          </button>
        </div>
      </div>

      {/* Win / Loss Banner */}
      {phase === 'won' && (
        <div className="glass-card p-5 border-anime-success/40 bg-anime-success/10 text-center animate-slide-up">
          <div className="text-4xl mb-2">🏆</div>
          <p className="text-anime-success font-bold text-xl">Félicitations !</p>
          <p className="text-black/60 dark:text-anime-light-text dark:text-anime-dark-text/60 text-sm mt-1">
            Trouvé en {attempts.length} essai{attempts.length > 1 ? 's' : ''} !
          </p>
          <div className="flex justify-center gap-1 mt-2">
            {[...Array(Math.max(0, 5 - Math.floor(attempts.length / 2)))].map((_, i) => (
              <Star key={i} className="w-5 h-5 text-anime-gold fill-anime-gold" />
            ))}
          </div>
        </div>
      )}

      {phase === 'lost' && (
        <div className="glass-card p-5 border-anime-error/40 bg-anime-error/10 text-center animate-slide-up">
          <div className="text-4xl mb-2">💀</div>
          <p className="text-anime-error font-bold text-xl">Partie terminée</p>
          {revealedAnswer && (
            <p className="text-black/60 dark:text-anime-light-text dark:text-anime-dark-text/60 text-sm mt-1">
              C'était : <span className="text-anime-light-text dark:text-anime-dark-text font-semibold">{revealedAnswer}</span>
            </p>
          )}
        </div>
      )}

      {/* Guess Input */}
      {phase === 'playing' && (
        <div className="glass-card p-4 space-y-3">
          <label className="text-xs font-semibold text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider block">
            Votre proposition
          </label>
          <SearchBar
            onSelect={setSelectedGuess}
            placeholder="Entrez le nom d'un anime..."
          />
          {selectedGuess && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-anime-purple/10 border border-anime-purple/30 animate-fade-in">
              <span className="text-sm text-black/80 dark:text-anime-light-text dark:text-anime-dark-text/80">
                Proposition : <strong className="text-anime-light-text dark:text-anime-dark-text">{selectedGuess.title || selectedGuess.name}</strong>
              </span>
              <button
                id="submit-guess-btn"
                onClick={handleGuess}
                disabled={isGuessing}
                className="btn-primary py-2 px-4 text-sm flex items-center gap-1.5"
              >
                {isGuessing ? (
                  <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Zap className="w-3 h-3" />
                    Valider
                  </>
                )}
              </button>
            </div>
          )}
          {error && (
            <p className="text-anime-error text-xs flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> {error}
            </p>
          )}
        </div>
      )}

      {/* Attempts History */}
      {attempts.length > 0 && (
        <div className="glass-card p-4 space-y-2">
          <h3 className="text-xs font-semibold text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 uppercase tracking-wider mb-3 flex items-center gap-2">
            <ChevronRight className="w-3 h-3" />
            Historique des tentatives
          </h3>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {[...attempts].reverse().map((attempt, idx) => (
              <AttemptRow key={idx} attempt={attempt} index={attempts.length - 1 - idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
