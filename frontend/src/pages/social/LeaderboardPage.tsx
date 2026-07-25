import React from 'react';
import { Trophy, Medal, Crown, Sparkles, Users, Flame, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLeaderboard } from '../../features/social/hooks/useLeaderboard';
import { Profile } from '../../types';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Avatar } from '../../components/ui/Avatar';

// Podium accents for the top 3 — édition de nuit. L'or (kin) est la voix des
// données : il porte le rang #1, l'argent (papier) le #2, le graphite le #3.
// Aucun dégradé : l'aplat encre chaque marche d'une seule voix.
const PODIUM = [
  {
    avatar: 'bg-[#FDB913] text-[#0B0C10]',
    ring: 'ring-[#FDB913]/40',
    icon: 'text-[#FDB913]',
    label: 'text-[#FDB913]',
    bar: 'bg-[#FDB913]',
    glow: 'shadow-[0_0_45px_-8px_rgba(253,185,19,0.7)]',
    Icon: Crown,
    order: 'sm:order-2',
    lift: 'sm:-translate-y-4',
  },
  {
    avatar: 'bg-[#F4F1E8] text-[#0B0C10]',
    ring: 'ring-[#F4F1E8]/30',
    icon: 'text-[#F4F1E8]',
    label: 'text-[#F4F1E8]',
    bar: 'bg-[#F4F1E8]',
    glow: '',
    Icon: Medal,
    order: 'sm:order-1',
    lift: '',
  },
  {
    avatar: 'bg-[#8F94A5] text-[#0B0C10]',
    ring: 'ring-[#8F94A5]/30',
    icon: 'text-[#8F94A5]',
    label: 'text-[#8F94A5]',
    bar: 'bg-[#8F94A5]',
    glow: '',
    Icon: Medal,
    order: 'sm:order-3',
    lift: '',
  },
];

const LevelPill: React.FC<{ level: number }> = ({ level }) => {
  const { t } = useTranslation();
  return (
    <span className="mt-1 inline-block rounded-full border border-[#F4F1E8]/10 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
      {t('social.profile.level', { level })}
    </span>
  );
};

/** Tuile de mesure — voix données (or). La valeur est déjà formatée en amont. */
const StatTile: React.FC<{
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  delay: number;
  mounted: boolean;
}> = ({ icon, value, label, delay, mounted }) => (
  <div
    className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-5 py-4 transition-all duration-500 ease-out"
    style={{
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'none' : 'translateY(10px)',
      transitionDelay: `${delay}ms`,
    }}
  >
    <div className="mb-2 flex items-center gap-2 text-[#8F94A5]">
      {icon}
      <span className="text-[9px] font-black uppercase tracking-[0.22em]">{label}</span>
    </div>
    <p className="font-manga text-2xl font-black italic leading-none text-[#FDB913]">{value}</p>
  </div>
);

/** Barre d'XP relative au champion — se remplit au montage. */
const XpBar: React.FC<{ pct: number; color: string; mounted: boolean; delay: number }> = ({
  pct,
  color,
  mounted,
  delay,
}) => (
  <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
    <div
      className={`h-full rounded-full ${color}`}
      style={{
        width: mounted ? `${pct}%` : '0%',
        transition: 'width 900ms cubic-bezier(0.22,1,0.36,1)',
        transitionDelay: `${delay}ms`,
      }}
    />
  </div>
);

const LeaderboardPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useLeaderboard();
  const leaders = Array.isArray(data) ? data : [];

  // Déclenche les animations d'entrée / remplissage après le premier rendu.
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

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

  // Statistiques dérivées du classement (voix données). Le classement est trié
  // par points classés : on prend le max d'XP pour l'échelle des barres afin
  // qu'elles restent parlantes quel que soit l'ordre.
  const championXp = leaders.reduce((max, p) => Math.max(max, p.xp ?? 0), 0);
  const totalXp = leaders.reduce((sum, p) => sum + (p.xp ?? 0), 0);
  const maxLevel = leaders.reduce((max, p) => Math.max(max, p.level ?? 0), 0);
  const fmt = (n: number) => n.toLocaleString('fr-FR');
  const relPct = (xp: number) => (championXp > 0 ? Math.max(4, (xp / championXp) * 100) : 0);

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-4xl px-6 py-16">
        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="relative mb-12 text-center">
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
            {/* ── Tuiles de statistiques ───────────────────────────── */}
            <div className="mb-12 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatTile
                icon={<Users className="h-3.5 w-3.5" />}
                value={fmt(leaders.length)}
                label={t('social.leaderboard.stat_ranked', 'Légendes classées')}
                delay={0}
                mounted={mounted}
              />
              <StatTile
                icon={<Crown className="h-3.5 w-3.5" />}
                value={fmt(championXp)}
                label={t('social.leaderboard.stat_champion', 'XP du champion')}
                delay={60}
                mounted={mounted}
              />
              <StatTile
                icon={<Flame className="h-3.5 w-3.5" />}
                value={fmt(totalXp)}
                label={t('social.leaderboard.stat_total', 'XP cumulé')}
                delay={120}
                mounted={mounted}
              />
              <StatTile
                icon={<TrendingUp className="h-3.5 w-3.5" />}
                value={fmt(maxLevel)}
                label={t('social.leaderboard.stat_maxlevel', 'Niveau max')}
                delay={180}
                mounted={mounted}
              />
            </div>

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
                    style={{
                      opacity: mounted ? 1 : 0,
                      transform: mounted ? undefined : 'translateY(14px)',
                      transition: 'opacity 500ms ease-out, transform 500ms ease-out',
                      transitionDelay: `${index * 90}ms`,
                    }}
                  >
                    <div
                      className={`relative flex flex-col items-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 pt-8 transition-transform hover:-translate-y-1 ${s.glow}`}
                    >
                      <div className="relative mb-4">
                        {index === 0 && (
                          <span
                            className="absolute inset-0 animate-ping rounded-2xl bg-[#FDB913]/20 motion-reduce:animate-none"
                            aria-hidden
                          />
                        )}
                        <Avatar
                          src={player.avatar}
                          name={player.username}
                          className={`relative h-20 w-20 rounded-2xl text-3xl font-black italic ring-4 ${s.ring}`}
                          fallbackClassName={s.avatar}
                        />
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
                      <div className="mt-4 w-full">
                        <XpBar
                          pct={relPct(player.xp)}
                          color={s.bar}
                          mounted={mounted}
                          delay={200 + index * 90}
                        />
                      </div>
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
                    style={{
                      opacity: mounted ? 1 : 0,
                      transform: mounted ? undefined : 'translateY(10px)',
                      transition: 'opacity 450ms ease-out, transform 450ms ease-out',
                      transitionDelay: `${Math.min(i, 12) * 45}ms`,
                    }}
                  >
                    <span className="w-10 text-center text-lg font-black italic text-[#8F94A5]">
                      #{i + 4}
                    </span>
                    <Avatar
                      src={player.avatar}
                      name={player.username}
                      className="h-11 w-11 flex-shrink-0 rounded-xl border border-[#F4F1E8]/10 font-black italic"
                      fallbackClassName="bg-[#0B0C10] text-[#F4F1E8]"
                    />
                    <div className="flex min-w-0 flex-grow flex-col gap-1.5">
                      <span
                        className="truncate font-bold text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]"
                        style={
                          player.custom_username_color
                            ? { color: player.custom_username_color }
                            : undefined
                        }
                      >
                        {player.username}
                      </span>
                      <XpBar
                        pct={relPct(player.xp)}
                        color="bg-[#FDB913]/70"
                        mounted={mounted}
                        delay={120 + Math.min(i, 12) * 45}
                      />
                    </div>
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
