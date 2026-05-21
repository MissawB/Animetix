import React, { useState, useEffect } from 'react';
import { ImageIcon, Send, RotateCcw } from 'lucide-react';

const CovertestPage = () => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [guess, setGuess] = useState('');

  const fetchState = async () => {
    try {
      const res = await fetch('/api/v1/game/covertest/state/');
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error loading game state:", err);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  const handleGuess = async () => {
    try {
      const res = await fetch('/api/v1/game/covertest/guess/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ guess })
      });
      if (res.ok) {
        setGuess('');
        fetchState();
      }
    } catch (err) {
      console.error("Error submitting guess:", err);
    }
  };

  if (loading) return <div className="text-center py-20 text-white font-black animate-pulse">CHARGEMENT DE LA COUVERTURE...</div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Couverture */}
        <div className="relative group">
          <div className="absolute -inset-4 bg-gradient-to-tr from-yellow-400 to-orange-500 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity"></div>
          <img src={gameState.cover_url} className={`relative w-full rounded-[2.5rem] shadow-2xl transition-all duration-700 ${!gameState.game_over ? 'blur-2xl' : 'blur-0 scale-105'}`} alt="Couverture" />
          {!gameState.game_over && (
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-black/60 backdrop-blur-md p-6 rounded-full border-2 border-white/20">
                    <ImageIcon className="w-12 h-12 text-white opacity-50" />
                </div>
            </div>
          )}
        </div>
        
        {/* Jeu */}
        <div className="bg-white dark:bg-navy-800 p-10 rounded-[3.5rem] shadow-2xl border border-gray-100 dark:border-white/5">
          <h2 className="text-4xl font-black italic manga-font mb-10 tracking-tighter">
            COVER <span className="text-yellow-400">QUEST</span>
          </h2>

          {gameState.game_over ? (
            <div className="text-center py-8">
                <h3 className="text-4xl font-black text-green-500 mb-2">TROUVÉ !</h3>
                <p className="text-2xl font-bold text-gray-800 dark:text-white">{gameState.secret_title}</p>
                <button onClick={() => window.location.reload()} className="mt-8 bg-black text-white px-10 py-4 rounded-2xl font-black italic flex items-center gap-3 mx-auto hover:scale-105 transition-transform">
                    <RotateCcw className="w-5 h-5" /> REJOUER
                </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="relative">
                <input 
                    type="text" 
                    value={guess} 
                    onChange={(e) => setGuess(e.target.value)}
                    className="w-full p-5 rounded-2xl bg-gray-50 dark:bg-navy-900 border-0 focus:ring-2 focus:ring-yellow-400 font-bold text-lg" 
                    placeholder="Quel manga est-ce ?"
                />
              </div>
              <button onClick={handleGuess} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-5 rounded-2xl shadow-xl flex items-center justify-center gap-3 transition-all hover:translate-y-[-2px]">
                <Send className="w-5 h-5" /> DEVINER
              </button>
            </div>
          )}

          <div className="mt-12 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-4">Journal des tentatives</h4>
            {gameState.guesses.map((g, i) => (
              <div key={i} className={`flex items-center justify-between p-4 rounded-2xl border-l-4 transition-all ${g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
                <span className="font-bold">{g.title}</span>
                <span className={`font-black text-xs ${g.is_correct ? 'text-green-500' : 'text-red-500'}`}>
                    {g.is_correct ? 'CORRECT' : 'FAUX'}
                </span>
              </div>
            ))}
            {gameState.guesses.length === 0 && <p className="text-center py-6 opacity-20 italic">Aucune tentative pour le moment.</p>}
          </div>
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

export default CovertestPage;
