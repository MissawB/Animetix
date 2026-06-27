import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const SingularityLab: React.FC = () => {
  const { isEn } = useGameModes();

  return (
    <section className="py-16">
      <Link to="/lab/" className="block no-underline group">
        <div className="relative w-full h-[280px] bg-gradient-to-r from-navy-950 via-[#0a0a16] to-black rounded-[3rem] overflow-hidden shadow-2xl border border-cyan-400/15 group-hover:border-cyan-400/50 transition-all duration-500 flex items-center p-8 md:p-16">
          {/* Latent-space coordinate grid — drifts continuously (signature motion) */}
          <div
            className="absolute inset-0 opacity-[0.18] animate-grid-pan motion-reduce:animate-none"
            style={{
              backgroundImage:
                'linear-gradient(rgba(0,243,255,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(0,243,255,0.35) 1px, transparent 1px)',
              backgroundSize: '44px 44px',
              maskImage: 'linear-gradient(90deg, transparent 0%, black 55%, black 100%)',
              WebkitMaskImage: 'linear-gradient(90deg, transparent 0%, black 55%, black 100%)',
            }}
          ></div>
          {/* Neon wash: cyan from the right, a hint of magenta low-left */}
          <div className="absolute top-0 right-0 w-2/3 h-full bg-gradient-to-l from-cyan-500/15 to-transparent"></div>
          <div className="absolute -bottom-1/2 -left-16 w-[360px] h-[360px] rounded-full bg-fuchsia-600/15 blur-[120px]"></div>

          <div className="relative z-10 max-w-2xl">
            <h2 className="text-4xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-white mb-4 leading-none">
              SINGULARITY{' '}
              <span className="bg-gradient-to-r from-cyan-300 via-cyan-400 to-fuchsia-500 bg-clip-text text-transparent drop-shadow-[0_0_25px_rgba(0,243,255,0.45)]">
                LABS
              </span>
            </h2>
            <p className="text-sm md:text-lg font-bold text-white/60 uppercase tracking-[0.2em] leading-relaxed italic">
              {isEn
                ? 'Explore the boundaries of generative AI and pure cognition.'
                : "Explorez la frontière entre l'IA générative et la cognition pure."}
            </p>
          </div>

          {/* The brand mesh as a neural-lattice artifact — glow intensifies on hover (no scale/rotate, unlike the mode cards) */}
          <img
            src="/static/img/logo/mesh_neon.png"
            className="absolute right-4 md:right-12 top-1/2 -translate-y-1/2 h-[95%] md:h-[112%] object-contain opacity-95 drop-shadow-[0_0_45px_rgba(0,243,255,0.4)] group-hover:drop-shadow-[0_0_85px_rgba(0,243,255,0.75)] group-hover:opacity-100 transition-all duration-700 z-0 pointer-events-none"
            alt="Singularity Labs"
            loading="lazy"
            decoding="async"
          />
        </div>
      </Link>
    </section>
  );
};
