import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DynamicAuraWrapper } from '../../../components/shared/DynamicAuraWrapper';
import { useGameModes } from '../data/useGameModes';

// Pool historique du site Django (`random.choice` côté serveur à chaque visite),
// perdu à la migration React qui avait figé hero.png. Restauré ici avec une
// vraie rotation à intervalle, départ aléatoire.
export const HERO_IMAGES = [
  '/static/img/hero.png',
  '/static/img/Dio.png',
  '/static/img/Gintama.png',
  '/static/img/Mugiwara.png',
  '/static/img/Team_7.png',
  '/static/img/Z_team.png',
];
export const HERO_ROTATION_MS = 8000;

export const HeroSection: React.FC = () => {
  const { t } = useTranslation();
  const { isEn } = useGameModes();
  const [heroIndex, setHeroIndex] = React.useState(() =>
    Math.floor(Math.random() * HERO_IMAGES.length),
  );

  React.useEffect(() => {
    const id = window.setInterval(
      () => setHeroIndex((i) => (i + 1) % HERO_IMAGES.length),
      HERO_ROTATION_MS,
    );
    return () => window.clearInterval(id);
  }, []);

  // Précharge la prochaine image : le fondu se joue sans flash de chargement.
  React.useEffect(() => {
    const next = new Image();
    next.src = HERO_IMAGES[(heroIndex + 1) % HERO_IMAGES.length];
  }, [heroIndex]);

  return (
    <section className="max-w-[1600px] mx-auto px-6 md:px-20 py-20 md:pb-32 min-h-[500px] flex flex-col md:flex-row items-center justify-between gap-12">
      <div className="z-10 md:w-1/2 text-left">
        <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter mb-8 uppercase text-black dark:text-white manga-font leading-none">
          ANIMETIX
        </h1>
        <p className="text-xl md:text-2xl mb-10 text-gray-700 dark:text-gray-300 font-medium leading-relaxed max-w-lg">
          {isEn
            ? 'Artificial intelligence in service of your passion.'
            : t('home.hero_tagline', "L'intelligence artificielle au service de votre passion.")}
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
          {/* key={src} remonte l'élément à chaque rotation → l'animation CSS hero-swap rejoue. */}
          <img
            key={HERO_IMAGES[heroIndex]}
            src={HERO_IMAGES[heroIndex]}
            alt="Hero Illustration"
            className="w-[500px] md:w-[600px] z-10 relative hero-img hero-swap transform"
          />
        </DynamicAuraWrapper>
      </div>
    </section>
  );
};
