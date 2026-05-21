import React, { useState, useEffect } from 'react';

const VisionPage = () => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [description, setDescription] = useState('');

  const fetchState = async () => {
    try {
      const res = await fetch('/api/v1/game/vision/state/');
      if (!res.ok) throw new Error('No game in progress');
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error loading Vision Quest:", err);
      startNewGame();
    }
  };

  const startNewGame = async () => {
    try {
      const res = await fetch('/api/v1/game/vision/start/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      const json = await res.json();
      setGameState(json);
      setLoading(false);
    } catch (err) {
      console.error("Error starting Vision Quest:", err);
    }
  };

  const submitGuess = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/game/vision/guess/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ description })
      });
      if (res.ok) {
        setDescription('');
        fetchState();
      }
    } catch (err) {
      console.error("Error submitting description:", err);
    }
  };

  useEffect(() => { fetchState(); }, []);

  if (loading) return <div className="text-center py-20">Initialisation de la vision...</div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        {/* IMAGE */}
        <div className="flex flex-col items-center">
          <img 
            src={gameState.image_url} 
            className="rounded-3xl shadow-2xl" 
            style={{ filter: gameState.game_over ? 'none' : `blur(${Math.max(0, 20 - gameState.best_score / 5)}px)` }} 
            alt="Target" 
          />
          <div className="text-4xl font-bold mt-4">{Math.round(gameState.best_score)}%</div>
          {gameState.game_over && <h3 className="text-primary mt-2">{gameState.secret_title}</h3>}
        </div>

        {/* RECHERCHE */}
        <div className="card p-6 shadow-xl rounded-3xl">
          {!gameState.game_over && (
            <form onSubmit={submitGuess} className="mb-8">
              <input 
                type="text" 
                value={description} 
                onChange={(e) => setDescription(e.target.value)}
                className="form-control mb-4" 
                placeholder="Décrivez l'image..."
                required
              />
              <button type="submit" className="btn btn-primary w-full">Analyser</button>
            </form>
          )}

          <div className="space-y-4">
            {gameState.guesses.map((g, i) => (
              <div key={i} className="p-3 border rounded-xl flex justify-between">
                <span>{g.text}</span>
                <span className="font-bold">{Math.round(g.score)}%</span>
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

export default VisionPage;
