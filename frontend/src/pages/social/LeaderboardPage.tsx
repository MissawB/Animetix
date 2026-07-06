import React from 'react';
import { Trophy, Medal, Crown, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLeaderboard } from '../../features/social/hooks/useLeaderboard';
import { Profile } from '../../types';
import { Badge } from "../../components/ui/Badge";
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from "../../components/ui/Skeleton";

// Podium accents for the top 3 (gold / silver / bronze).
// `icon` = vibrant colour for the medal (non-text, no contrast rule); `label` =
// AA-contrast colour for the rank text on the white/dark card.
const PODIUM = [
  { grad: 'from-yellow-400 to-amber-500', icon: 'text-yellow-500', label: 'text-yellow-700 dark:text-yellow-400', ring: 'ring-yellow-400/50', Icon: Crown, order: 'sm:order-2', lift: 'sm:-translate-y-4' },
  { grad: 'from-slate-300 to-slate-400', icon: 'text-slate-400', label: 'text-slate-600 dark:text-slate-300', ring: 'ring-slate-300/50', Icon: Medal, order: 'sm:order-1', lift: '' },
  { grad: 'from-orange-400 to-orange-600', icon: 'text-orange-500', label: 'text-orange-700 dark:text-orange-400', ring: 'ring-orange-400/50', Icon: Medal, order: 'sm:order-3', lift: '' },
];

const initial = (name: string) => (name?.[0] ?? '?').toUpperCase();

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

  const top3 = leaders.slice(0, 3);
  const rest = leaders.slice(3);

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] text-yellow-700 dark:text-yellow-400 mb-4">
          <Sparkles className="w-3.5 h-3.5" /> {t('social.leaderboard.world_ranking', 'Classement mondial')}
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase leading-none">
          <span className="bg-gradient-to-r from-yellow-500 via-amber-600 to-orange-600 dark:from-yellow-400 dark:via-amber-500 dark:to-orange-500 bg-clip-text text-transparent">
            {t('social.leaderboard.title')}
          </span>
        </h1>
        <p className="mt-4 text-sm font-bold text-gray-600 dark:text-gray-400">{t('social.leaderboard.subtitle', 'Les légendes qui ont décodé le plus de secrets.')}</p>
      </div>

      {leaders.length === 0 ? (
        <div className="text-center py-16 rounded-3xl border border-dashed border-gray-200 dark:border-white/10">
          <Trophy className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p className="font-bold text-gray-600 dark:text-gray-400">{t('social.leaderboard.empty', 'Le panthéon est encore vide. À toi d\'y entrer.')}</p>
        </div>
      ) : (
        <>
          {/* ── Podium (top 3) ───────────────────────────────────── */}
          <div className="flex flex-col sm:flex-row items-center sm:items-end justify-center gap-5 mb-10">
            {top3.map((player: Profile, index: number) => {
              const s = PODIUM[index];
              const Icon = s.Icon;
              return (
                <Link
                  key={player.username}
                  to={`/profile/${player.username}/`}
                  className={`group w-full sm:w-56 no-underline text-current ${s.order} ${s.lift}`}
                >
                  <div className="relative flex flex-col items-center rounded-3xl border border-gray-100 dark:border-white/10 bg-white dark:bg-navy-900 p-6 pt-8 shadow-lg transition-transform hover:-translate-y-1">
                    <div className="relative mb-4">
                      <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${s.grad} flex items-center justify-center text-3xl font-black italic text-white shadow-lg ring-4 ${s.ring}`}>
                        {initial(player.username)}
                      </div>
                      <Icon className={`absolute -top-3 -right-3 w-8 h-8 ${s.icon} drop-shadow`} aria-hidden="true" />
                    </div>
                    <div className={`text-[11px] font-black uppercase tracking-[0.2em] ${s.label} mb-1`}>#{index + 1}</div>
                    <div
                      className="font-black italic manga-font text-lg truncate max-w-full group-hover:text-yellow-500 transition-colors"
                      style={player.custom_username_color ? { color: player.custom_username_color } : undefined}
                    >
                      {player.username}
                    </div>
                    <div className="mt-2 font-black text-blue-600 dark:text-blue-400">{player.xp} XP</div>
                    <Badge variant="neutral">{t('social.profile.level', { level: player.level })}</Badge>
                  </div>
                </Link>
              );
            })}
          </div>

          {/* ── Reste du classement ──────────────────────────────── */}
          {rest.length > 0 && (
            <div className="space-y-3 max-w-3xl mx-auto">
              {rest.map((player: Profile, i: number) => (
                <Link
                  key={player.username}
                  to={`/profile/${player.username}/`}
                  className="flex items-center gap-4 rounded-2xl border border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-navy-900 px-5 py-4 no-underline text-current hover:border-yellow-500/40 hover:translate-x-1 transition-all"
                >
                  <span className="w-10 text-center font-black italic text-lg text-gray-500 dark:text-gray-400">#{i + 4}</span>
                  <div className="w-11 h-11 flex-shrink-0 rounded-xl bg-black dark:bg-white/10 flex items-center justify-center font-black italic text-white dark:text-yellow-400">
                    {initial(player.username)}
                  </div>
                  <span
                    className="flex-grow font-bold truncate group-hover:text-yellow-500 transition-colors"
                    style={player.custom_username_color ? { color: player.custom_username_color } : undefined}
                  >
                    {player.username}
                  </span>
                  <div className="flex flex-col items-end">
                    <span className="font-black text-blue-600 dark:text-blue-400">{player.xp} XP</span>
                    <Badge variant="neutral">{t('social.profile.level', { level: player.level })}</Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default LeaderboardPage;
