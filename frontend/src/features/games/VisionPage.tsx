import React, { useEffect } from 'react';
import { Search, Eye, Trophy } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useVisionStore } from './stores/visionStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';

const visionSchema = z.object({
  description: z.string().min(3, "Veuillez entrer au moins 3 caractères pour l'analyse.").max(200, "La description est trop longue."),
});

type VisionFormValues = z.infer<typeof visionSchema>;

const VisionPage: React.FC = () => {
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useVisionStore();
  
  useEffect(() => {
    loadGame();
  }, [loadGame]);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<VisionFormValues>({
    resolver: zodResolver(visionSchema),
    defaultValues: { description: '' }
  });

  const onSubmit = async (data: VisionFormValues) => {
    submitGuess(data.description);
    reset();
  };

  if (isLoading) return <div className="text-center py-20 text-white font-black animate-pulse">ANALYSE VISIONNAIRE EN COURS...</div>;
  
  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
           <h2 className="text-2xl font-black text-red-500 mb-4 italic">SYSTÈME OPTIQUE DÉFAILLANT</h2>
           <p className="mb-8 opacity-60 font-bold">{error}</p>
           <Button variant="danger" onClick={restartGame}>RÉINITIALISER LE SCAN</Button>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-5xl font-black italic manga-font mb-12 text-center">
        VISION <span className="text-blue-500">QUEST</span>
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-start">
        {/* IMAGE */}
        <div className="flex flex-col items-center sticky top-24">
          <Card padding="sm" className="relative group overflow-hidden transition-all hover:scale-[1.02]">
            <img 
                src={gameState.image_url} 
                className="rounded-[2rem] shadow-lg w-full transition-all duration-1000" 
                style={{ filter: gameState.gameOver ? 'none' : `blur(${Math.max(0, 20 - gameState.best_score / 5)}px)` }} 
                alt="Target" 
            />
            <div className="absolute top-8 right-8 bg-black/60 backdrop-blur-md px-6 py-2 rounded-full border border-white/20">
                <span className="text-3xl font-black text-white">{Math.round(gameState.best_score)}%</span>
            </div>
          </Card>
          
          {gameState.gameOver && (
            <div className="mt-8 text-center bg-green-500 text-white p-8 rounded-[2.5rem] shadow-xl border-4 border-white/20 animate-bounce">
                <Trophy className="w-12 h-12 mx-auto mb-3" />
                <h3 className="text-2xl font-black">{gameState.secret_title}</h3>
                <Button variant="outline" className="mt-4 bg-white text-green-600 border-none" onClick={restartGame}>REJOUER</Button>
            </div>
          )}
        </div>

        {/* RECHERCHE */}
        <Card padding="lg">
          {!gameState.gameOver && (
            <form onSubmit={handleSubmit(onSubmit)} className="mb-12 flex flex-col gap-4">
              <h2 className="text-xs font-black uppercase opacity-40 mb-2 tracking-[0.2em] flex items-center gap-2">
                  <Eye className="w-4 h-4" /> Décrivez ce que vous voyez
              </h2>
              
              <Input 
                {...register('description')}
                error={errors.description?.message}
                placeholder="Ex: Un guerrier aux cheveux noirs..."
              />
              
              <Button type="submit" variant="primary" size="lg" fullWidth>
                <Search className="w-5 h-5" /> ANALYSER L'IMAGE
              </Button>
            </form>
          )}

          <div className="space-y-4">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-widest mb-4">Journal d'analyse</h4>
            {gameState.guesses.map((g: any, i: number) => (
              <div key={i} className="p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex justify-between items-center group hover:bg-blue-500/10 transition-colors border border-gray-100 dark:border-white/5">
                <span className="font-bold opacity-80">{g.text}</span>
                <Badge variant="primary">{Math.round(g.score)}%</Badge>
              </div>
            ))}
            {gameState.guesses.length === 0 && <p className="text-center py-10 opacity-20 italic">Aucune analyse effectuée pour le moment.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default VisionPage;
