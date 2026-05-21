import React, { useState, useEffect } from 'react';
import { Brain, History, Check, X, HelpCircle } from 'lucide-react';

const AkinetixPage = () => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/v1/game/akinetix/state/');
      if (!res.ok) throw new Error('No game in progress');
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error loading Akinetix:", err);
      startNewGame();
    }
  };

  const startNewGame = async () => {
    try {
      const res = await fetch('/api/v1/game/akinetix/start/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error starting Akinetix:", err);
    }
  };

  const answer = async (ans) => {
    try {
      const res = await fetch('/api/v1/game/akinetix/answer/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ answer: ans })
      });
      const json = await res.json();
      setGameState(json);
    } catch (err) {
      console.error("Error submitting answer:", err);
    }
  };

  const confirm = async (isCorrect) => {
    try {
      const res = await fetch('/api/v1/game/akinetix/confirm/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ correct: isCorrect })
      });
      if (res.ok) window.location.reload();
    } catch (err) {
      console.error("Error confirming:", err);
    }
  };

  useEffect(() => { fetchState(); }, []);

  if (loading) return <div className="text-center py-20 text-white">Initialisation du devin...</div>;

  return (
    <div className="flex justify-center items-center py-12 px-6">
      <div className="max-w-3xl w-full text-center">
        <div className="bg-white dark:bg-navy-800 border border-gray-100 dark:border-white/5 shadow-2xl p-10 rounded-[3rem]">
          <h2 className="text-3xl font-black mb-8 flex items-center justify-center gap-3">
            <Brain className="w-8 h-8 text-yellow-400" /> Akinetix : Le Devin
          </h2>
          
          <div className="mb-6 text-left bg-gray-50 dark:bg-navy-900 p-6 rounded-2xl max-h-40 overflow-y-auto">
            <h4 className="text-xs font-black uppercase opacity-40 mb-3 flex items-center gap-2">
                <History className="w-3 h-3" /> Historique
            </h4>
            {gameState.history.map((item, i) => (
              <div key={i} className="text-sm opacity-70 mb-2 border-l-2 border-yellow-400 pl-3">
                <span className="font-bold text-yellow-500">IA :</span> {item.q} <span className="font-black italic ml-2">{item.a}</span>
              </div>
            ))}
          </div>

          <div className="text-2xl md:text-4xl mb-10 font-black text-blue-600 dark:text-blue-400 leading-tight">
            {gameState.game_over ? `C'est un(e) ${gameState.ai_guess} ?` : gameState.current_question}
          </div>

          {!gameState.game_over ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button onClick={() => answer('OUI')} className="bg-green-500 hover:bg-green-600 text-white font-black py-4 rounded-2xl transition-transform hover:scale-105 shadow-xl flex items-center justify-center gap-2">
                <Check className="w-5 h-5" /> OUI
              </button>
              <button onClick={() => answer('NON')} className="bg-red-500 hover:bg-red-600 text-white font-black py-4 rounded-2xl transition-transform hover:scale-105 shadow-xl flex items-center justify-center gap-2">
                <X className="w-5 h-5" /> NON
              </button>
              <button onClick={() => answer('PEUT-ÊTRE')} className="bg-gray-500 hover:bg-gray-600 text-white font-black py-4 rounded-2xl transition-transform hover:scale-105 shadow-xl flex items-center justify-center gap-2">
                <HelpCircle className="w-5 h-5" /> PEUT-ÊTRE
              </button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <button onClick={() => confirm(true)} className="bg-blue-600 hover:bg-blue-700 text-white font-black py-4 px-10 rounded-2xl transition-transform hover:scale-105 shadow-xl">
                OUI, BIEN JOUÉ !
              </button>
              <button onClick={() => confirm(false)} className="border-2 border-gray-800 dark:border-white/20 hover:bg-gray-800 hover:text-white font-black py-4 px-10 rounded-2xl transition-all">
                NON, TU AS ÉCHOUÉ
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export default AkinetixPage;
