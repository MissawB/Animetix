import React from 'react';
import { Target, Trophy, RotateCcw, AlertTriangle } from 'lucide-react';
import { useMachine } from '@xstate/react';
import { paradoxMachine } from './machines/paradoxMachine';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

const ParadoxGamePage: React.FC = () => {
  const [state, send] = useMachine(paradoxMachine);
  const { gameState } = state.context;

  const isLoading = state.matches('initializing') || state.matches('submitting');

  if (isLoading) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-[0.3em]">Ouverture d'une faille temporelle...</div>;
  
  if (state.matches('error')) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
           <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6" />
           <h2 className="text-2xl font-black text-red-500 mb-4 italic">PARADOXE INSTABLE</h2>
           <p className="mb-8 opacity-60 font-bold">La connexion au flux sémantique a été rompue.</p>
           <Button variant="danger" onClick={() => send({ type: 'RESTART' })}>RÉINITIALISER LE FLUX</Button>
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

      {state.matches('gameOver') ? (
        <div className="max-w-2xl mx-auto text-center">
          <Card padding="lg" className="border-4 border-green-500">
            <Trophy className="w-20 h-20 text-green-500 mx-auto mb-6 animate-bounce" />
            <h2 className="text-4xl font-black mb-4">ANOMALIE RÉSOLUE !</h2>
            <p className="text-xl mb-8 opacity-70">Vous avez démasqué l'intrus avec une précision chirurgicale.</p>
            <Button variant="success" size="lg" className="mx-auto" onClick={() => send({ type: 'RESTART' })}>
                <RotateCcw className="w-5 h-5" /> REJOUER
            </Button>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {gameState.items.map((item: any) => (
            <div 
                key={item.id} 
                onClick={() => send({ type: 'GUESS', itemId: item.id })}
                className="group relative bg-white dark:bg-navy-800 rounded-[2.5rem] overflow-hidden shadow-xl cursor-pointer transition-all hover:scale-105 hover:shadow-2xl border-4 border-transparent hover:border-red-500/50"
            >
                <img src={item.image} className="w-full h-80 object-cover grayscale group-hover:grayscale-0 transition-all duration-700" alt={item.title} />
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
