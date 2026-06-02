import React, { useState, useRef, useEffect } from 'react';
import { Play, Check, X, Music } from 'lucide-react';
import { useBlindtestStore } from './stores/blindtestStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

const BlindtestPage: React.FC = () => {
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useBlindtestStore();
  const [guess, setGuess] = useState<string>('');
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  const onSubmit = async () => {
    submitGuess(guess);
    setGuess('');
  };

  if (isLoading) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-widest">Récupération de l'audio...</div>;
  
  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
           <h2 className="text-2xl font-black text-red-500 mb-4 italic">SIGNAL PERDU</h2>
           <p className="mb-8 opacity-60 font-bold">{error}</p>
           <Button variant="danger" onClick={restartGame}>RECONNEXION</Button>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* LECTEUR */}
        <Card padding="md">
          {gameState.gameOver ? (
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
        </Card>

        {/* JEU */}
        <Card padding="lg">
          <h2 className="text-3xl font-black mb-8 flex items-center gap-3 italic">
              <Music className="w-8 h-8 text-yellow-400" /> DÉCOUVREZ L'ANIMÉ
          </h2>
          {!gameState.gameOver ? (
            <div className="space-y-6">
              <input 
                type="text" 
                value={guess} 
                onChange={(e) => setGuess(e.target.value)}
                className="w-full p-4 rounded-2xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold" 
                placeholder="Titre de l'animé..."
              />
              <Button variant="primary" fullWidth onClick={onSubmit}>
                VALIDER MA RÉPONSE
              </Button>
            </div>
          ) : (
            <div className="bg-green-500/10 border-2 border-green-500 p-6 rounded-2xl text-center">
                <p className="text-green-500 font-black text-2xl animate-bounce">🎉 BIEN JOUÉ !</p>
                <p className="text-xl font-bold mt-2">C'était : <span className="text-yellow-500">{gameState.secret_title}</span></p>
                <Button variant="success" className="mt-6" onClick={restartGame}>
                    REJOUER
                </Button>
            </div>
          )}

          <div className="mt-10 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-widest">Tentatives précédentes</h4>
            {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-gray-100 dark:border-white/5">
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? <Check className="text-green-500 w-5 h-5" /> : <X className="text-red-500 w-5 h-5" />}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default BlindtestPage;
