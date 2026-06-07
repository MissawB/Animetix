import React, { useState } from 'react';
import { Send, Trophy, Sparkles } from 'lucide-react';
import { useEmoji } from '../../features/games/hooks/useEmoji';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";

import { useTranslation } from 'react-i18next';
import { EmojiState } from "../../types";

const EmojiPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, loading, handleGuess } = useEmoji() as unknown as {
    gameState: EmojiState | undefined;
    loading: boolean;
    handleGuess: (arg: { guess: string }) => Promise<void>;
  };
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
    
      <div className="max-w-4xl mx-auto p-6 text-center py-16">
        <h2 className="text-5xl font-black italic manga-font mb-12 tracking-tighter uppercase">
          EMOJI <span className="text-orange-500">DECODE</span>
        </h2>
        
        <Card padding="lg" className="bg-gradient-to-r from-orange-500 to-red-600 mb-12 text-white border-none relative overflow-hidden group">
          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          <div className="text-6xl md:text-8xl tracking-[0.5em] mb-6 flex justify-center drop-shadow-lg">
              {gameState.emojis}
          </div>
          <p className="font-black italic text-sm uppercase tracking-widest opacity-80 flex items-center justify-center gap-2">
              <Sparkles className="w-4 h-4" /> L'IA a résumé une œuvre. Saurez-vous la retrouver ?
          </p>
        </Card>

        {!gameState.gameOver ? (
          <div className="max-w-md mx-auto space-y-4">
            <Input 
              value={guess} 
              onChange={(e) => setGuess(e.target.value)}
              placeholder="Tapez votre proposition..."
              className="text-center"
            />
            <Button variant="primary" size="lg" fullWidth onClick={onSubmit} className="bg-black text-white hover:bg-gray-900 border-none">
              <Send className="w-5 h-5" /> DEVINER
            </Button>
          </div>
        ) : (
          <Card padding="lg" className="bg-green-500 text-white mb-12 border-4 border-white/20">
            <Trophy className="w-16 h-16 mx-auto mb-4" />
            <h3 className="text-5xl font-black italic manga-font mb-2 uppercase">VICTOIRE !</h3>
            <p className="text-2xl font-bold">C'était : <span className="text-yellow-200">{gameState.secret_title}</span></p>
            <Button variant="success" className="mt-8 bg-white text-green-600 border-none px-12" onClick={() => window.location.reload()}>
              REJOUER
            </Button>
          </Card>
        )}

        <div className="max-w-2xl mx-auto space-y-4 mt-12">
          <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em] mb-6">Tes tentatives</h4>
          {gameState.guesses.map((g: { title: string; title_en?: string; image: string; is_correct: boolean }, i: number) => (
            <Card key={i} padding="sm" className="flex items-center transition-all hover:scale-[1.02]">
              <img src={g.image} className="w-14 h-20 object-cover rounded-2xl shadow-md border-2 border-surface-text/10" alt="" />
              <div className="flex-grow text-left ml-6">
                <div className="font-black text-lg truncate uppercase italic manga-font leading-none mb-2">{g.title_en || g.title}</div>
                <Badge variant={g.is_correct ? 'success' : 'danger'}>
                    {g.is_correct ? 'TROUVÉ' : 'ÉCHEC'}
                </Badge>
              </div>
              <div className="text-3xl px-4">{g.is_correct ? '✅' : '❌'}</div>
            </Card>
          ))}
        </div>
      </div>
    
  );
};

export default EmojiPage;


