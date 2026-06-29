import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Target, Trophy, RotateCcw, AlertTriangle, Lock, Zap } from 'lucide-react';
import { useParadoxStore } from '../../features/games/stores/paradoxStore';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

const ParadoxGamePage: React.FC = () => {
  const { gameState, isLoading, error, errorKind, loadGame, submitGuess } = useParadoxStore();

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  if (isLoading) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-[0.3em]">Ouverture d'une faille temporelle...</div>;

  if (error && errorKind === 'auth') {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-indigo-500/50 max-w-md">
          <Lock className="w-16 h-16 text-indigo-400 mx-auto mb-6" />
          <h2 className="text-2xl font-black text-indigo-300 mb-4 italic">CONNEXION REQUISE</h2>
          <p className="mb-8 opacity-70 font-bold">{error}</p>
          <Link to="/auth/login/">
            <Button variant="primary" className="mx-auto">Se connecter</Button>
          </Link>
        </Card>
      </div>
    );
  }

  if (error && errorKind === 'payment') {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-amber-500/50 max-w-md">
          <Zap className="w-16 h-16 text-amber-400 mx-auto mb-6" />
          <h2 className="text-2xl font-black text-amber-300 mb-4 italic">BERRIX INSUFFISANTS</h2>
          <p className="mb-8 opacity-70 font-bold">{error}</p>
          <div className="flex gap-3 justify-center">
            <Link to="/power-station/">
              <Button variant="primary" className="mx-auto">Recharger des Berrix</Button>
            </Link>
            <Button variant="ghost" onClick={loadGame}>Réessayer</Button>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
           <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6" />
           <h2 className="text-2xl font-black text-red-500 mb-4 italic">PARADOXE INSTABLE</h2>
           <p className="mb-8 opacity-60 font-bold">{error}</p>
           <Button variant="danger" onClick={loadGame}>RÉINITIALISER LE FLUX</Button>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-5xl font-black italic manga-font mb-4 text-center tracking-tighter">
        PARADOX <span className="text-red-500">INTRUDER</span>
      </h1>
      <p className="text-center text-gray-500 font-bold uppercase tracking-widest mb-12">Démasquez l'anomalie sémantique</p>

      {gameState.gameOver ? (
        <div className="max-w-2xl mx-auto text-center">
          <Card padding="lg" className="border-4 border-green-500">
            <Trophy className="w-20 h-20 text-green-500 mx-auto mb-6 animate-bounce" />
            <h2 className="text-4xl font-black mb-4">ANOMALIE RÉSOLUE !</h2>
            <p className="text-xl mb-8 opacity-70">Vous avez démasqué l'intrus avec une précision chirurgicale.</p>
            <Button variant="success" size="lg" className="mx-auto" onClick={loadGame}>
                <RotateCcw className="w-5 h-5" /> REJOUER
            </Button>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {gameState.items.map((item) => (
            <div 
                key={item.id} 
                onClick={() => submitGuess(item.id)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        submitGuess(item.id);
                    }
                }}
                role="button"
                tabIndex={0}
                aria-label={`Sélectionner ${item.title}`}
                className="group relative bg-white dark:bg-navy-800 rounded-[2.5rem] overflow-hidden shadow-xl cursor-pointer transition-all hover:scale-105 hover:shadow-2xl border-4 border-transparent hover:border-red-500/50"
            >
                <img src={item.image} className="w-full h-80 object-cover grayscale group-hover:grayscale-0 transition-all duration-700" alt={item.title} loading="lazy" decoding="async" />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
                <div className="absolute bottom-6 left-6 right-6 text-center">
                    <h3 className="text-white font-black italic manga-font text-xl leading-none mb-2">{item.title}</h3>
                    <div className="flex items-center justify-center gap-2 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Target className="w-4 h-4" />
                        <span className="text-[10px] font-black uppercase">ÉLIMINER L'ANOMALIE</span>
                    </div>
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ParadoxGamePage;


