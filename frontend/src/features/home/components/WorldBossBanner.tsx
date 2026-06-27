import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const WorldBossBanner: React.FC = () => {
  const { isEn } = useGameModes();

  return (
    <section className="mb-16">
      <Link to="/game/world-boss/active/" className="block no-underline group">
        <div className="relative w-full h-[280px] bg-gradient-to-r from-red-950 to-black rounded-[3rem] overflow-hidden shadow-2xl border-4 border-red-600/20 group-hover:border-red-600/60 transition-all duration-500 flex items-center p-8 md:p-16">
          {/* Carbon-fibre grain */}
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 mix-blend-overlay"></div>
          <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-red-600/10 to-transparent"></div>

          {/* Signature: breathing danger aura behind the boss */}
          <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[420px] h-[420px] rounded-full bg-red-600/25 blur-[100px] animate-boss-pulse group-hover:bg-red-500/40 transition-colors duration-500 pointer-events-none z-0"></div>

          {/* Signature: alert beam scanning across the banner */}
          <div className="absolute top-0 left-0 h-full w-1/3 bg-gradient-to-r from-transparent via-red-500/30 to-transparent blur-xl animate-boss-sweep pointer-events-none z-0"></div>

          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600 text-white text-[10px] font-black uppercase tracking-widest mb-6 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-white"></span> {isEn ? 'Live Event' : 'Event en cours'}
            </div>
            <h2 className="text-4xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-white mb-4 leading-none">
              WORLD <span className="text-red-600 text-glow">BOSS</span>
            </h2>
            <p className="text-sm md:text-lg font-bold text-white/60 uppercase tracking-[0.2em] leading-relaxed italic">
              {isEn ? 'Join the global community to take down the legendary Titan.' : "Rejoignez la communauté mondiale pour terrasser le Titan légendaire."}
            </p>
          </div>

          {/* The boss lunges forward and flares on hover (no generic rotate) */}
          <img
            src="/static/img/modes/WorldBoss.png"
            className="absolute right-0 md:right-6 bottom-0 h-[85%] md:h-[100%] object-contain drop-shadow-[0_20px_50px_rgba(220,38,38,0.5)] group-hover:scale-105 group-hover:-translate-x-2 transition-transform duration-700 ease-out z-20 pointer-events-none"
            alt="World Boss"
            loading="lazy"
            decoding="async"
          />
        </div>
      </Link>
    </section>
  );
};
