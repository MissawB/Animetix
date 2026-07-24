import React, { useEffect, useMemo } from 'react';
import { Search, Eye, Trophy } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { useVisionStore } from '../../features/games/stores/visionStore';

type VisionFormValues = { description: string };

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';
const SHU_CTA =
  'inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';

const VisionPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, isLoading, error, loadGame, restartGame, submitGuess } = useVisionStore();

  const visionSchema = useMemo(
    () =>
      z.object({
        description: z
          .string()
          .min(
            3,
            t(
              'games.vision.validation_min',
              "Veuillez entrer au moins 3 caractères pour l'analyse.",
            ),
          )
          .max(200, t('games.vision.validation_max', 'La description est trop longue.')),
      }),
    [t],
  );

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<VisionFormValues>({
    resolver: zodResolver(visionSchema),
    defaultValues: { description: '' },
  });

  const onSubmit = async (data: VisionFormValues) => {
    submitGuess(data.description);
    reset();
  };

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-20 text-[#F4F1E8] font-black animate-pulse">
        {t('games.vision.loading', 'ANALYSE VISIONNAIRE EN COURS...')}
      </div>
    );

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className={`${PANEL} border-[#E8442B]/40 p-8 md:p-10 text-center max-w-md`}>
          <h2 className="font-manga text-2xl font-black italic uppercase text-[#E8442B] mb-4">
            {t('games.vision.error_title', 'SYSTÈME OPTIQUE DÉFAILLANT')}
          </h2>
          <p className="mb-8 font-bold text-[#8F94A5]">{error}</p>
          <button className={SHU_CTA} onClick={restartGame}>
            {t('games.vision.reset_scan', 'RÉINITIALISER LE SCAN')}
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h1 className="font-manga text-5xl font-black italic uppercase mb-12 text-center flex items-center justify-center gap-3 text-[#F4F1E8]">
          <span className="explore-stamp -rotate-2" aria-hidden>
            目
          </span>
          VISION <span className="text-[#E8442B]">QUEST</span>
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-start">
          {/* IMAGE */}
          <div className="flex flex-col items-center sticky top-24">
            <div className={`${PANEL} p-4 relative overflow-hidden w-full`}>
              <img
                src={gameState.image_url}
                className="rounded-2xl w-full transition-all duration-1000"
                style={{
                  filter: gameState.gameOver
                    ? 'none'
                    : `blur(${Math.max(0, 20 - gameState.best_score / 5)}px)`,
                }}
                alt="Target"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute top-8 right-8 bg-[#0B0C10]/70 backdrop-blur-md px-6 py-2 rounded-full border border-[#F4F1E8]/20">
                <span className="text-3xl font-black text-[#FDB913]">
                  {Math.round(gameState.best_score)}%
                </span>
              </div>
            </div>

            {gameState.gameOver && (
              <div className={`${PANEL} border-[#FDB913]/40 mt-8 text-center p-8`}>
                <Trophy className="w-12 h-12 mx-auto mb-3 text-[#FDB913]" />
                <h3 className="font-manga text-2xl font-black italic uppercase text-[#F4F1E8]">
                  {gameState.secret_title}
                </h3>
                <button className={`${SHU_CTA} mt-4`} onClick={restartGame}>
                  {t('games.vision.replay', 'REJOUER')}
                </button>
              </div>
            )}
          </div>

          {/* RECHERCHE */}
          <div className={`${PANEL} p-8 md:p-10`}>
            {!gameState.gameOver && (
              <form onSubmit={handleSubmit(onSubmit)} className="mb-12 flex flex-col gap-4">
                <h2 className="text-xs font-black uppercase text-[#8F94A5] mb-2 tracking-[0.2em] flex items-center gap-2">
                  <Eye className="w-4 h-4 text-[#FDB913]" />{' '}
                  {t('games.vision.describe_prompt', 'Décrivez ce que vous voyez')}
                </h2>

                <div className="w-full flex flex-col gap-2 text-left">
                  <input
                    {...register('description')}
                    aria-invalid={!!errors.description}
                    placeholder={t(
                      'games.vision.guess_placeholder',
                      'Ex: Un guerrier aux cheveux noirs...',
                    )}
                    className={`w-full rounded-xl border bg-[#0B0C10] px-5 py-3.5 font-bold text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 ${
                      errors.description
                        ? 'border-[#E8442B] focus:border-[#E8442B]'
                        : 'border-[#F4F1E8]/15 focus:border-[#FDB913]'
                    }`}
                  />
                  {errors.description?.message && (
                    <span className="text-[#E8442B] text-xs font-black pl-2">
                      {errors.description.message}
                    </span>
                  )}
                </div>

                <button type="submit" className={`${SHU_CTA} w-full`}>
                  <Search className="w-5 h-5" /> {t('games.vision.analyze_btn', "ANALYSER L'IMAGE")}
                </button>
              </form>
            )}

            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-[#8F94A5]/60 uppercase tracking-widest mb-4">
                {t('games.vision.analysis_log', "Journal d'analyse")}
              </h4>
              {gameState.guesses.map((g, i: number) => (
                <div
                  key={i}
                  className="p-4 bg-[#0B0C10] rounded-xl flex justify-between items-center border border-[#F4F1E8]/10 hover:border-[#FDB913]/40 transition-colors"
                >
                  <span className="font-bold text-[#F4F1E8]/80">{g.text}</span>
                  <span className="px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase inline-flex items-center gap-1 border bg-[#FDB913]/10 text-[#FDB913] border-[#FDB913]/20">
                    {Math.round(g.score)}%
                  </span>
                </div>
              ))}
              {gameState.guesses.length === 0 && (
                <p className="text-center py-10 text-[#8F94A5]/50 italic">
                  {t('games.vision.no_analysis', 'Aucune analyse effectuée pour le moment.')}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisionPage;
