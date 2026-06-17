import React from 'react';
import { Calendar, Layers, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDailyChallenge } from '../../features/utils/hooks/useDailyChallenge';
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import { useTranslation } from 'react-i18next';

import { DailyMode } from '../../types';

const DailyChallengePage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useDailyChallenge();

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
            Une seule cible, plusieurs façons de la débusquer.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Badge variant="neutral" className="bg-black text-white py-2 px-6">
              <Calendar className="w-4 h-4" /> {data.date}
            </Badge>
            <Badge variant="neutral" className="bg-white text-black py-2 px-6 shadow-lg">
              <Layers className="w-4 h-4" /> {data.media_type.toUpperCase()}
            </Badge>
          </div>
        </div>
      </div>

      {/* Grid Selection */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {data.modes.map((mode: DailyMode) => (
            <Link 
              key={mode.id} 
              to={`/game/${mode.id}/`} 
              className="group relative block h-[320px] rounded-[3rem] overflow-hidden shadow-2xl no-underline transition-all hover:translate-y-[-10px] hover:rotate-2"
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
              <img src={mode.icon} alt="" className="absolute -right-4 -bottom-4 h-[85%] object-contain z-20 drop-shadow-2xl transition-transform duration-500 group-hover:scale-110" />
              
              {mode.completed && (
                <div className="absolute inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-center justify-center">
                  <div className="bg-yellow-400 text-black px-8 py-3 rounded-2xl font-black italic manga-font text-2xl rotate-12 shadow-2xl flex items-center gap-2">
                    COMPLÉTÉ <CheckCircle2 className="w-6 h-6" />
                  </div>
                </div>
              )}
            </Link>
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
