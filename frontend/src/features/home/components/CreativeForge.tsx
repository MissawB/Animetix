import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const CreativeForge: React.FC = () => {
  const { modesCreative, isEn } = useGameModes();

  return (
    <section className="py-16 text-left">
      <h2 className="text-3xl font-black mb-12 flex items-baseline text-black dark:text-white uppercase italic manga-font">
        {isEn ? 'Creative Forge' : 'Créative'}
        <span className="text-yellow-400 text-4xl leading-none ml-1">.</span>
      </h2>
      
      {modesCreative.map((mode) => (
        <Link 
          key={mode.titre}
          to={mode.url} 
          className="w-full block no-underline group"
        >
          <div className="relative w-full h-[350px] md:h-[500px] bg-[#050505] rounded-[3rem] overflow-hidden shadow-2xl flex flex-col justify-between p-8 md:p-12 transition-transform duration-500 hover:scale-[1.01] active:scale-100">
            <div className="absolute inset-0 w-full h-full flex items-center justify-center z-10 p-4">
              <img 
                src={mode.fusion_image} 
                className="max-h-full max-w-full object-contain grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700" 
                alt="Fusion" 
              />
            </div>

            <div className="absolute bottom-0 left-0 w-full h-[180px] bg-gradient-to-t from-black via-black/80 to-transparent z-20"></div>

            <div className="relative z-30 mt-auto">
              <h1 
                className="text-white text-4xl md:text-7xl lg:text-9xl font-black uppercase tracking-tighter leading-none mb-3 manga-font italic" 
                style={{ textShadow: '0 10px 30px rgba(0,0,0,0.5)' }}
              >
                {mode.titre}
              </h1>
              <p className="text-yellow-400 text-sm md:text-xl font-black uppercase tracking-[0.2em] manga-font opacity-90 leading-none">
                {mode.titre_sub}
              </p>
            </div>
          </div>
        </Link>
      ))}
    </section>
  );
};
