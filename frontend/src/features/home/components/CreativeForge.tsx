import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGameModes } from '../data/useGameModes';

export const CreativeForge: React.FC = () => {
  const { t } = useTranslation();
  const { modesCreative, isEn } = useGameModes();

  return (
    <section className="py-16 text-left">
      <h2 className="text-3xl font-black mb-12 flex items-baseline text-[#F4F1E8] uppercase italic font-manga">
        {isEn ? 'Creative Forge' : t('home.creative_title', 'Créative')}
        <span className="text-[#E8442B] text-4xl leading-none ml-1">.</span>
      </h2>

      {modesCreative.map((mode) => (
        <Link key={mode.titre} to={mode.url} className="w-full block no-underline group">
          <div className="relative w-full h-[350px] md:h-[500px] bg-[#14161D] rounded-2xl border border-[#F4F1E8]/10 overflow-hidden shadow-2xl flex flex-col justify-between p-8 md:p-12 transition-all duration-500 hover:scale-[1.01] hover:border-[#E8442B]/40 active:scale-100">
            <div className="absolute inset-0 w-full h-full flex items-center justify-center z-10 p-4">
              <img
                src={mode.fusion_image}
                className="max-h-full max-w-full object-contain grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
                alt="Fusion"
                loading="lazy"
                decoding="async"
              />
            </div>

            <div className="absolute bottom-0 left-0 w-full h-[180px] bg-gradient-to-t from-[#14161D] via-[#14161D]/80 to-transparent z-20"></div>

            <div className="relative z-30 mt-auto">
              <h1
                className="text-[#F4F1E8] text-4xl md:text-7xl lg:text-9xl font-black uppercase tracking-tighter leading-none mb-3 font-manga italic"
                style={{ textShadow: '0 10px 30px rgba(0,0,0,0.5)' }}
              >
                {mode.titre}
              </h1>
              <p className="text-[#FDB913] text-sm md:text-xl font-black uppercase tracking-[0.2em] font-manga opacity-90 leading-none">
                {mode.titre_sub}
              </p>
            </div>
          </div>
        </Link>
      ))}
    </section>
  );
};
