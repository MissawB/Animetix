import { useState, useEffect } from 'react';
import { getCovertestGameState, startCovertestGame, guessCovertestGame } from '../api';
import { SearchBar } from './SearchBar';
import { Loader2, RefreshCw, Trophy, Book } from 'lucide-react';

export function CovertestGame() {
  const [state, setState] = useState({
    coverUrl: null,
    guesses: [],
    gameOver: false,
    isDaily: false,
    secretTitle: null,
    locale: 'FR',
    volume: 1,
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
        data = await getCovertestGameState();
      } catch (err) {
        data = await startCovertestGame(false);
      }
      
      setState({
        coverUrl: data.cover_url,
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        secretTitle: data.secret_title || null,
        locale: data.locale || 'FR',
        volume: data.volume || 1,
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
      const data = await startCovertestGame(false);
      setState({
        coverUrl: data.cover_url,
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        secretTitle: null,
        locale: data.locale || 'FR',
        volume: data.volume || 1,
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
      const data = await guessCovertestGame(item.title || item.name);
      
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

  if (loading && !state.coverUrl) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">Recherche d'une couverture...</p>
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
    <div className="w-full max-w-5xl mx-auto px-6 py-10 animate-fade-in pb-20">
      
      <div className="text-center mb-10">
        {state.isDaily && (
          <div className="inline-block bg-yellow-400 text-black font-black uppercase text-xs px-4 py-2 rounded-full mb-4 shadow-sm animate-bounce-in">
            ⭐ Défi du jour
          </div>
        )}
        <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter uppercase text-anime-light-text dark:text-anime-dark-text manga-font mb-4">
          COVER TEST<span className="text-yellow-400">.</span>
        </h1>
        <p className="text-xl font-bold uppercase tracking-widest text-anime-light-text dark:text-anime-dark-text opacity-80 mb-6">
          Observez la couverture et devinez le manga.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-stretch">
        
        {/* LEFT COLUMN: THE COVER */}
        <div className="w-full md:w-1/2 flex flex-col">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[40px] p-8 shadow-xl flex-grow flex flex-col items-center justify-center relative overflow-hidden">
            
            <div className="w-full max-w-[300px]">
              <div className="relative p-4 bg-white dark:bg-[#0a0a0a] shadow-2xl rounded-xl transform perspective-[1000px] -rotate-y-6 hover:rotate-y-0 transition-transform duration-500 mb-8">
                <div className="aspect-[3/4] rounded overflow-hidden relative shadow-inner bg-black">
                    <img 
                      src={state.coverUrl} 
                      alt="Manga Cover" 
                      className="w-full h-full object-cover"
                    />
                    {!state.gameOver && (
                        <div className="absolute inset-0 bg-black/40 backdrop-blur-xl flex flex-col items-center justify-center transition-opacity duration-500">
                            <div className="text-6xl opacity-50 mb-4">❓</div>
                            <div className="text-xs text-white font-black uppercase tracking-[0.3em] opacity-80">Couverture Cachée</div>
                        </div>
                    )}
                </div>
              </div>

              <div className="flex justify-between items-center px-2 mb-8">
                  <div className="bg-amber-500 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase italic tracking-widest shadow-lg">
                      Edition {state.locale.toUpperCase()}
                  </div>
                  <div className="bg-gray-800 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase italic tracking-widest shadow-lg">
                      Volume {state.volume}
                  </div>
              </div>

              {state.gameOver && (
                  <div className="text-center animate-fade-in-up">
                      <h2 className="text-4xl font-black italic manga-font text-amber-500 mb-2 uppercase">{state.secretTitle}</h2>
                      <div className="inline-block bg-emerald-500 text-white px-10 py-3 rounded-2xl font-black italic manga-font text-2xl shadow-xl transform -rotate-2 mb-8">
                          TROUVÉ ! ✅
                      </div>
                      <div className="mt-4">
                          <button onClick={handleRestart} className="inline-block bg-amber-500 hover:bg-amber-600 text-white font-black italic manga-font py-4 px-12 rounded-2xl shadow-2xl hover:scale-105 transition-all">
                              NOUVELLE COVER
                          </button>
                      </div>
                  </div>
              )}
            </div>

          </div>
        </div>

        {/* RIGHT COLUMN: THE SEARCH & HISTORY */}
        <div className="w-full md:w-1/2 flex flex-col text-left">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[30px] p-8 shadow-xl flex-grow flex flex-col border-2 border-amber-500/20">
            <h2 className="text-3xl font-black italic manga-font mb-8 uppercase text-anime-light-text dark:text-anime-dark-text">
                DÉCOUVREZ LE TITRE<span className="text-amber-500">.</span>
            </h2>
            
            {!state.gameOver && (
              <div className="mb-10 relative z-20">
                <SearchBar onSelect={handleGuess} placeholder="Quel manga est-ce ?" mediaType="manga" />
              </div>
            )}

            <div className="flex items-center justify-between mb-6">
                <h6 className="text-xs font-black uppercase tracking-widest opacity-40 text-anime-light-text dark:text-anime-dark-text">TENTATIVES ({state.guesses.length})</h6>
            </div>
            
            <div className="overflow-y-auto pr-2 custom-scrollbar flex-grow" style={{ maxHeight: '400px' }}>
              {state.guesses.length > 0 ? (
                state.guesses.slice().reverse().map((g, idx) => {
                    const isCorrect = g.is_correct;
                    return (
                        <div key={idx} className={\`p-4 mb-3 rounded-3xl flex items-center shadow-sm border-2 animate-slide-up \${isCorrect ? 'bg-emerald-500/10 border-emerald-500 text-emerald-600 dark:text-emerald-400' : 'bg-gray-50 dark:bg-gray-800/50 border-gray-100 dark:border-gray-700'}\`}>
                            {g.image && <img src={g.image} className="w-12 h-12 rounded-xl object-cover shadow-md mr-4" alt="" />}
                            <div className="flex-grow">
                                <div className="font-black italic manga-font uppercase leading-none mb-1 text-sm text-anime-light-text dark:text-anime-dark-text">{g.title}</div>
                                {g.title_english && <div className="text-[10px] opacity-60 font-bold text-anime-light-text dark:text-anime-dark-text">{g.title_english}</div>}
                            </div>
                            
                            {isCorrect ? (
                                <div className="bg-emerald-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">✓</div>
                            ) : (
                                <div className="bg-red-500/10 text-red-500 w-8 h-8 rounded-full flex items-center justify-center font-bold">✕</div>
                            )}
                        </div>
                    );
                })
              ) : (
                <div className="text-center py-20 opacity-30 flex flex-col items-center">
                  <Book className="w-16 h-16 mb-4 text-anime-light-text dark:text-anime-dark-text" />
                  <p className="font-black italic manga-font text-anime-light-text dark:text-anime-dark-text">Proposez un titre pour commencer !</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
