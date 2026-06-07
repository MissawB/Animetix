import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const WorldBossBanner: React.FC = () => {
  const { isEn } = useGameModes();

  return (
    <section className="mb-16">
      <Link to="/game/world-boss/active/" className="block no-underline group">
        <div className="relative w-full h-[280px] bg-gradient-to-r from-red-950 to-black rounded-[3rem] overflow-hidden shadow-2xl border-4 border-red-600/20 group-hover:border-red-600/50 transition-all duration-500 flex items-center p-8 md:p-16">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 mix-blend-overlay"></div>
          <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-red-600/10 to-transparent"></div>

          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600 text-white text-[10px] font-black uppercase tracking-widest mb-6 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-white"></span> EVENT EN COURS
            </div>
            <h2 className="text-4xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-white mb-4 leading-none">
              WORLD <span className="text-red-600 text-glow">BOSS</span>
            </h2>
            <p className="text-sm md:text-lg font-bold text-white/60 uppercase tracking-[0.2em] leading-relaxed italic">
              {isEn ? 'Join the global community to take down the legendary Titan.' : "Rejoignez la communauté mondiale pour terrasser le Titan légendaire."}
            </p>
          </div>

          <img 
            src="/static/img/modes/worldboss.png" 
            className="absolute right-0 bottom-0 h-[110%] md:h-[130%] object-contain drop-shadow-[0_20px_50px_rgba(220,38,38,0.5)] group-hover:scale-110 group-hover:-rotate-3 transition-all duration-700 z-20 pointer-events-none" 
            alt="World Boss" 
          />
        </div>
      </Link>
    </section>
  );
};
