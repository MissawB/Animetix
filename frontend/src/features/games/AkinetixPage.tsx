import React from 'react';
import { Brain, History, Check, X, HelpCircle } from 'lucide-react';
import { useMachine } from '@xstate/react';
import { akinetixMachine } from './machines/akinetixMachine';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

import { CardSkeleton } from '../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';



const AkinetixPage: React.FC = () => {
  const { t } = useTranslation();
  const [state, send] = useMachine(akinetixMachine);
  const { gameState } = state.context;

  // Gestion des états de chargement basée sur la machine
  const isLoading = state.matches('initializing') || state.matches('submittingAnswer') || state.matches('confirming');

  if (isLoading) return (
    <div className="flex justify-center items-center py-12 px-6">
      <CardSkeleton />
    </div>
  );
  
  if (state.matches('error')) {
    return (
      
        <div className="flex justify-center items-center py-20">
          <Card padding="lg" className="text-center border-red-500/50">
             <h2 className="text-2xl font-black text-red-500 mb-4 tracking-tighter italic">CRITICAL ERROR</h2>
             <p className="mb-8 opacity-60 font-bold">L'IA du devin semble avoir perdu le contact.</p>
             <Button variant="danger" onClick={() => send({ type: 'RESTART' })}>RÉINITIALISER LE NOYAU</Button>
          </Card>
        </div>
      
    );
  }

  if (!gameState) return null;

  return (
    
      <div className="flex justify-center items-center py-12 px-6">
        <div className="max-w-3xl w-full text-center">
          <Card padding="lg">
            <h2 className="text-3xl font-black mb-8 flex items-center justify-center gap-3">
              <Brain className="w-8 h-8 text-yellow-400" /> {t('games.akinetix.title')}
            </h2>
            
            <div className="mb-6 text-left bg-gray-50 dark:bg-navy-900 p-6 rounded-2xl max-h-40 overflow-y-auto border border-gray-100 dark:border-white/5">
              <h4 className="text-xs font-black uppercase opacity-40 mb-3 flex items-center gap-2">
                  <History className="w-3 h-3" /> {t('games.akinetix.history')}
              </h4>
              {gameState.history.map((item: any, i: number) => (
                <div key={i} className="text-sm opacity-70 mb-2 border-l-2 border-yellow-400 pl-3">
                  <span className="font-bold text-yellow-500">IA :</span> {item.q} <span className="font-black italic ml-2">{item.a}</span>
                </div>
              ))}
            </div>

            <div className="text-2xl md:text-4xl mb-10 font-black text-blue-600 dark:text-blue-400 leading-tight">
              {gameState.gameOver ? t('games.akinetix.game_over', { guess: gameState.aiGuess }) : gameState.currentQuestion}
            </div>

            {!gameState.gameOver ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Button variant="success" onClick={() => send({ type: 'ANSWER', answer: 'OUI' })}>
                  <Check className="w-5 h-5" /> {t('common.yes')}
                </Button>
                <Button variant="danger" onClick={() => send({ type: 'ANSWER', answer: 'NON' })}>
                  <X className="w-5 h-5" /> {t('common.no')}
                </Button>
                <Button variant="secondary" onClick={() => send({ type: 'ANSWER', answer: 'PEUT-ÊTRE' })}>
                  <HelpCircle className="w-5 h-5" /> PEUT-ÊTRE
                </Button>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Button variant="primary" onClick={() => send({ type: 'CONFIRM', isCorrect: true })}>
                  {t('common.yes')}, BIEN JOUÉ !
                </Button>
                <Button variant="outline" onClick={() => send({ type: 'CONFIRM', isCorrect: false })}>
                  {t('common.no')}, ÉCHEC DE L'IA
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>
    
  );
};

export default AkinetixPage;
