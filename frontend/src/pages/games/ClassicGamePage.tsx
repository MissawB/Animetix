import React, { useState } from 'react';
import { Search, Zap, Trophy, HelpCircle, History } from 'lucide-react';
import { useClassicGame } from '../../features/games/hooks/useClassicGame';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Badge } from '../../../components/ui/Badge';
import { CardSkeleton } from '../../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

const ClassicGamePage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, loading, handleGuess } = useClassicGame();
  const [guess, setGuess] = useState<string>('');

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
    
      <div className="max-w-5xl mx-auto px-6 py-16">
        <h1 className="text-5xl font-black italic manga-font mb-12 text-center tracking-tighter uppercase">
          CLASSIC <span className="text-blue-500">QUEST</span>
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Game Area */}
          <div className="lg:col-span-2 space-y-8">
              <Card padding="lg">
                  {!gameState.gameOver ? (
                      <form onSubmit={onSubmit} className="space-y-6">
                          <div className="flex items-center gap-4 text-xs font-black uppercase opacity-40 mb-2">
                              <Zap className="w-4 h-4 text-yellow-500" /> Devinez l'œuvre mystère
                          </div>
                          <Input 
                              value={guess} 
                              onChange={(e) => setGuess(e.target.value)}
                              placeholder="Entrez un titre..."
                              required
                          />
                          <Button type="submit" variant="primary" size="lg" fullWidth>
                              <Search className="w-6 h-6" /> ENVOYER
                          </Button>
                      </form>
                  ) : (
                      <div className="text-center py-10 bg-green-500/10 border-4 border-green-500 rounded-[2.5rem]">
                          <Trophy className="w-20 h-20 text-green-500 mx-auto mb-6" />
                          <h2 className="text-4xl font-black text-green-600 mb-2">VICTOIRE !</h2>
                          <p className="text-xl font-bold opacity-70 mb-8">C'était bien {gameState.secret_title}</p>
                          <Button variant="success" className="mx-auto" onClick={() => window.location.reload()}>
                              REJOUER
                          </Button>
                      </div>
                  )}
              </Card>

              {/* History */}
              <Card padding="md">
                  <h3 className="text-xs font-black uppercase opacity-30 mb-8 tracking-widest flex items-center gap-2">
                      <History className="w-4 h-4" /> Historique des tentatives
                  </h3>
                  <div className="space-y-4">
                      {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
                          <div key={i} className={`p-4 rounded-2xl flex items-center justify-between transition-all ${g.is_correct ? 'bg-green-500 text-white shadow-green-500/20' : 'bg-gray-50 dark:bg-navy-900 border border-gray-100 dark:border-white/5'}`}>
                              <span className="font-bold">{g.title}</span>
                              <Badge variant={g.is_correct ? 'success' : 'danger'}>
                                  {g.is_correct ? 'TROUVÉ' : 'FAUX'}
                              </Badge>
                          </div>
                      ))}
                      {gameState.guesses.length === 0 && <p className="text-center py-10 opacity-20 italic">Aucune tentative. Lancez-vous !</p>}
                  </div>
              </Card>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-8">
              <Card padding="md" className="bg-brand-primary text-white border-none relative overflow-hidden group shadow-brand-primary/20">
                  <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:rotate-12 transition-transform">
                      <HelpCircle className="w-32 h-32" />
                  </div>
                  <h4 className="font-black italic text-xl mb-4 uppercase">Besoin d'aide ?</h4>
                  <p className="text-sm opacity-80 leading-relaxed mb-6 font-bold">
                      Utilisez vos indices judicieusement. Chaque indice révélé diminue votre récompense finale en XP.
                  </p>
                  <div className="space-y-3">
                      <Button variant="outline" fullWidth size="sm" className="bg-white/10 border-white/20 text-white hover:bg-white/20">RÉVÉLER UN INDICE (-5 XP)</Button>
                      <Button variant="outline" fullWidth size="sm" className="bg-white/10 border-white/20 text-white hover:bg-white/20">VOIR LE SYNOPSIS (-10 XP)</Button>
                  </div>
              </Card>
          </div>
        </div>
      </div>
    
  );
};

export default ClassicGamePage;

