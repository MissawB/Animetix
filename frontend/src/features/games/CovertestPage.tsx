import React, { useState } from 'react';
import { ImageIcon, Send, RotateCcw } from 'lucide-react';
import { useCovertest } from './hooks/useCovertest';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

const CovertestPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, loading, handleGuess } = useCovertest();
  const [guess, setGuess] = useState<string>('');

  const onSubmit = async () => {
    await handleGuess({ guess });
    setGuess('');
  };

  if (loading) return (
    <div className="flex justify-center items-center py-12 px-6">
      <CardSkeleton />
    </div>
  );
  
  if (!gameState) return null;

  return (
    
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Couverture */}
          <div className="relative group">
            <div className="absolute -inset-4 bg-gradient-to-tr from-yellow-400 to-orange-500 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity"></div>
            <img src={gameState.cover_url} className={`relative w-full rounded-[2.5rem] shadow-2xl transition-all duration-700 ${!gameState.gameOver ? 'blur-2xl' : 'blur-0 scale-105'}`} alt="Couverture" />
            {!gameState.gameOver && (
              <div className="absolute inset-0 flex items-center justify-center">
                  <div className="bg-black/60 backdrop-blur-md p-6 rounded-full border-2 border-white/20">
                      <ImageIcon className="w-12 h-12 text-white opacity-50" />
                  </div>
              </div>
            )}
          </div>
          
          {/* Jeu */}
          <Card padding="lg">
            <h2 className="text-4xl font-black italic manga-font mb-10 tracking-tighter uppercase">
              COVER <span className="text-yellow-400">QUEST</span>
            </h2>

            {gameState.gameOver ? (
              <div className="text-center py-8">
                  <h3 className="text-4xl font-black text-green-500 mb-2 uppercase italic manga-font">TROUVÉ !</h3>
                  <p className="text-2xl font-bold text-gray-800 dark:text-white mb-8">{gameState.secret_title}</p>
                  <Button variant="primary" className="mx-auto px-12 py-4 italic" onClick={() => window.location.reload()}>
                      <RotateCcw className="w-5 h-5" /> REJOUER
                  </Button>
              </div>
            ) : (
              <div className="space-y-6">
                <Input 
                  value={guess} 
                  onChange={(e) => setGuess(e.target.value)}
                  placeholder="Quel manga est-ce ?"
                />
                <Button variant="primary" size="lg" fullWidth onClick={onSubmit}>
                  <Send className="w-5 h-5" /> DEVINER
                </Button>
              </div>
            )}

            <div className="mt-12 space-y-3">
              <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-4">Journal des tentatives</h4>
              {gameState.guesses.map((g: any, i: number) => (
                <div key={i} className={`flex items-center justify-between p-4 rounded-2xl border-l-4 transition-all ${g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
                  <span className="font-bold">{g.title}</span>
                  <Badge variant={g.is_correct ? 'success' : 'danger'}>
                      {g.is_correct ? 'CORRECT' : 'FAUX'}
                  </Badge>
                </div>
              ))}
              {gameState.guesses.length === 0 && <p className="text-center py-6 opacity-20 italic">Aucune tentative pour le moment.</p>}
            </div>
          </Card>
        </div>
      </div>
    
  );
};

export default CovertestPage;
