import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Skull, Trophy, Zap } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { apiClient } from '../../utils/apiClient';
import { useAuthStore } from '../../store/authStore';
import {
  useWorldBossRun,
  type BossQuestion,
} from '../../features/games/world_boss/useWorldBossRun';
import { TierLadder } from '../../features/games/world_boss/TierLadder';
import { TimerRing } from '../../features/games/world_boss/TimerRing';
import { QuestionCard } from '../../features/games/world_boss/QuestionCard';

interface LeaderboardRow {
  id: number;
  username: string;
  best_tier: number;
  points_contributed: number;
  limiter_breaks: number;
}

// Exported for testing. `tier`/`band`/`archetype`/`prompt` are not enough to
// name a question uniquely: `band` is a pure function of `tier`, and two
// archetypes (`cover`, `most_popular`) reuse the exact same prompt text for
// every subject they draw. The options are the one field that is always
// subject-specific — so they are the only thing guaranteed to change between
// two genuinely different questions, while staying byte-identical when the
// backend re-issues the same pending question verbatim (same options, same
// order).
export const buildQuestionId = (question: BossQuestion | null): string =>
  question ? question.options.join('|') : '';

const WorldBossPage: React.FC = () => {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const { question, verdict, phase, start, answer, next } = useWorldBossRun();

  const { data: boss, error } = useQuery({
    queryKey: ['world-boss', 'active'],
    queryFn: () => apiClient('/api/v1/game/world-boss/active/'),
    refetchInterval: 10000,
  });

  const { data: leaderboard } = useQuery({
    queryKey: ['world-boss', 'leaderboard', boss?.id],
    queryFn: async () => {
      const res = await apiClient('/api/v1/game/world-boss/leaderboard/', { skipToast: true });
      // The server is the only thing that should surprise us — not its own payload.
      return Array.isArray(res?.leaderboard) ? (res.leaderboard as LeaderboardRow[]) : [];
    },
    enabled: !!boss?.id,
    refetchInterval: 10000,
  });

  if (error || !boss)
    return (
      <AnimatedPage>
        <div className="flex min-h-screen flex-col items-center justify-center bg-black p-6 text-center text-white">
          <Skull size={80} className="mb-6 text-gray-800" />
          <h2 className="mb-4 text-4xl font-black uppercase italic">
            {t('games.world_boss.no_boss_title', 'Aucun boss actif')}
          </h2>
          <p className="max-w-md text-gray-500">
            {t(
              'games.world_boss.no_boss_desc',
              'Le monde est en sécurité pour le moment... Reviens plus tard pour le prochain raid mondial !',
            )}
          </p>
        </div>
      </AnimatedPage>
    );

  const hpPercent = boss.total_hp ? (boss.current_hp / boss.total_hp) * 100 : 0;
  const limiterBreak = question?.limiter_break ?? false;
  const tier = question?.tier ?? 1;
  // Once the boss's own HP hits 0, the server marks it inactive on the very
  // verdict that lands the killing blow — a fresh /question/ would 404, so the
  // "next question" control has to give way to a closing message instead.
  const bossDefeated = verdict !== null && verdict.boss.is_active === false;
  const questionId = buildQuestionId(question);

  return (
    <AnimatedPage>
      <div
        className={`mx-auto max-w-7xl px-6 py-12 text-white transition-colors ${
          limiterBreak ? 'bg-red-950/20' : ''
        }`}
      >
        <header className="mb-12 text-center">
          <h1 className="text-6xl font-black uppercase italic md:text-7xl">{boss.title}</h1>
          <div className="mt-4 flex items-center justify-center gap-6 text-xs font-bold uppercase tracking-widest text-gray-400">
            <span className="flex items-center gap-2">
              <Trophy size={14} className="text-yellow-500" />
              {t('games.world_boss.xp_reward', 'RÉCOMPENSE : {{xp}} XP', { xp: boss.reward_xp })}
            </span>
            {question && (
              <span>
                {t('games.world_boss.best_tier', 'Meilleur palier')} : {question.best_tier}
              </span>
            )}
            {question && question.run_damage > 0 && (
              <span>
                {t('games.world_boss.run_damage', 'Dégâts de la montée')} : {question.run_damage}
              </span>
            )}
          </div>

          <div className="mx-auto mt-8 max-w-3xl">
            <div className="mb-2 flex items-end justify-between font-mono">
              <span className="text-3xl font-black italic">
                {(boss.current_hp ?? 0).toLocaleString('fr-FR')}
                <span className="text-lg font-normal text-gray-600">
                  {' '}
                  / {(boss.total_hp ?? 0).toLocaleString('fr-FR')}
                </span>
              </span>
              <span className="text-xl font-black text-red-500">{Math.round(hpPercent)}%</span>
            </div>
            <div className="h-4 overflow-hidden rounded-full border border-white/5 bg-gray-900 p-1">
              <motion.div
                animate={{ width: `${hpPercent}%` }}
                transition={{ duration: 1, ease: 'circOut' }}
                className="h-full rounded-full bg-red-500"
              />
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
          <aside className={limiterBreak ? 'lg:-mx-4' : ''}>
            <TierLadder tier={tier} limiterBreak={limiterBreak} />
            {question && tier >= 12 && !limiterBreak && question.streak > 0 && (
              <p className="mt-3 text-center font-mono text-xs font-bold uppercase tracking-widest text-amber-400">
                {t('games.world_boss.limiter_progress', '{{n}}/5 au palier 12', {
                  n: question.streak,
                })}
              </p>
            )}
          </aside>

          <main className="lg:col-span-2">
            <div className="rounded-3xl border border-white/5 bg-gray-900/50 p-8 backdrop-blur-xl">
              {!question ? (
                <div className="space-y-6 text-center">
                  <p className="leading-relaxed text-gray-400">
                    {t(
                      'games.world_boss.protocol_desc',
                      "Chaque bonne réponse double les dégâts du palier suivant : 1, 2, 4… jusqu'à 2 048. Une seule erreur et tu repars du palier 1 — mais les dégâts déjà infligés restent acquis à la communauté. Cinq bonnes réponses au palier 12 déclenchent le Brisage de Limiteur.",
                    )}
                  </p>
                  <button
                    type="button"
                    onClick={start}
                    disabled={phase === 'answering'}
                    className="rounded-2xl bg-amber-500 px-10 py-4 font-black uppercase italic tracking-widest text-black transition hover:bg-amber-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {t('games.world_boss.start', 'Commencer la montée')}
                  </button>
                  {!isAuthenticated && (
                    <p className="text-xs font-bold uppercase tracking-widest text-gray-600">
                      {t('games.world_boss.login_required', 'Connecte-toi pour frapper le boss.')}
                    </p>
                  )}
                </div>
              ) : (
                <div className="space-y-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-black uppercase tracking-widest text-gray-500">
                        {t('games.world_boss.tier', 'Palier {{n}}', { n: question.tier })}
                      </div>
                      <div className="font-mono text-3xl font-black text-amber-400">
                        {t('games.world_boss.damage_at_tier', '{{dmg}} dégâts', {
                          dmg: question.damage,
                        })}
                      </div>
                    </div>
                    <TimerRing
                      questionId={questionId}
                      seconds={question.timer}
                      paused={phase !== 'asking'}
                      onExpire={() => answer(-1)}
                    />
                  </div>

                  <QuestionCard
                    question={question}
                    verdict={verdict}
                    onPick={answer}
                    locked={phase === 'answering' || verdict !== null}
                  />

                  <AnimatePresence>
                    {verdict && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-3 text-center"
                      >
                        <p
                          className={`text-2xl font-black italic ${
                            verdict.correct ? 'text-emerald-400' : 'text-red-500'
                          }`}
                        >
                          {verdict.correct
                            ? t('games.world_boss.correct', '+{{dmg}} dégâts', {
                                dmg: verdict.damage_dealt,
                              })
                            : verdict.late
                              ? t('games.world_boss.too_late', 'Temps écoulé — retour au palier 1')
                              : t('games.world_boss.wrong', 'Raté — retour au palier 1')}
                        </p>
                        {!verdict.correct && (
                          <p className="text-gray-400">
                            {t('games.world_boss.answer_was', 'La réponse était : {{answer}}', {
                              answer: verdict.correct_label,
                            })}
                          </p>
                        )}
                        <p className="text-sm text-gray-600">
                          {t('games.world_boss.subject_was', "Il s'agissait de « {{title}} »", {
                            title: verdict.subject,
                          })}
                        </p>
                        {verdict.limiter_break && (
                          <p className="font-black uppercase italic tracking-widest text-red-400">
                            {t(
                              'games.world_boss.limiter_break_on',
                              'BRISAGE DE LIMITEUR — dégâts doublés, plus aucune limite',
                            )}
                          </p>
                        )}
                        {bossDefeated ? (
                          <p className="font-black uppercase italic tracking-widest text-emerald-400">
                            {t(
                              'games.world_boss.defeated',
                              'Le boss est vaincu. Rendez-vous la semaine prochaine.',
                            )}
                          </p>
                        ) : (
                          <button
                            type="button"
                            onClick={next}
                            disabled={phase === 'answering'}
                            className="rounded-2xl bg-white px-8 py-3 font-black uppercase italic tracking-widest text-black transition hover:bg-amber-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {t('games.world_boss.next', 'Question suivante')}
                          </button>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </main>

          <aside className="rounded-3xl border border-white/5 bg-gray-900/50 p-6 backdrop-blur-xl">
            <h3 className="mb-6 flex items-center gap-3 text-lg font-black uppercase italic">
              <Zap size={18} className="text-yellow-500" fill="currentColor" />
              {t('games.world_boss.top_raiders', 'Meilleurs raiders')}
            </h3>
            <div className="space-y-2">
              {leaderboard && leaderboard.length > 0 ? (
                leaderboard.map((row: LeaderboardRow, i: number) => (
                  <div key={row.id} className="flex items-center gap-3 rounded-xl bg-black/40 p-3">
                    <span className="w-6 text-center font-black italic text-gray-600">{i + 1}</span>
                    <span className="flex-1 truncate font-bold text-white/90">{row.username}</span>
                    <span className="font-mono text-sm font-black text-amber-400">
                      {t('games.world_boss.tier', 'Palier {{n}}', { n: row.best_tier })}
                    </span>
                  </div>
                ))
              ) : (
                <p className="py-10 text-center font-black uppercase italic tracking-widest text-gray-700">
                  {t(
                    'games.world_boss.no_raiders',
                    'Aucun raider pour le moment. Sois le premier !',
                  )}
                </p>
              )}
            </div>
          </aside>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default WorldBossPage;
