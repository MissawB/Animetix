import React from 'react';
import { CheckCircle2, Trophy } from 'lucide-react';
import { useAchievements } from './hooks/useAchievements';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';

interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  rarity: string;
  xp_reward: number;
}

const AchievementsPage: React.FC = () => {
  const { t } = useTranslation();
  const { data: achievements, isLoading, isError } = useAchievements();

  if (isLoading) return (
    <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
        </div>
    </div>
  );

  if (isError || !achievements) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="manga-font text-5xl italic mb-2 tracking-tighter uppercase">
            📜 Grimoire des Hauts Faits
        </h1>
        <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Votre légende s'écrit à chaque secret découvert.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {achievements.map((ach: Achievement) => (
          <Card key={ach.id} padding="md" className={`${true ? 'bg-white' : 'bg-gray-50 opacity-70 grayscale'}`}>
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg ${true ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                <Trophy className="w-8 h-8" />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h5 className="manga-font text-sm uppercase leading-none">{ach.name}</h5>
                  <Badge variant="neutral" className="text-[8px]">{ach.rarity}</Badge>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 font-medium">{ach.description}</p>
                <div className="text-green-600 font-black text-[10px] flex items-center uppercase tracking-tighter">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> {true ? "Débloqué" : `Verrouillé (+${ach.xp_reward} XP)`}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AchievementsPage;
