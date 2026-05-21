import React, { useState, useEffect, useRef } from 'react';
import { Play, Check, X, Music } from 'lucide-react';

const BlindtestPage = () => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [guess, setGuess] = useState('');
  const videoRef = useRef(null);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/v1/game/blindtest/state/');
      if (!res.ok) throw new Error('No game in progress');
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error loading Blindtest:", err);
      startNewGame();
    }
  };

  const startNewGame = async () => {
    try {
      const res = await fetch('/api/v1/game/blindtest/start/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error starting Blindtest:", err);
    }
  };

  const handleGuess = async () => {
    try {
      const res = await fetch('/api/v1/game/blindtest/guess/', {
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

  useEffect(() => { fetchState(); }, []);

  if (loading) return <div className="text-center py-20 text-white">Chargement de l'extrait...</div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* LECTEUR */}
        <div className="bg-white dark:bg-navy-800 p-8 rounded-[3rem] shadow-2xl border border-gray-100 dark:border-white/5">
          {gameState.game_over ? (
            <video ref={videoRef} src={gameState.video_url} controls className="w-full rounded-3xl shadow-lg" />
          ) : (
            <div className="text-center py-10">
               <div className="w-48 h-48 bg-gray-900 rounded-full mx-auto flex items-center justify-center mb-8 shadow-inner border-4 border-yellow-400/20">
                 <button className="bg-yellow-400 text-black p-6 rounded-full hover:scale-110 transition-transform shadow-xl">
                   <Play className="w-10 h-10 fill-current" />
                 </button>
               </div>
               <p className="font-bold text-gray-500 uppercase tracking-widest text-xs">Écoutez l'extrait pour deviner !</p>
            </div>
          )}
        </div>

        {/* JEU */}
        <div className="bg-white dark:bg-navy-800 p-10 rounded-[3rem] shadow-2xl border border-gray-100 dark:border-white/5">
          <h2 className="text-3xl font-black mb-8 flex items-center gap-3">
              <Music className="w-8 h-8 text-yellow-400" /> DÉCOUVREZ L'ANIMÉ
          </h2>
          {!gameState.game_over ? (
            <div className="space-y-6">
              <input 
                type="text" 
                value={guess} 
                onChange={(e) => setGuess(e.target.value)}
                className="w-full p-4 rounded-2xl bg-gray-50 dark:bg-navy-900 border-0 focus:ring-2 focus:ring-yellow-400 font-bold" 
                placeholder="Titre de l'animé..."
              />
              <button onClick={handleGuess} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-4 rounded-2xl shadow-xl transition-all hover:scale-[1.02]">
                VALIDER MA RÉPONSE
              </button>
            </div>
          ) : (
            <div className="bg-green-500/10 border-2 border-green-500 p-6 rounded-2xl text-center">
                <p className="text-green-500 font-black text-2xl">🎉 BIEN JOUÉ !</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                <button onClick={startNewGame} className="mt-4 bg-green-500 text-white font-bold py-2 px-6 rounded-full hover:bg-green-600 transition-colors">
                    REJOUER
                </button>
            </div>
          )}

          <div className="mt-10 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-widest">Tentatives précédentes</h4>
            {gameState.guesses.map((g, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl">
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? <Check className="text-green-500 w-5 h-5" /> : <X className="text-red-500 w-5 h-5" />}
              </div>
            ))}
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

export default BlindtestPage;
