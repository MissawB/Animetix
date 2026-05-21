import { useState, useEffect } from 'react';
import { getAkinetixGameState, startAkinetixGame, answerAkinetixGame, confirmAkinetixGame } from '../api';
import { Loader2, RefreshCw, Trophy, Brain, Check, X, HelpCircle } from 'lucide-react';

export function AkinetixGame() {
  const [state, setState] = useState({
    mediaType: 'Anime',
    currentQuestion: null,
    history: [],
    gameOver: false,
    aiGuess: null,
    isDaily: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userWon, setUserWon] = useState(false);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    setLoading(true);
    try {
      let data;
      try {
        data = await getAkinetixGameState();
      } catch (err) {
        data = await startAkinetixGame('Anime');
      }
      
      setState({
        mediaType: data.media_type || 'Anime',
        currentQuestion: data.current_question || null,
        history: data.history || [],
        gameOver: data.game_over || false,
        aiGuess: data.ai_guess || null,
        isDaily: data.is_daily || false,
      });
      setUserWon(false);
    } catch (err) {
      setError("Erreur de chargement. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      const data = await startAkinetixGame(state.mediaType);
      setState({
        mediaType: data.media_type || 'Anime',
        currentQuestion: data.current_question || null,
        history: data.history || [],
        gameOver: data.game_over || false,
        aiGuess: data.ai_guess || null,
        isDaily: data.is_daily || false,
      });
      setUserWon(false);
    } catch (err) {
      setError("Impossible de relancer la partie.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (answer) => {
    if (state.gameOver || state.aiGuess) return;
    setLoading(true);
    try {
      const data = await answerAkinetixGame(answer);
      setState(prev => ({
        ...prev,
        currentQuestion: data.current_question,
        history: data.history,
        gameOver: data.game_over,
        aiGuess: data.ai_guess,
      }));
    } catch (err) {
      console.error("Erreur lors de la réponse :", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (isCorrect) => {
    setLoading(true);
    try {
      const data = await confirmAkinetixGame(isCorrect);
      setState(prev => ({
        ...prev,
        gameOver: true,
      }));
      setUserWon(data.user_won);
    } catch (err) {
      console.error("Erreur lors de la confirmation :", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !state.currentQuestion && !state.aiGuess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="w-12 h-12 text-anime-accent animate-spin mb-4" />
        <p className="manga-font text-xl italic opacity-50 text-anime-light-text dark:text-anime-dark-text">Connexion à l'IA Akinetix...</p>
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
          🧠 Akinetix Devin <span className="text-anime-accent text-xl ml-2">({state.mediaType})</span>
        </h2>
      </div>

      {/* ZONE PRINCIPALE DU JEU */}
      {!state.gameOver && !state.aiGuess && (
        <div className="bg-gradient-to-br from-pink-600 via-rose-500 to-pink-400 rounded-[3rem] p-10 mb-12 shadow-2xl text-center transform transition-all duration-500 text-white">
          <Brain className="w-16 h-16 mx-auto mb-6 opacity-90 animate-pulse" />
          <h3 className="text-3xl font-black italic manga-font mb-10 drop-shadow-lg leading-tight">
            "{state.currentQuestion}"
          </h3>
          
          <div className="flex flex-wrap justify-center gap-6">
            <button 
              onClick={() => handleAnswer('OUI')}
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white font-black italic manga-font text-xl py-4 px-8 rounded-2xl shadow-lg transition-transform hover:scale-105 disabled:opacity-50 flex items-center gap-2"
            >
              <Check className="w-6 h-6" /> OUI
            </button>
            <button 
              onClick={() => handleAnswer('NON')}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white font-black italic manga-font text-xl py-4 px-8 rounded-2xl shadow-lg transition-transform hover:scale-105 disabled:opacity-50 flex items-center gap-2"
            >
              <X className="w-6 h-6" /> NON
            </button>
            <button 
              onClick={() => handleAnswer('PEUT-ÊTRE')}
              disabled={loading}
              className="bg-yellow-500 hover:bg-yellow-600 text-white font-black italic manga-font text-xl py-4 px-8 rounded-2xl shadow-lg transition-transform hover:scale-105 disabled:opacity-50 flex items-center gap-2"
            >
              <HelpCircle className="w-6 h-6" /> PEUT-ÊTRE
            </button>
          </div>
        </div>
      )}

      {/* ZONE DE PROPOSITION DE L'IA */}
      {!state.gameOver && state.aiGuess && (
        <div className="bg-gradient-to-br from-purple-700 via-indigo-600 to-blue-500 rounded-[3rem] p-10 mb-12 shadow-2xl text-center transform transition-all duration-500 text-white animate-bounce-in">
          <h3 className="text-2xl font-bold mb-4 opacity-90">L'IA pense à...</h3>
          <h2 className="text-5xl font-black italic manga-font mb-10 text-yellow-400 drop-shadow-xl">
            {state.aiGuess}
          </h2>
          <p className="mb-6 font-bold text-lg">Est-ce bien cela ?</p>
          
          <div className="flex flex-wrap justify-center gap-6">
            <button 
              onClick={() => handleConfirm(true)}
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white font-black italic manga-font text-xl py-4 px-8 rounded-2xl shadow-lg transition-transform hover:scale-105 disabled:opacity-50"
            >
              OUI, TU AS TROUVÉ !
            </button>
            <button 
              onClick={() => handleConfirm(false)}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white font-black italic manga-font text-xl py-4 px-8 rounded-2xl shadow-lg transition-transform hover:scale-105 disabled:opacity-50"
            >
              NON, C'EST FAUX !
            </button>
          </div>
        </div>
      )}

      {/* GESTION DE FIN DE JEU */}
      {state.gameOver && (
        <div className={`p-8 rounded-[3rem] bg-white dark:bg-[#1a1a2e] mb-12 shadow-2xl animate-bounce-in border-4 ${userWon ? 'border-yellow-500' : 'border-red-500'} text-center`}>
          <h3 className={`manga-font text-4xl mb-6 flex justify-center items-center gap-3 ${userWon ? 'text-yellow-500' : 'text-red-500'}`}>
            {userWon ? <><Trophy className="w-10 h-10" /> VOUS AVEZ BATTU L'IA !</> : '🤖 L\'IA A GAGNÉ !'}
          </h3>
          <p className="text-xl mb-8 text-anime-light-text dark:text-anime-dark-text">
            {userWon 
              ? "Impressionnant, l'Akinetix n'a pas réussi à deviner à quoi vous pensiez." 
              : `L'IA a réussi à trouver ${state.aiGuess}.`}
          </p>
          <button 
            onClick={handleRestart}
            className="bg-anime-accent hover:bg-anime-accent-dark text-black px-8 py-4 rounded-2xl font-black italic manga-font shadow-lg transition-all hover:scale-105 flex items-center justify-center gap-2 mx-auto"
          >
            <RefreshCw className="w-5 h-5" /> Rejouer
          </button>
        </div>
      )}

      {/* HISTORIQUE DES QUESTIONS */}
      {state.history.length > 0 && (
        <div className="mt-8 animate-fade-in">
          <h5 className="manga-font text-xl italic opacity-50 mb-6 text-anime-light-text dark:text-anime-dark-text">HISTORIQUE DES QUESTIONS</h5>
          <div className="flex flex-col gap-3">
            {state.history.map((item, idx) => (
              <div key={idx} className="bg-white dark:bg-[#2a2a3a] rounded-2xl shadow-md p-4 flex justify-between items-center text-anime-light-text dark:text-anime-dark-text">
                <span className="font-medium italic">"{item.question}"</span>
                <span className={`font-black uppercase text-sm ${item.answer === 'OUI' ? 'text-green-500' : item.answer === 'NON' ? 'text-red-500' : 'text-yellow-500'}`}>
                  {item.answer}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
