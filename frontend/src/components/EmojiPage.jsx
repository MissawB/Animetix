import React, { useState, useEffect } from 'react';

const EmojiPage = () => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [guess, setGuess] = useState('');

  const fetchState = async () => {
    try {
      const res = await fetch('/api/v1/game/emoji/state/');
      if (!res.ok) throw new Error('No game in progress');
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error loading Emoji game:", err);
      startNewGame();
    }
  };

  const startNewGame = async () => {
    try {
      const res = await fetch('/api/v1/game/emoji/start/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error starting Emoji game:", err);
    }
  };

  const handleGuess = async () => {
    try {
      const res = await fetch('/api/v1/game/emoji/guess/', {
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

  if (loading) return <div className="text-center py-20">Chargement du jeu...</div>;

  return (
    <div className="text-center p-6">
      <h2 className="text-4xl manga-font mb-8">🎭 Emoji Decode</h2>
      
      <div className="bg-gradient-to-r from-orange-500 to-red-500 p-10 rounded-[3rem] shadow-2xl mb-10 text-white">
        <div className="text-8xl tracking-[1em] mb-4">{gameState.emojis}</div>
        <p className="font-bold italic">L'IA a résumé une œuvre en 5 emojis. Saurez-vous la retrouver ?</p>
      </div>

      {!gameState.game_over ? (
        <div className="max-w-md mx-auto space-y-4">
          <input 
            type="text" 
            value={guess} 
            onChange={(e) => setGuess(e.target.value)}
            className="form-control" 
            placeholder="Tapez votre proposition..."
          />
          <button onClick={handleGuess} className="btn btn-primary w-full">Deviner</button>
        </div>
      ) : (
        <div className="p-8 rounded-[3rem] bg-green-500 text-white mb-10">
          <h3 className="text-4xl mb-2">🎉 VICTOIRE !</h3>
          <p className="text-xl">C'était : <strong>{gameState.secret_title}</strong></p>
          <button onClick={startNewGame} className="btn btn-light mt-4">Rejouer</button>
        </div>
      )}

      <div className="max-w-2xl mx-auto space-y-4">
        {gameState.guesses.map((g, i) => (
          <div key={i} className="flex items-center p-4 rounded-3xl bg-gray-100 shadow-sm">
            <img src={g.image} className="w-12 h-16 object-cover rounded-xl me-4" alt="" />
            <div className="flex-grow text-start">
              <div className="font-bold">{g.title_en || g.title}</div>
            </div>
            <div className="text-2xl">{g.is_correct ? '✅' : '❌'}</div>
          </div>
        ))}
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

export default EmojiPage;
