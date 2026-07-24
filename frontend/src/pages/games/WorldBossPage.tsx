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
        <div className="flex min-h-screen flex-col items-center justify-center bg-[#0B0C10] p-6 text-center text-[#F4F1E8]">
          <Skull size={80} className="mb-6 text-[#8F94A5]/40" />
          <h2 className="font-manga mb-4 text-4xl font-black uppercase italic">
            {t('games.world_boss.no_boss_title', 'Aucun boss actif')}
          </h2>
          <p className="max-w-md text-[#8F94A5]">
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
        className={`min-h-screen bg-[#0B0C10] text-[#F4F1E8] transition-colors ${
          limiterBreak ? 'bg-[#E8442B]/10' : ''
        }`}
      >
        <div className="mx-auto max-w-7xl px-6 py-12">
          <header className="mb-12 text-center">
            <span className="explore-stamp mb-4 inline-block -rotate-2" aria-hidden>
              王
            </span>
            <h1 className="font-manga text-6xl font-black uppercase italic md:text-7xl">
              {boss.title}
            </h1>
            <div className="mt-4 flex items-center justify-center gap-6 text-xs font-bold uppercase tracking-widest text-[#8F94A5]">
              <span className="flex items-center gap-2">
                <Trophy size={14} className="text-[#FDB913]" />
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
                  <span className="text-lg font-normal text-[#8F94A5]">
                    {' '}
                    / {(boss.total_hp ?? 0).toLocaleString('fr-FR')}
                  </span>
                </span>
                <span className="text-xl font-black text-[#E8442B]">{Math.round(hpPercent)}%</span>
              </div>
              <div className="h-4 overflow-hidden rounded-full border border-[#F4F1E8]/10 bg-[#0F1016] p-1">
                <motion.div
                  animate={{ width: `${hpPercent}%` }}
                  transition={{ duration: 1, ease: 'circOut' }}
                  className="h-full rounded-full bg-[#E8442B]"
                />
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
            <aside className={limiterBreak ? 'lg:-mx-4' : ''}>
              <TierLadder tier={tier} limiterBreak={limiterBreak} />
              {question && tier >= 12 && !limiterBreak && question.streak > 0 && (
                <p className="mt-3 text-center font-mono text-xs font-bold uppercase tracking-widest text-[#FDB913]">
                  {t('games.world_boss.limiter_progress', '{{n}}/5 au palier 12', {
                    n: question.streak,
                  })}
                </p>
              )}
            </aside>

            <main className="lg:col-span-2">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
                {!question ? (
                  <div className="space-y-6 text-center">
                    <p className="leading-relaxed text-[#8F94A5]">
                      {t(
                        'games.world_boss.protocol_desc',
                        "Chaque bonne réponse double les dégâts du palier suivant : 1, 2, 4… jusqu'à 2 048. Une seule erreur et tu repars du palier 1 — mais les dégâts déjà infligés restent acquis à la communauté. Cinq bonnes réponses au palier 12 déclenchent le Brisage de Limiteur.",
                      )}
                    </p>
                    {/* Cliquable hors connexion, le bouton n'offrait qu'un 401 en
                      toast : la seule chose qu'il pouvait faire, c'est échouer.
                      Un visiteur anonyme le voit désactivé, et la ligne
                      ci-dessous lui dit pourquoi. */}
                    <button
                      type="button"
                      onClick={start}
                      disabled={phase === 'answering' || !isAuthenticated}
                      className="font-manga rounded-xl bg-[#E8442B] px-10 py-4 font-black uppercase italic tracking-widest text-[#F4F1E8] transition hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {t('games.world_boss.start', 'Commencer la montée')}
                    </button>
                    {!isAuthenticated && (
                      <p className="text-xs font-bold uppercase tracking-widest text-[#8F94A5]">
                        {t('games.world_boss.login_required', 'Connecte-toi pour frapper le boss.')}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-8">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                          {t('games.world_boss.tier', 'Palier {{n}}', { n: question.tier })}
                        </div>
                        <div className="font-mono text-3xl font-black text-[#FDB913]">
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
                              verdict.correct ? 'text-[#FDB913]' : 'text-[#E8442B]'
                            }`}
                          >
                            {verdict.correct
                              ? t('games.world_boss.correct', '+{{dmg}} dégâts', {
                                  dmg: verdict.damage_dealt,
                                })
                              : verdict.late
                                ? t(
                                    'games.world_boss.too_late',
                                    'Temps écoulé — retour au palier 1',
                                  )
                                : t('games.world_boss.wrong', 'Raté — retour au palier 1')}
                          </p>
                          {!verdict.correct && (
                            <p className="text-[#8F94A5]">
                              {t('games.world_boss.answer_was', 'La réponse était : {{answer}}', {
                                answer: verdict.correct_label,
                              })}
                            </p>
                          )}
                          <p className="text-sm text-[#8F94A5]/70">
                            {t('games.world_boss.subject_was', "Il s'agissait de « {{title}} »", {
                              title: verdict.subject,
                            })}
                          </p>
                          {verdict.limiter_break && (
                            <p className="font-black uppercase italic tracking-widest text-[#E8442B]">
                              {t(
                                'games.world_boss.limiter_break_on',
                                'BRISAGE DE LIMITEUR — dégâts doublés, plus aucune limite',
                              )}
                            </p>
                          )}
                          {bossDefeated ? (
                            <p className="font-black uppercase italic tracking-widest text-[#FDB913]">
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
                              className="font-manga rounded-xl border border-[#F4F1E8]/20 bg-transparent px-8 py-3 font-black uppercase italic tracking-widest text-[#F4F1E8] transition hover:border-[#FDB913] hover:text-[#FDB913] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] disabled:cursor-not-allowed disabled:opacity-50"
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

            <aside className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
              <h3 className="font-manga mb-6 flex items-center gap-3 text-lg font-black uppercase italic">
                <Zap size={18} className="text-[#FDB913]" fill="currentColor" />
                {t('games.world_boss.top_raiders', 'Meilleurs raiders')}
              </h3>
              <div className="space-y-2">
                {leaderboard && leaderboard.length > 0 ? (
                  leaderboard.map((row: LeaderboardRow, i: number) => (
                    <div
                      key={row.id}
                      className="flex items-center gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3"
                    >
                      <span className="w-6 text-center font-black italic text-[#8F94A5]">
                        {i + 1}
                      </span>
                      <span className="flex-1 truncate font-bold text-[#F4F1E8]">
                        {row.username}
                      </span>
                      <span className="font-mono text-sm font-black text-[#FDB913]">
                        {t('games.world_boss.tier', 'Palier {{n}}', { n: row.best_tier })}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="py-10 text-center font-black uppercase italic tracking-widest text-[#8F94A5]/60">
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
      </div>
    </AnimatedPage>
  );
};

export default WorldBossPage;
