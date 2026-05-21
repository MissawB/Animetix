import { useState, useEffect } from 'react';
import { getEmojiGameState, startEmojiGame, guessEmojiGame } from '../api';
import { SearchBar } from './SearchBar';
import { Loader2, RefreshCw, Trophy } from 'lucide-react';

export function EmojiGame() {
  const [state, setState] = useState({
    emojis: null,
    guesses: [],
    gameOver: false,
    mediaType: 'Anime',
    secretTitle: null,
    isDaily: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    setLoading(true);
    try {
      let data;
      try {
        data = await getEmojiGameState();
      } catch (err) {
        // If no game in progress, start one automatically
        data = await startEmojiGame('Anime');
      }
      
      setState({
        emojis: data.emojis,
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        mediaType: data.media_type || 'Anime',
        secretTitle: data.secret_title || null,
        isDaily: data.is_daily || false,
      });
    } catch (err) {
      setError("Erreur de chargement. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      const data = await startEmojiGame(state.mediaType);
      setState({
        emojis: data.emojis,
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        mediaType: data.media_type || 'Anime',
        secretTitle: null,
        isDaily: data.is_daily || false,
      });
    } catch (err) {
      setError("Impossible de relancer la partie.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuess = async (item) => {
    if (state.gameOver) return;
    
    try {
      const data = await guessEmojiGame(item.title || item.name);
      
      setState(prev => ({
        ...prev,
        guesses: data.guesses,
        gameOver: data.game_over,
        secretTitle: data.secret_title,
      }));
    } catch (err) {
      console.error("Erreur lors de la soumission de la proposition :", err);
    }
  };

  if (loading && !state.emojis) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">Création de l'énigme en cours...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <p className="text-red-500 font-bold mb-4">{error}</p>
        <button onClick={loadState} className="btn-primary">Réessayer</button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-10 animate-fade-in pb-20">
      
      <div className="text-center mb-10">
        {state.isDaily && (
          <div className="inline-block bg-yellow-400 text-black font-black uppercase text-xs px-4 py-2 rounded-full mb-4 shadow-sm animate-bounce-in">
            🏆 Défi du jour
          </div>
        )}
        <h2 className="text-4xl font-black italic manga-font text-anime-light-text dark:text-anime-dark-text">
          🎭 Emoji Decode <span className="text-anime-accent text-xl ml-2">({state.mediaType})</span>
        </h2>
      </div>

      {/* ZONE DES EMOJIS */}
      <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-[3rem] p-10 mb-10 shadow-2xl text-center transform transition-all duration-500">
        <div className="text-white text-6xl md:text-8xl mb-6 drop-shadow-lg tracking-[15px]">
          {state.emojis}
        </div>
        <p className="text-white/90 font-bold italic text-lg">
          L'IA a résumé une œuvre en 5 emojis. Saurez-vous la retrouver ?
        </p>
      </div>

      {/* GESTION DE FIN DE JEU OU RECHERCHE */}
      {state.gameOver ? (
        <div className="p-8 rounded-[3rem] bg-white dark:bg-[#1a1a2e] mb-12 shadow-2xl animate-bounce-in border-4 border-green-500 flex flex-col md:flex-row items-center gap-8">
          <div className="w-1/3">
            {state.guesses.filter(g => g.is_correct).map((g, idx) => (
              <img key={idx} src={g.image} alt="Secret" className="w-full rounded-3xl shadow-xl border-4 border-yellow-400" />
            ))}
          </div>
          <div className="w-2/3 text-left">
            <h3 className="manga-font text-4xl mb-2 text-green-500 flex items-center gap-2">
              <Trophy className="w-8 h-8" /> VICTOIRE !
            </h3>
            <p className="text-xl mb-6 text-anime-light-text dark:text-anime-dark-text">
              C'était bien : <strong className="text-anime-accent font-black">{state.secretTitle}</strong>
            </p>
            <button 
              onClick={handleRestart}
              className="bg-green-500 hover:bg-green-600 text-white px-8 py-4 rounded-2xl font-black italic manga-font shadow-lg transition-all hover:scale-105 flex items-center gap-2"
            >
              <RefreshCw className="w-5 h-5" /> Rejouer
            </button>
          </div>
        </div>
      ) : (
        <div className="mb-12 relative z-20">
          <SearchBar onSelect={handleGuess} placeholder="Proposez une œuvre..." />
        </div>
      )}

      {/* HISTORIQUE */}
      {state.guesses.length > 0 && (
        <div className="mt-8 animate-fade-in">
          <h5 className="manga-font text-xl italic opacity-50 mb-6 text-anime-light-text dark:text-anime-dark-text">VOS TENTATIVES</h5>
          <div className="flex flex-col gap-4">
            {state.guesses.slice().reverse().map((guess, idx) => (
              <div key={idx} className="bg-white dark:bg-[#2a2a3a] rounded-3xl shadow-xl overflow-hidden flex items-center p-4 gap-4 animate-slide-up" style={{ animationDelay: `${idx * 0.05}s` }}>
                <img src={guess.image} alt="Cover" className="w-14 h-20 object-cover rounded-xl shadow-sm" />
                <div className="flex-grow min-w-0">
                  <div className="font-black text-xl text-anime-light-text dark:text-anime-dark-text truncate">
                    {guess.title_en || guess.title}
                  </div>
                  {guess.title_jp && (
                    <div className="text-sm opacity-50 text-anime-light-text dark:text-anime-dark-text truncate">
                      {guess.title_jp}
                    </div>
                  )}
                </div>
                <div className="text-3xl flex-shrink-0 ml-4">
                  {guess.is_correct ? '✅' : '❌'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
