import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const SoloChallenges: React.FC = () => {
  const { modesSolo, isEn } = useGameModes();

  return (
    <section className="py-16 text-left">
      <h2 className="text-3xl font-black mb-12 flex items-baseline text-black dark:text-white uppercase italic manga-font">
        {isEn ? 'Solo Challenges' : 'Défis Solo'}
        <span className="text-yellow-400 text-4xl leading-none ml-1">.</span>
      </h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-16 gap-x-12">
        {modesSolo.map((mode, index) => (
          <div 
            key={mode.titre}
            className="relative w-full h-[200px] char-card-group cursor-pointer animate-float"
            style={{ animationDelay: `0.${index}s` }}
          >
            <Link to={mode.url} className="block h-full relative no-underline">
              <div className="absolute inset-0 rounded-[24px] overflow-hidden shadow-lg char-card-bg">
                <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient}`}></div>
                <img 
                  src="https://www.transparenttextures.com/patterns/stardust.png" 
                  className="absolute inset-0 w-full h-full object-cover opacity-40 mix-blend-screen" 
                  alt="Stars"
                  loading="lazy"
                  decoding="async"
                />
              </div>

              <div className="absolute top-[5%] -left-4 z-30 transition-transform duration-500 char-card-text pointer-events-none">
                <h2 
                  className="manga-font text-white text-4xl leading-[0.7] -rotate-12 tracking-tighter uppercase whitespace-nowrap" 
                  style={{ textShadow: '-1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 4px 10px rgba(0,0,0,0.5)' }}
                >
                  {mode.titre_brush_1}<br />
                  <span className="text-yellow-400 text-2xl ml-6 tracking-normal">{mode.titre_brush_2}</span>
                </h2>
                <p
                  className="manga-font text-white text-xs italic mt-16 ml-10 opacity-90 tracking-wider leading-relaxed max-w-[60%] line-clamp-3"
                  style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}
                >
                  {mode.description}
                </p>
              </div>

              <img 
                src={mode.icon_url} 
                alt={mode.titre} 
                className="absolute bottom-0 -right-4 h-[105%] w-auto object-contain z-20 drop-shadow-[0_10px_10px_rgba(0,0,0,0.4)] transition-all duration-500 char-card-render"
                style={{ clipPath: 'inset(-100% -100% 0% -100%)', maxWidth: 'none' }}
                loading="lazy"
                decoding="async"
              />
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
};
