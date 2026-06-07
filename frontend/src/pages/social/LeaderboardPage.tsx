import React from 'react';
import { Trophy, Medal } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLeaderboard } from '../../features/social/hooks/useLeaderboard';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from "../../components/ui/Skeleton";

const LeaderboardPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useLeaderboard();
  const leaders = Array.isArray(data) ? data : [];

  if (isLoading) return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <CardSkeleton />
    </div>
  );
  
  if (isError) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;
  if (!leaders) return null;

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-5xl font-black italic manga-font mb-12 text-center tracking-tighter uppercase">
        {t('social.leaderboard.title')}
      </h1>

      <Card padding="none" className="overflow-hidden">
        <div className="p-8">
          <table className="w-full text-left border-separate border-spacing-y-4">
            <thead>
              <tr className="text-[10px] font-black uppercase opacity-30 tracking-[0.2em]">
                <th className="pb-4 pl-6">{t('social.leaderboard.rank')}</th>
                <th className="pb-4">{t('social.leaderboard.player')}</th>
                <th className="pb-4 text-right pr-6">{t('social.leaderboard.xp_level')}</th>
              </tr>
            </thead>
            <tbody>
              {(leaders || []).map((player: any, index: number) => (
                <tr key={player.username} className="bg-gray-50 dark:bg-navy-900 transition-transform hover:scale-[1.01] border border-gray-100 dark:border-white/5">
                  <td className="py-5 pl-6 rounded-l-2xl">
                    <div className="flex items-center gap-3">
                      {index === 0 && <Trophy className="w-5 h-5 text-yellow-400" />}
                      {index === 1 && <Medal className="w-5 h-5 text-gray-400" />}
                      {index === 2 && <Medal className="w-5 h-5 text-orange-400" />}
                      <span className="font-black italic">#{index + 1}</span>
                    </div>
                  </td>
                  <td className="py-5">
                    <Link to={`/profile/${player.username}/`} className="flex items-center gap-4 no-underline text-current group">
                      <div className="w-10 h-10 bg-black dark:bg-white/10 rounded-xl flex items-center justify-center font-black italic text-white dark:text-yellow-400">
                        {player.username[0].toUpperCase()}
                      </div>
                      <span className="font-bold group-hover:text-yellow-500 transition-colors">{player.username}</span>
                    </Link>
                  </td>
                  <td className="py-5 text-right pr-6 rounded-r-2xl">
                    <div className="flex flex-col items-end">
                      <span className="font-black text-blue-600 dark:text-blue-400">{player.xp} XP</span>
                      <Badge variant="neutral">{t('social.profile.level', { level: player.level })}</Badge>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default LeaderboardPage;


