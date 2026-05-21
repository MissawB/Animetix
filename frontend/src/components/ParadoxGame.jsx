import { useState, useEffect } from 'react';
import { getParadoxGameState, startParadoxGame, guessParadoxGame } from '../api';
import { Loader2, RefreshCw, Trophy, Target, AlertTriangle } from 'lucide-react';

export function ParadoxGame() {
  const [state, setState] = useState({
    mediaType: 'Anime',
    scenario: null,
    options: [],
    gameOver: false,
    isDaily: false,
    reasoning: null,
    isCorrect: null,
    answer: null,
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
        data = await getParadoxGameState();
      } catch (err) {
        data = await startParadoxGame('Anime');
      }
      
      setState({
        mediaType: data.media_type || 'Anime',
        scenario: data.scenario || null,
        options: data.options || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        reasoning: data.reasoning || null,
        isCorrect: data.is_correct ?? null,
        answer: data.answer || null,
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
      const data = await startParadoxGame(state.mediaType);
      setState({
        mediaType: data.media_type || 'Anime',
        scenario: data.scenario || null,
        options: data.options || [],
        gameOver: data.game_over || false,
        isDaily: data.is_daily || false,
        reasoning: null,
        isCorrect: null,
        answer: null,
      });
    } catch (err) {
      setError("Impossible de relancer la partie.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuess = async (guessTitle) => {
    if (state.gameOver) return;
    setLoading(true);
    try {
      const data = await guessParadoxGame(guessTitle);
      setState(prev => ({
        ...prev,
        gameOver: true,
        isCorrect: data.is_correct,
        reasoning: data.reasoning,
        answer: data.answer,
        options: data.final_options || prev.options,
      }));
    } catch (err) {
      console.error("Erreur lors du choix :", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !state.scenario) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">L'IA génère le paradoxe...</p>
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
            🏆 Défi du jour
          </div>
        )}
        <h2 className="text-4xl font-black italic manga-font text-anime-light-text dark:text-anime-dark-text flex items-center justify-center gap-4">
          <AlertTriangle className="w-10 h-10 text-red-500" /> Paradox Quest <span className="text-anime-accent text-xl">({state.mediaType})</span>
        </h2>
      </div>

      {/* ZONE DU SCÉNARIO */}
      <div className="bg-gradient-to-br from-red-800 via-red-600 to-rose-500 rounded-[3rem] p-10 mb-12 shadow-2xl transform transition-all duration-500 text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Target className="w-64 h-64" />
        </div>
        <div className="relative z-10 text-center">
          <p className="text-white/80 font-bold uppercase tracking-widest text-sm mb-6">Rapport de l'IA</p>
          <p className="text-2xl md:text-3xl font-serif italic mb-8 leading-relaxed drop-shadow-md">
            "{state.scenario}"
          </p>
          {!state.gameOver && (
            <p className="text-yellow-300 font-black tracking-widest uppercase text-xl animate-pulse">
              DÉBUSQUEZ L'INTRUS !
            </p>
          )}
        </div>
      </div>

      {/* OPTIONS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        {state.options.map((opt, idx) => {
          const isSelected = opt.is_user_choice;
          const isIntruder = opt.is_intruder;
          
          let cardClass = "bg-white dark:bg-[#1a1a2e] rounded-3xl shadow-xl overflow-hidden cursor-pointer transform transition-all duration-300 hover:scale-105 border-4 border-transparent group";
          
          if (state.gameOver) {
            cardClass = "bg-white dark:bg-[#1a1a2e] rounded-3xl shadow-xl overflow-hidden transform transition-all duration-500 opacity-80 border-4 border-transparent";
            if (isIntruder) {
              cardClass += " !border-red-500 scale-105 opacity-100 z-10";
            }
            if (isSelected && !isIntruder) {
              cardClass += " !border-gray-500 grayscale";
            }
          }

          return (
            <div 
              key={idx} 
              className={cardClass}
              onClick={() => !state.gameOver && handleGuess(opt.title)}
            >
              <div className="relative h-64 w-full">
                {opt.image ? (
                  <img src={opt.image} alt={opt.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-black/10 dark:bg-white/10 flex items-center justify-center text-4xl">❓</div>
                )}
                
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>
                
                {state.gameOver && isIntruder && (
                  <div className="absolute top-4 right-4 bg-red-500 text-white px-3 py-1 rounded-full font-black text-xs uppercase animate-bounce-in">
                    Intrus
                  </div>
                )}
                {state.gameOver && isSelected && !isIntruder && (
                  <div className="absolute top-4 right-4 bg-gray-500 text-white px-3 py-1 rounded-full font-black text-xs uppercase animate-bounce-in">
                    Erreur
                  </div>
                )}
              </div>
              <div className="p-6 text-center bg-[#111]">
                <h3 className="manga-font text-2xl text-white drop-shadow-md">
                  {opt.title}
                </h3>
              </div>
            </div>
          );
        })}
      </div>

      {/* GESTION DE FIN DE JEU */}
      {state.gameOver && (
        <div className={`p-10 rounded-[3rem] bg-white dark:bg-[#1a1a2e] mb-12 shadow-2xl animate-slide-up border-4 ${state.isCorrect ? 'border-green-500' : 'border-red-500'}`}>
          <div className="text-center mb-8">
            <h3 className={`manga-font text-5xl mb-4 flex justify-center items-center gap-3 ${state.isCorrect ? 'text-green-500' : 'text-red-500'}`}>
              {state.isCorrect ? <><Trophy className="w-12 h-12" /> BIEN JOUÉ !</> : 'ÉCHEC...'}
            </h3>
            <p className="text-2xl text-anime-light-text dark:text-anime-dark-text">
              L'intrus était bien <strong className="text-anime-accent font-black">{state.answer}</strong>.
            </p>
          </div>
          
          <div className="bg-black/5 dark:bg-white/5 rounded-2xl p-6 text-center italic text-lg leading-relaxed text-anime-light-text dark:text-anime-dark-text mb-10 border-l-4 border-anime-accent">
            "{state.reasoning}"
          </div>
          
          <div className="flex justify-center">
            <button 
              onClick={handleRestart}
              className="bg-anime-accent hover:bg-anime-accent-dark text-black px-10 py-4 rounded-2xl font-black italic manga-font shadow-lg transition-all hover:scale-105 flex items-center gap-3 text-xl"
            >
              <RefreshCw className="w-6 h-6" /> Rejouer
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
