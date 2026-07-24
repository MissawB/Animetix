import React from 'react';
import { Trophy, Medal, Crown, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLeaderboard } from '../../features/social/hooks/useLeaderboard';
import { Profile } from '../../types';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';

// Podium accents for the top 3 — édition de nuit. L'or (kin) est la voix des
// données : il porte le rang #1, l'argent (papier) le #2, le graphite le #3.
// Aucun dégradé : l'aplat encre chaque marche d'une seule voix.
const PODIUM = [
  {
    avatar: 'bg-[#FDB913] text-[#0B0C10]',
    ring: 'ring-[#FDB913]/40',
    icon: 'text-[#FDB913]',
    label: 'text-[#FDB913]',
    Icon: Crown,
    order: 'sm:order-2',
    lift: 'sm:-translate-y-4',
  },
  {
    avatar: 'bg-[#F4F1E8] text-[#0B0C10]',
    ring: 'ring-[#F4F1E8]/30',
    icon: 'text-[#F4F1E8]',
    label: 'text-[#F4F1E8]',
    Icon: Medal,
    order: 'sm:order-1',
    lift: '',
  },
  {
    avatar: 'bg-[#8F94A5] text-[#0B0C10]',
    ring: 'ring-[#8F94A5]/30',
    icon: 'text-[#8F94A5]',
    label: 'text-[#8F94A5]',
    Icon: Medal,
    order: 'sm:order-3',
    lift: '',
  },
];

const initial = (name: string) => (name?.[0] ?? '?').toUpperCase();

const LevelPill: React.FC<{ level: number }> = ({ level }) => {
  const { t } = useTranslation();
  return (
    <span className="mt-1 inline-block rounded-full border border-[#F4F1E8]/10 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
      {t('social.profile.level', { level })}
    </span>
  );
};

const LeaderboardPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useLeaderboard();
  const leaders = Array.isArray(data) ? data : [];

  if (isLoading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError)
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-[#0B0C10] text-center">
        <p className="font-manga text-2xl font-black uppercase italic text-[#E8442B]">
          {t('common.error')}
        </p>
      </div>
    );

  const top3 = leaders.slice(0, 3);
  const rest = leaders.slice(3);

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-4xl px-6 py-16">
        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="relative mb-14 text-center">
          <div
            className="explore-halftone pointer-events-none absolute inset-x-0 -top-10 h-40"
            aria-hidden
          />
          <div className="relative mb-4 flex items-center justify-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              位
            </span>
            <span className="inline-flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              <Sparkles className="h-3.5 w-3.5" />{' '}
              {t('social.leaderboard.world_ranking', 'Classement mondial')}
            </span>
          </div>
          <h1 className="font-manga relative text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
            {t('social.leaderboard.title')}
          </h1>
          <p className="relative mt-4 text-sm leading-relaxed text-[#8F94A5]">
            {t('social.leaderboard.subtitle', 'Les légendes qui ont décodé le plus de secrets.')}
          </p>
        </div>

        {leaders.length === 0 ? (
          <div className="flex flex-col items-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-16 text-center">
            <Trophy className="mb-4 h-12 w-12 text-[#8F94A5]/30" />
            <p className="text-sm font-bold text-[#8F94A5]">
              {t('social.leaderboard.empty', "Le panthéon est encore vide. À toi d'y entrer.")}
            </p>
          </div>
        ) : (
          <>
            {/* ── Podium (top 3) ───────────────────────────────────── */}
            <div className="mb-10 flex flex-col items-center justify-center gap-5 sm:flex-row sm:items-end">
              {top3.map((player: Profile, index: number) => {
                const s = PODIUM[index];
                const Icon = s.Icon;
                return (
                  <Link
                    key={player.username}
                    to={`/profile/${player.username}/`}
                    className={`group w-full no-underline sm:w-56 ${s.order} ${s.lift}`}
                  >
                    <div className="relative flex flex-col items-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 pt-8 transition-transform hover:-translate-y-1">
                      <div className="relative mb-4">
                        <div
                          className={`flex h-20 w-20 items-center justify-center rounded-2xl text-3xl font-black italic ring-4 ${s.avatar} ${s.ring}`}
                        >
                          {initial(player.username)}
                        </div>
                        <Icon
                          className={`absolute -right-3 -top-3 h-8 w-8 ${s.icon}`}
                          aria-hidden="true"
                        />
                      </div>
                      <div
                        className={`mb-1 text-[11px] font-black uppercase tracking-[0.2em] ${s.label}`}
                      >
                        #{index + 1}
                      </div>
                      <div
                        className="font-manga max-w-full truncate text-lg font-black uppercase italic text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]"
                        style={
                          player.custom_username_color
                            ? { color: player.custom_username_color }
                            : undefined
                        }
                      >
                        {player.username}
                      </div>
                      <div className="mt-2 font-black italic text-[#FDB913]">{player.xp} XP</div>
                      <LevelPill level={player.level} />
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* ── Reste du classement ──────────────────────────────── */}
            {rest.length > 0 && (
              <div className="mx-auto max-w-3xl space-y-3">
                {rest.map((player: Profile, i: number) => (
                  <Link
                    key={player.username}
                    to={`/profile/${player.username}/`}
                    className="group flex items-center gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-5 py-4 no-underline transition-all hover:translate-x-1 hover:border-[#FDB913]/40"
                  >
                    <span className="w-10 text-center text-lg font-black italic text-[#8F94A5]">
                      #{i + 4}
                    </span>
                    <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] font-black italic text-[#F4F1E8]">
                      {initial(player.username)}
                    </div>
                    <span
                      className="flex-grow truncate font-bold text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]"
                      style={
                        player.custom_username_color
                          ? { color: player.custom_username_color }
                          : undefined
                      }
                    >
                      {player.username}
                    </span>
                    <div className="flex flex-col items-end">
                      <span className="font-black italic text-[#FDB913]">{player.xp} XP</span>
                      <LevelPill level={player.level} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default LeaderboardPage;
