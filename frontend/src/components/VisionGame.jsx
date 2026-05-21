import { useState, useEffect } from 'react';
import { getVisionGameState, startVisionGame, guessVisionGame } from '../api';
import { Loader2, RefreshCw, Trophy } from 'lucide-react';

export function VisionGame() {
  const [state, setState] = useState({
    mediaType: 'Anime',
    isDaily: false,
    gameOver: false,
    guesses: [],
    bestScore: 0,
    imageUrl: null,
    secretTitle: null,
  });
  const [loading, setLoading] = useState(true);
  const [guessText, setGuessText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    setLoading(true);
    try {
      let data;
      try {
        data = await getVisionGameState();
      } catch (err) {
        data = await startVisionGame('Anime');
      }
      
      setState({
        mediaType: data.media_type || 'Anime',
        isDaily: data.is_daily || false,
        gameOver: data.game_over || false,
        guesses: data.guesses || [],
        bestScore: data.best_score || 0,
        imageUrl: data.image_url || null,
        secretTitle: data.secret_title || null,
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
      const data = await startVisionGame(state.mediaType);
      setState({
        mediaType: data.media_type || 'Anime',
        isDaily: data.is_daily || false,
        gameOver: data.game_over || false,
        guesses: data.guesses || [],
        bestScore: data.best_score || 0,
        imageUrl: data.image_url || null,
        secretTitle: null,
      });
      setGuessText("");
    } catch (err) {
      setError("Impossible de relancer la partie.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!guessText.trim() || state.gameOver || submitting) return;
    
    setSubmitting(true);
    try {
      const data = await guessVisionGame(guessText);
      setState(prev => ({
        ...prev,
        guesses: data.guesses,
        gameOver: data.game_over,
        bestScore: data.best_score,
        secretTitle: data.secret_title,
      }));
      setGuessText("");
    } catch (err) {
      console.error("Erreur lors de la soumission de la proposition :", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !state.imageUrl) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">Initialisation de la vision...</p>
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

  const blurAmount = state.bestScore > 80 ? 'blur(2px)' : (state.bestScore > 50 ? 'blur(8px)' : 'blur(20px)');

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-10 animate-fade-in pb-20">
      
      <div className="text-center mb-10">
        {state.isDaily && (
          <div className="inline-block bg-yellow-400 text-black font-black uppercase text-xs px-4 py-2 rounded-full mb-4 shadow-sm animate-bounce-in">
            ⭐ Défi du jour
          </div>
        )}
        <div className="text-5xl mb-2">👁️</div>
        <h2 className="text-4xl font-black italic manga-font text-anime-light-text dark:text-anime-dark-text">
          Vision Quest <span className="text-anime-accent text-xl ml-2">({state.mediaType})</span>
        </h2>
        <p className="text-lg opacity-70 mt-2 text-anime-light-text dark:text-anime-dark-text">
          L'IA voit une image. Décrivez-la avec précision pour la faire apparaître.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-stretch">
        
        {/* LEFT COLUMN: THE IMAGE */}
        <div className="w-full md:w-1/2 flex flex-col">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[40px] p-8 shadow-xl flex-grow flex flex-col items-center justify-center relative overflow-hidden">
            <div className="relative w-full max-w-[400px]">
              {state.gameOver ? (
                <div className="animate-zoom-in text-center">
                  <img src={state.imageUrl} alt="Secret" className="w-full rounded-2xl shadow-lg border-4 border-green-500" />
                  <div className="mt-6 animate-fade-in-up">
                    <h2 className="text-3xl font-black text-green-500 mb-2">{state.secretTitle}</h2>
                    <div className="inline-block bg-green-500 text-white rounded-full px-6 py-2 font-bold shadow-sm mb-6">
                      DÉCOUVERT !
                    </div>
                    <div>
                      <button 
                        onClick={handleRestart}
                        className="bg-anime-accent hover:bg-anime-accent-dark text-black px-8 py-3 rounded-full font-black italic manga-font shadow-lg transition-transform hover:scale-105"
                      >
                        Nouvelle Quête
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <img 
                    src={state.imageUrl} 
                    alt="Blurred Target" 
                    className="w-full rounded-2xl shadow-lg transition-all duration-1000 ease-in-out"
                    style={{ filter: blurAmount }}
                  />
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white text-center bg-black/40 backdrop-blur-md px-6 py-4 rounded-3xl shadow-2xl border border-white/10">
                    <div className="text-5xl font-black">{Math.round(state.bestScore)}%</div>
                    <div className="font-bold uppercase text-xs tracking-wider opacity-80 mt-1">Similarité Visuelle</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: THE SEARCH & HISTORY */}
        <div className="w-full md:w-1/2 flex flex-col text-left">
          <div className="bg-white dark:bg-[#1a1a2e] rounded-[30px] p-8 shadow-xl flex-grow flex flex-col">
            <h4 className="text-2xl font-black italic manga-font mb-6 text-anime-light-text dark:text-anime-dark-text">
              Décrivez ce que vous "voyez"
            </h4>
            
            {!state.gameOver && (
              <form onSubmit={handleSubmit} className="mb-6">
                <div className="flex bg-gray-100 dark:bg-gray-800 rounded-full shadow-inner overflow-hidden border border-gray-200 dark:border-gray-700">
                  <input 
                    type="text" 
                    value={guessText}
                    onChange={(e) => setGuessText(e.target.value)}
                    className="flex-grow bg-transparent border-0 px-6 py-4 outline-none text-anime-light-text dark:text-anime-dark-text placeholder-gray-400"
                    placeholder="Ex: Un guerrier avec une épée géante..."
                    required
                    disabled={submitting}
                  />
                  <button 
                    type="submit" 
                    disabled={submitting}
                    className="bg-anime-accent hover:bg-anime-accent-dark text-black px-8 font-black transition-colors disabled:opacity-50"
                  >
                    {submitting ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : 'Analyser'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-3 px-4 font-medium">
                  Plus vos mots décrivent fidèlement l'image, plus le score augmente.
                </p>
              </form>
            )}

            <h6 className="text-sm uppercase font-bold text-gray-400 tracking-wider mb-4">
              Historique des descriptions
            </h6>
            
            <div className="overflow-y-auto pr-2 custom-scrollbar flex-grow" style={{ maxHeight: '400px' }}>
              {state.guesses.length > 0 ? (
                state.guesses.map((g, idx) => {
                  const isGood = g.score > 80;
                  return (
                    <div 
                      key={idx} 
                      className={`p-4 mb-3 rounded-2xl flex justify-between items-center transition-all animate-slide-up ${isGood ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-gray-50 dark:bg-gray-800/50 text-anime-light-text dark:text-anime-dark-text'}`}
                    >
                      <span className="text-sm font-medium pr-4 flex-grow italic">"{g.text}"</span>
                      <div className="flex flex-col items-end flex-shrink-0">
                        <span className="font-black text-lg mb-1">{g.score.toFixed(1)}%</span>
                        <div className="h-1.5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${isGood ? 'bg-green-500' : 'bg-blue-500'}`}
                            style={{ width: \`\${Math.min(100, Math.max(0, g.score))}%\` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-10 opacity-30 flex flex-col items-center">
                  <div className="text-5xl mb-4">💬</div>
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
