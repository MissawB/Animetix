import React, { useState } from 'react';
import { Calendar, Layers, ArrowLeft, CheckCircle2, Loader2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useDailyChallenge } from '../../features/utils/hooks/useDailyChallenge';
import { classicGameService } from '../../features/games/services/classicService';
import { Button } from "../../components/ui/Button";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToastStore } from '../../store/toastStore';
import { useTranslation } from 'react-i18next';

import { DailyMode } from '../../types';

const DailyChallengePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);
  const { data, isLoading, isError } = useDailyChallenge();
  const [launching, setLaunching] = useState<string | null>(null);

  // Launch the Classic game in daily mode for this card's media type (everyone
  // gets the same deterministic target of the day), then jump straight to play.
  const launchDaily = async (mode: DailyMode) => {
    if (launching) return;
    setLaunching(mode.id);
    try {
      await classicGameService.start(mode.media_type ?? 'Anime', 'Normal', undefined, true);
      navigate('/game/classic/play/');
    } catch {
      addToast('Impossible de lancer le défi du jour. Réessayez.', 'error');
      setLaunching(null);
    }
  };

  if (isLoading) return (
    <div className="min-h-screen pb-20">
      <div className="h-64 w-full bg-gray-200 dark:bg-navy-900 animate-pulse rounded-b-[4rem]" />
      <div className="max-w-7xl mx-auto px-6 -mt-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Skeleton className="h-80 rounded-[3rem]" />
            <Skeleton className="h-80 rounded-[3rem]" />
            <Skeleton className="h-80 rounded-[3rem]" />
        </div>
      </div>
    </div>
  );

  if (isError || !data) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="bg-gradient-to-br from-yellow-400 to-orange-500 py-16 px-6 shadow-2xl mb-12 rounded-b-[4rem]">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl md:text-8xl font-black italic manga-font tracking-tighter uppercase text-black mb-4">
            DÉFIS DU JOUR<span className="text-white">.</span>
          </h1>
          <p className="text-xl font-bold uppercase tracking-widest text-black/60">
            Une seule cible par univers, à débusquer.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full bg-black text-white px-5 py-2 text-xs font-black uppercase tracking-widest">
              <Calendar className="w-4 h-4" /> {data.date}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-white text-black px-5 py-2 text-xs font-black uppercase tracking-widest shadow-lg">
              <Layers className="w-4 h-4" /> {data.modes.length} défis
            </span>
          </div>
        </div>
      </div>

      {/* Grid Selection */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {data.modes.map((mode: DailyMode) => (
            <button
              key={mode.id}
              onClick={() => launchDaily(mode)}
              disabled={!!launching}
              className="group relative block h-[320px] w-full text-left rounded-[3rem] overflow-hidden shadow-2xl no-underline transition-all hover:translate-y-[-10px] hover:rotate-2 disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:rotate-0"
            >
              {/* Background Gradient */}
              <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient} z-0`}></div>

              {/* Title Overlay (Brush Style) */}
              <div className="absolute top-8 left-8 z-30 transform -rotate-6 transition-transform group-hover:rotate-0">
                <h2 className="manga-font text-white text-5xl leading-[0.8] uppercase tracking-tighter" style={{ textShadow: '2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000' }}>
                  {mode.brush1}<br />
                  <span className="text-yellow-400 text-3xl ml-4">{mode.brush2}</span>
                </h2>
              </div>

              {/* Description */}
              <div className="absolute bottom-8 left-8 right-8 z-30 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <p className="text-white font-bold text-sm italic leading-tight drop-shadow-md">
                  {mode.description}
                </p>
              </div>

              {/* Character Icon */}
              <img src={mode.icon} alt="" className="absolute -right-4 -bottom-4 h-[85%] object-contain object-bottom z-20 drop-shadow-2xl transition-transform duration-500 group-hover:scale-110" loading="lazy" decoding="async" />

              {launching === mode.id && (
                <div className="absolute inset-0 z-40 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                  <Loader2 className="w-10 h-10 text-white animate-spin" />
                </div>
              )}

              {mode.completed && (
                <div className="absolute inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-center justify-center">
                  <div className="bg-yellow-400 text-black px-8 py-3 rounded-2xl font-black italic manga-font text-2xl rotate-12 shadow-2xl flex items-center gap-2">
                    COMPLÉTÉ <CheckCircle2 className="w-6 h-6" />
                  </div>
                </div>
              )}
            </button>
          ))}
        </div>

        <div className="mt-20 text-center">
          <Button as={Link} to="/" variant="outline" size="lg" className="italic px-12">
            <ArrowLeft className="w-5 h-5" /> RETOUR À L'ACCUEIL
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DailyChallengePage;
