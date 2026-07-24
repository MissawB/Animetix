import React, { useState } from 'react';
import {
  Calendar,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Star,
  Trophy,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useDailyChallenge } from '../../features/utils/hooks/useDailyChallenge';
import { classicGameService } from '../../features/games/services/classicService';
import { CLASSIC_STATE_QUERY_KEY } from '../../features/games/hooks/useClassicGame';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { useToastStore } from '../../store/toastStore';
import { useTranslation } from 'react-i18next';

import { DailyChallenge, DailyMode } from '../../types';

const DailyChallengePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);
  const [date, setDate] = useState<string | undefined>(undefined); // undefined = today
  const { data, isLoading, isError } = useDailyChallenge(date);
  const [launching, setLaunching] = useState<string | null>(null);

  // Launch the Classic game in daily mode for this card's media type and the
  // currently viewed date (everyone gets the same deterministic target).
  const launchDaily = async (mode: DailyMode, day: string) => {
    if (launching) return;
    setLaunching(mode.id);
    try {
      const state = await classicGameService.start(
        mode.media_type ?? 'Anime',
        'Normal',
        undefined,
        true,
        day,
      );
      queryClient.setQueryData(CLASSIC_STATE_QUERY_KEY, state);
      navigate('/game/classic/play/');
    } catch {
      addToast('Impossible de lancer le défi du jour. Réessayez.', 'error');
      setLaunching(null);
    }
  };

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] pb-20">
        <div className="h-64 w-full bg-[#0F1016] border-b border-[#F4F1E8]/10 animate-pulse" />
        <div className="max-w-7xl mx-auto px-6 -mt-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Skeleton className="h-80 rounded-2xl" />
            <Skeleton className="h-80 rounded-2xl" />
            <Skeleton className="h-80 rounded-2xl" />
          </div>
        </div>
      </div>
    );

  if (isError || !data)
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-20 text-[#E8442B] font-bold">
        {t('common.error')}
      </div>
    );

  const daily = data as DailyChallenge;

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8] pb-20">
      {/* En-tête */}
      <div className="relative border-b border-[#F4F1E8]/10 bg-[#0F1016] py-16 px-6 mb-12 overflow-hidden">
        <div className="explore-halftone pointer-events-none absolute inset-0" aria-hidden />
        <div className="relative max-w-4xl mx-auto text-center">
          <div className="mb-4 flex items-center justify-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              日
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              Défi quotidien
            </span>
          </div>
          <h1 className="font-manga text-6xl md:text-8xl font-black italic tracking-tighter uppercase text-[#F4F1E8] mb-4">
            DÉFIS DU JOUR<span className="text-[#E8442B]">.</span>
          </h1>
          <p className="text-base leading-relaxed text-[#8F94A5]">
            {daily.is_today
              ? 'Une seule cible par univers, à débusquer.'
              : 'Rejoue un défi passé pour battre ton score.'}
          </p>

          {/* Navigation par date */}
          <div className="mt-8 flex items-center justify-center gap-3">
            <button
              onClick={() => daily.prev_date && setDate(daily.prev_date)}
              disabled={!daily.prev_date}
              aria-label="Jour précédent"
              className="grid place-items-center w-10 h-10 rounded-full border border-[#F4F1E8]/15 text-[#F4F1E8] disabled:opacity-30 hover:border-[#FDB913] transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-[#0B0C10] text-[#F4F1E8] px-5 py-2 text-xs font-black uppercase tracking-widest">
              <Calendar className="w-4 h-4 text-[#FDB913]" /> {daily.date}
            </span>
            <button
              onClick={() => daily.next_date && setDate(daily.next_date)}
              disabled={!daily.next_date}
              aria-label="Jour suivant"
              className="grid place-items-center w-10 h-10 rounded-full border border-[#F4F1E8]/15 text-[#F4F1E8] disabled:opacity-30 hover:border-[#FDB913] transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <div className="mt-4 flex items-center justify-center gap-3">
            {!daily.is_today && (
              <button
                onClick={() => setDate(undefined)}
                className="rounded-full border border-[#F4F1E8]/15 text-[#F4F1E8] px-5 py-2 text-xs font-black uppercase tracking-widest hover:border-[#FDB913] transition-colors"
              >
                Aujourd'hui
              </button>
            )}
            <span className="inline-flex items-center gap-2 rounded-full border border-[#FDB913]/40 bg-[#FDB913]/10 text-[#FDB913] px-5 py-2 text-xs font-black uppercase tracking-widest">
              <Trophy className="w-4 h-4" /> {daily.total_score ?? 0} pts
            </span>
          </div>
        </div>
      </div>

      {/* Grid Selection */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {daily.modes.map((mode: DailyMode) => (
            <button
              key={mode.id}
              onClick={() => launchDaily(mode, daily.date)}
              disabled={!!launching}
              className="group relative block h-[320px] w-full text-left rounded-[3rem] overflow-hidden shadow-2xl no-underline transition-all hover:translate-y-[-10px] hover:rotate-2 disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:rotate-0"
            >
              {/* Background Gradient */}
              <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient} z-0`}></div>

              {/* Title Overlay (Brush Style) */}
              <div className="absolute top-8 left-8 z-30 transform -rotate-6 transition-transform group-hover:rotate-0">
                <h2
                  className="manga-font text-white text-5xl leading-[0.8] uppercase tracking-tighter"
                  style={{
                    textShadow:
                      '2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000',
                  }}
                >
                  {mode.brush1}
                  <br />
                  <span className="text-yellow-400 text-3xl ml-4">{mode.brush2}</span>
                </h2>
              </div>

              {/* Score badge (when already completed for this day) */}
              {mode.completed && mode.score != null && (
                <div className="absolute top-6 right-6 z-30 inline-flex items-center gap-1.5 rounded-full bg-black/70 backdrop-blur text-yellow-400 px-4 py-1.5 text-sm font-black shadow-lg">
                  <Star className="w-4 h-4 fill-current" /> {mode.score}
                </div>
              )}

              {/* Description */}
              <div className="absolute bottom-8 left-8 right-8 z-30 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <p className="text-white font-bold text-sm italic leading-tight drop-shadow-md">
                  {mode.completed
                    ? 'Déjà résolu — rejoue pour améliorer ton score.'
                    : mode.description}
                </p>
              </div>

              {/* Character Icon */}
              <img
                src={mode.icon}
                alt=""
                className="absolute -right-4 -bottom-4 h-[85%] object-contain object-bottom z-20 drop-shadow-2xl transition-transform duration-500 group-hover:scale-110"
                loading="lazy"
                decoding="async"
              />

              {launching === mode.id && (
                <div className="absolute inset-0 z-40 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                  <Loader2 className="w-10 h-10 text-white animate-spin" />
                </div>
              )}

              {mode.completed && (
                <div className="absolute bottom-6 right-6 z-30 text-green-400">
                  <CheckCircle2 className="w-7 h-7 drop-shadow" />
                </div>
              )}
            </button>
          ))}
        </div>

        <div className="mt-20 text-center">
          <Button
            as={Link}
            to="/"
            variant="outline"
            size="lg"
            className="italic px-12 border-[#F4F1E8]/15 text-[#F4F1E8] hover:border-[#FDB913] hover:bg-transparent"
          >
            <ArrowLeft className="w-5 h-5" /> RETOUR À L'ACCUEIL
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DailyChallengePage;
