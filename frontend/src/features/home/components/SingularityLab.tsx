import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGameModes } from '../data/useGameModes';

export const SingularityLab: React.FC = () => {
  const { t } = useTranslation();
  const { isEn } = useGameModes();

  return (
    <section className="py-16 text-left">
      <h2 className="text-3xl font-black mb-6 flex items-baseline text-[#F4F1E8] uppercase italic font-manga">
        Labs
        <span className="text-[#E8442B] text-3xl leading-none ml-1">.</span>
      </h2>
      <Link to="/lab/" className="block no-underline group">
        <div className="relative w-full h-[280px] bg-[#14161D] rounded-2xl overflow-hidden shadow-2xl border border-[#F4F1E8]/10 group-hover:border-[#5D7FD3]/50 transition-all duration-500 flex items-center p-8 md:p-16">
          {/* Latent-space coordinate grid — drifts continuously (signature motion) */}
          <div
            className="absolute inset-0 opacity-[0.14] animate-grid-pan motion-reduce:animate-none"
            style={{
              backgroundImage:
                'linear-gradient(rgba(93,127,211,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(93,127,211,0.35) 1px, transparent 1px)',
              backgroundSize: '44px 44px',
              maskImage: 'linear-gradient(90deg, transparent 0%, black 55%, black 100%)',
              WebkitMaskImage: 'linear-gradient(90deg, transparent 0%, black 55%, black 100%)',
            }}
          ></div>
          {/* Voile indigo cognition depuis la droite */}
          <div className="absolute top-0 right-0 w-2/3 h-full bg-gradient-to-l from-[#5D7FD3]/10 to-transparent"></div>

          <div className="relative z-10 max-w-2xl">
            <h2 className="text-4xl md:text-6xl font-black italic font-manga tracking-tighter uppercase text-[#F4F1E8] mb-4 leading-none">
              SINGULARITY <span className="text-[#5D7FD3]">LABS</span>
            </h2>
            <p className="text-sm md:text-lg font-bold text-[#8F94A5] uppercase tracking-[0.2em] leading-relaxed italic">
              {isEn
                ? 'Explore the boundaries of generative AI and pure cognition.'
                : t(
                    'home.singularity_desc',
                    "Explorez la frontière entre l'IA générative et la cognition pure.",
                  )}
            </p>
          </div>

          {/* The brand mesh as a neural-lattice artifact — subtle lift on hover (no scale/rotate, unlike the mode cards) */}
          <img
            src="/static/img/logo/mesh_neon.png"
            className="absolute right-4 md:right-12 top-1/2 -translate-y-1/2 h-[95%] md:h-[112%] object-contain opacity-70 group-hover:opacity-95 transition-all duration-700 z-0 pointer-events-none"
            alt="Singularity Labs"
            loading="lazy"
            decoding="async"
          />
        </div>
      </Link>
    </section>
  );
};
