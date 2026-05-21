import { useState, useEffect, useRef } from 'react';
import { getBlindtestGameState, startBlindtestGame, guessBlindtestGame } from '../api';
import { SearchBar } from './SearchBar';
import { Loader2, RefreshCw, Trophy, Play, Pause } from 'lucide-react';

export function BlindtestGame() {
  const [state, setState] = useState({
    videoUrl: null,
    themeType: 'Random',
    blindtestSong: null,
    blindtestArtists: [],
    guesses: [],
    gameOver: false,
    isDaily: false,
    secretTitle: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const videoRef = useRef(null);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    setLoading(true);
    try {
      let data;
      try {
        data = await getBlindtestGameState();
      } catch (err) {
        data = await startBlindtestGame('Random');
      }
      
      setState({
        videoUrl: data.video_url,
        themeType: data.theme_type || 'Random',
        blindtestSong: data.blindtest_song,
        blindtestArtists: data.blindtest_artists || [],
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        secretTitle: data.secret_title || null,
      });
    } catch (err) {
      setError("Erreur de chargement. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async (themePref = 'Random') => {
    setLoading(true);
    setIsPlaying(false);
    try {
      const data = await startBlindtestGame(themePref);
      setState({
        videoUrl: data.video_url,
        themeType: data.theme_type || themePref,
        blindtestSong: data.blindtest_song,
        blindtestArtists: data.blindtest_artists || [],
        guesses: data.guesses || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        secretTitle: null,
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
      const data = await guessBlindtestGame(item.title || item.name);
      
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

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  if (loading && !state.videoUrl) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">Préparation de l'extrait audio...</p>
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

  const showVideoHint = state.guesses.length >= 5;

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-10 animate-fade-in pb-20">
      
      <div className="text-center mb-10">
        {state.isDaily && (
          <div className="inline-block bg-yellow-400 text-black font-black uppercase text-xs px-4 py-2 rounded-full mb-4 shadow-sm animate-bounce-in">
            ⭐ Défi du jour
          </div>
        )}
        <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter uppercase text-anime-light-text dark:text-anime-dark-text manga-font mb-4">
          BLIND TEST<span className="text-yellow-400">.</span>
        </h1>
        <p className="text-xl font-bold uppercase tracking-widest text-anime-light-text dark:text-anime-dark-text opacity-80 mb-6">
          Écoutez l'extrait et devinez l'animé.
        </p>

        <div className="flex justify-center gap-2">
            <button onClick={() => handleRestart('OP')} className={\`px-6 py-2 rounded-full font-black italic manga-font text-xs transition-all shadow-lg \${state.themeType === 'OP' ? 'bg-emerald-500 text-white scale-110' : 'bg-gray-200 dark:bg-gray-800 text-gray-500 hover:bg-emerald-500 hover:text-white'}\`}>OPENINGS</button>
            <button onClick={() => handleRestart('ED')} className={\`px-6 py-2 rounded-full font-black italic manga-font text-xs transition-all shadow-lg \${state.themeType === 'ED' ? 'bg-emerald-500 text-white scale-110' : 'bg-gray-200 dark:bg-gray-800 text-gray-500 hover:bg-emerald-500 hover:text-white'}\`}>ENDINGS</button>
            <button onClick={() => handleRestart('Random')} className={\`px-6 py-2 rounded-full font-black italic manga-font text-xs transition-all shadow-lg \${state.themeType === 'Random' ? 'bg-emerald-500 text-white scale-110' : 'bg-gray-200 dark:bg-gray-800 text-gray-500 hover:bg-emerald-500 hover:text-white'}\`}>MÉLANGE</button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-stretch">
        
        {/* LEFT COLUMN: THE PLAYER */}
        <div className="w-full md:w-1/2 flex flex-col">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[40px] p-8 shadow-xl flex-grow flex flex-col items-center justify-center relative overflow-hidden">
            
            {state.gameOver ? (
              <div className="w-full animate-zoom-in text-center">
                <div className="aspect-video rounded-[2rem] overflow-hidden shadow-2xl mb-8 border-4 border-emerald-500 bg-black group relative">
                    <video controls autoPlay className="w-full h-full object-cover">
                        <source src={state.videoUrl} type="video/webm" />
                    </video>
                </div>
                <h2 className="text-4xl font-black italic manga-font text-emerald-500 mb-2 uppercase">{state.secretTitle}</h2>
                <p className="text-xl mb-1 opacity-60 text-anime-light-text dark:text-anime-dark-text">{state.blindtestSong}</p>
                <p className="text-sm opacity-50 mb-6 text-anime-light-text dark:text-anime-dark-text">{state.blindtestArtists.join(", ")}</p>
                
                <div className="inline-block bg-emerald-500 text-white px-10 py-3 rounded-2xl font-black italic manga-font text-2xl shadow-xl transform -rotate-2 mb-8">
                    VICTOIRE ! ✅
                </div>
                
                <div className="mt-4">
                    <button onClick={() => handleRestart(state.themeType)} className="inline-block bg-emerald-500 hover:bg-emerald-600 text-white font-black italic manga-font py-4 px-12 rounded-2xl shadow-2xl hover:scale-105 transition-all">
                        NOUVEL EXTRAIT
                    </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center w-full">
                {/* VINYL UI */}
                <div className={\`relative w-64 h-64 mb-10 transition-all duration-700 \${showVideoHint ? 'scale-75 opacity-50' : 'scale-100'}\`}>
                    <div className={\`w-full h-full rounded-full bg-[#111] border-8 border-[#222] shadow-[0_0_50px_rgba(0,0,0,0.5)] flex items-center justify-center \${isPlaying ? 'animate-spin-slow' : ''}\`}>
                        {/* Grooves */}
                        <div className="absolute inset-0 rounded-full" style={{ background: 'repeating-radial-gradient(circle at center, transparent, transparent 5px, rgba(255,255,255,0.05) 6px, transparent 7px)' }}></div>
                        {/* Label */}
                        <div className="w-24 h-24 bg-emerald-500 rounded-full border-4 border-[#111] z-10 flex items-center justify-center">
                            <span className="text-3xl">❓</span>
                        </div>
                    </div>
                    <button 
                        onClick={togglePlay}
                        className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 bg-emerald-500 text-white w-16 h-16 rounded-full flex items-center justify-center shadow-2xl hover:scale-110 transition-all z-20"
                    >
                        {isPlaying ? <Pause className="w-8 h-8 fill-current" /> : <Play className="w-8 h-8 fill-current ml-1" />}
                    </button>
                </div>

                {/* HIDDEN OR BLURRED VIDEO ELEMENT */}
                <div className={\`w-full transition-all duration-1000 overflow-hidden rounded-[2rem] shadow-2xl border-4 border-emerald-500/30 bg-black \${showVideoHint ? 'h-auto opacity-100 mb-8' : 'h-0 opacity-0 mb-0'}\`}>
                    <video 
                        ref={videoRef} 
                        className={\`w-full object-cover \${!state.gameOver ? 'blur-[30px] opacity-80' : ''}\`}
                        onEnded={() => setIsPlaying(false)}
                    >
                        <source src={state.videoUrl} type="video/webm" />
                    </video>
                </div>
              </div>
            )}
            
          </div>
        </div>

        {/* RIGHT COLUMN: THE SEARCH & HISTORY */}
        <div className="w-full md:w-1/2 flex flex-col text-left">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[30px] p-8 shadow-xl flex-grow flex flex-col">
            <h4 className="text-2xl font-black italic manga-font mb-6 text-anime-light-text dark:text-anime-dark-text">
              Proposez un animé
            </h4>
            
            {!state.gameOver && (
              <div className="mb-6 relative z-20">
                <SearchBar onSelect={handleGuess} placeholder="Rechercher un animé..." mediaType="anime" />
              </div>
            )}

            <h6 className="text-sm uppercase font-bold text-gray-400 tracking-wider mb-4">
              Historique des tentatives
            </h6>
            
            <div className="overflow-y-auto pr-2 custom-scrollbar flex-grow" style={{ maxHeight: '400px' }}>
              {state.guesses.length > 0 ? (
                state.guesses.slice().reverse().map((g, idx) => (
                    <div key={idx} className="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-3 flex items-center gap-4 mb-3 animate-slide-up border border-gray-100 dark:border-gray-700">
                        {g.image && <img src={g.image} alt={g.title} className="w-12 h-16 object-cover rounded-xl shadow-sm" />}
                        <div className="flex-grow font-bold text-anime-light-text dark:text-anime-dark-text truncate">
                            {g.title}
                        </div>
                        <div className="text-2xl flex-shrink-0 ml-2">
                            {g.is_correct ? '✅' : '❌'}
                        </div>
                    </div>
                ))
              ) : (
                <div className="text-center py-10 opacity-30 flex flex-col items-center">
                  <div className="text-5xl mb-4">🎵</div>
                  <p className="font-medium">Aucune tentative...</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
