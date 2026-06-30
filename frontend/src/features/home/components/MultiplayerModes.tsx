import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const MultiplayerModes: React.FC = () => {
  const { modesMulti, isEn } = useGameModes();

  return (
    <section className="px-6 md:px-10 py-16 bg-[#f1f3f5] dark:bg-[#0f0f1a] rounded-[3rem] border border-black/5 dark:border-white/5 text-left">
      <h2 className="text-3xl font-black mb-12 flex items-baseline text-black dark:text-white uppercase italic manga-font">
        {isEn ? 'With Friends' : 'Entre Amis'}
        <span className="text-yellow-400 text-3xl leading-none ml-1">.</span>
      </h2>
      <div className="flex flex-wrap gap-12 justify-center pb-4">
        {modesMulti.map((mode) => (
          <Link 
            key={mode.titre}
            to={mode.url} 
            className="collection-card rounded-3xl p-8 relative flex items-center justify-between w-full md:w-[500px] h-[220px] shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95 no-underline group overflow-hidden border border-black/10"
          >
            <div className="z-10 max-w-[60%]">
              <h3 className="text-black text-4xl font-black italic tracking-tighter manga-font leading-none">{mode.titre}</h3>
              <p className="text-black/70 text-xs font-bold uppercase tracking-widest mt-4 leading-relaxed">{mode.description}</p>
            </div>
            <img
              src={mode.icon_url}
              className="absolute right-2 bottom-0 h-[92%] w-auto max-w-[50%] object-contain object-bottom drop-shadow-lg transition-transform group-hover:scale-105"
              alt={mode.titre}
              loading="lazy"
              decoding="async"
            />
          </Link>
        ))}
      </div>
    </section>
  );
};
