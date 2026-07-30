import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DynamicAuraWrapper } from '../../../components/shared/DynamicAuraWrapper';
import { useGameModes } from '../data/useGameModes';

// Pool historique du site Django (`random.choice` côté serveur à chaque visite),
// perdu à la migration React qui avait figé hero.png. Une seule image est
// tirée au hasard au chargement de la page — pas de rotation.
export const HERO_IMAGES = [
  '/static/img/hero.png',
  '/static/img/Dio.png',
  '/static/img/Gintama.png',
  '/static/img/Mugiwara.png',
  '/static/img/Team_7.png',
  '/static/img/Z_team.png',
];

export const HeroSection: React.FC = () => {
  const { t } = useTranslation();
  const { isEn } = useGameModes();
  // Tirage unique au montage : l'image reste fixe pour toute la visite.
  const [heroImage] = React.useState(
    () => HERO_IMAGES[Math.floor(Math.random() * HERO_IMAGES.length)],
  );

  return (
    <section className="relative max-w-[1600px] mx-auto px-6 md:px-20 py-20 md:pb-32 min-h-[500px] flex flex-col md:flex-row items-center justify-between gap-12">
      {/* Trame halftone discrète (édition de nuit) */}
      <div className="explore-halftone absolute inset-0 pointer-events-none" aria-hidden />
      {/* Sceau volume, très discret */}
      <span
        className="font-manga pointer-events-none absolute -top-2 right-6 md:right-24 text-[10rem] leading-none font-black italic text-[#F4F1E8]/[0.04] select-none"
        aria-hidden
      >
        巻
      </span>

      <div className="z-10 md:w-1/2 text-left">
        <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter mb-8 uppercase text-[#F4F1E8] font-manga leading-none">
          ANIME<span className="text-shu-bright">TIX</span>
        </h1>
        <p className="text-xl md:text-2xl mb-10 text-[#8F94A5] font-medium leading-relaxed max-w-lg">
          {isEn
            ? 'Artificial intelligence in service of your passion.'
            : t('home.hero_tagline', "L'intelligence artificielle au service de votre passion.")}
        </p>
        <div className="flex flex-wrap gap-6">
          <Link
            to="/daily-challenge/"
            className="bg-[#E8442B] hover:bg-[#c9391f] text-[#0B0C10] font-manga font-black italic uppercase text-sm py-4 px-10 rounded-2xl hover:scale-105 active:scale-95 transition-all no-underline inline-block border border-[#E8442B]"
          >
            {t('nav.daily', 'Défi Quotidien')}
          </Link>
          <Link
            to="/leaderboard/"
            className="bg-[#0F1016] text-[#F4F1E8] font-manga font-black italic py-4 px-10 rounded-2xl text-sm tracking-wider uppercase transition-all duration-300 border border-[#F4F1E8]/10 hover:border-[#FDB913]/60 hover:text-[#FDB913] hover:scale-105 active:scale-95 no-underline inline-block"
          >
            {t('nav.leaderboard', 'Classement')}
          </Link>
        </div>
      </div>

      <div className="md:w-1/2 relative mt-10 md:mt-0 flex justify-center">
        <DynamicAuraWrapper>
          <img
            src={heroImage}
            alt="Hero Illustration"
            className="w-[500px] md:w-[600px] z-10 relative hero-img hero-swap transform"
          />
        </DynamicAuraWrapper>
      </div>
    </section>
  );
};
