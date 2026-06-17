import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DynamicAuraWrapper } from '../../../components/shared/DynamicAuraWrapper';
import { useGameModes } from '../data/useGameModes';

export const HeroSection: React.FC = () => {
  const { t } = useTranslation();
  const { isEn } = useGameModes();

  return (
    <section className="max-w-[1600px] mx-auto px-6 md:px-20 py-20 md:pb-32 min-h-[500px] flex flex-col md:flex-row items-center justify-between gap-12">
      <div className="z-10 md:w-1/2 text-left">
        <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter mb-8 uppercase text-black dark:text-white manga-font leading-none">
          ANIMETIX
        </h1>
        <p className="text-xl md:text-2xl mb-10 text-gray-700 dark:text-gray-300 font-medium leading-relaxed max-w-lg">
          {isEn ? 'Artificial intelligence in service of your passion.' : "L'intelligence artificielle au service de votre passion."}
        </p>
        <div className="flex flex-wrap gap-6">
          <Link 
            to="/daily-challenge/" 
            className="bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font text-sm py-4 px-10 rounded-2xl shadow-2xl hover:scale-105 active:scale-95 transition-all no-underline inline-block border-2 border-black"
          >
            {t('nav.daily', 'Défi Quotidien')}
          </Link>
          <Link 
            to="/leaderboard/" 
            className="bg-gray-800 dark:bg-gray-700 text-white font-black italic manga-font py-4 px-10 rounded-2xl text-sm tracking-wider uppercase transition-all duration-300 hover:bg-black dark:hover:bg-gray-600 hover:scale-105 active:scale-95 no-underline inline-block shadow-2xl"
          >
            {t('nav.leaderboard', 'Classement')}
          </Link>
        </div>
      </div>
      
      <div className="md:w-1/2 relative mt-10 md:mt-0 flex justify-center">
        <DynamicAuraWrapper>
          <img 
            src="/static/img/hero.png" 
            alt="Hero Illustration" 
            className="w-[500px] md:w-[600px] z-10 relative hero-img transform"
          />
        </DynamicAuraWrapper>
      </div>
    </section>
  );
};
