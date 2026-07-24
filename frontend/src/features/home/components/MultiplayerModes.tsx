import React from 'react';
import { Link } from 'react-router-dom';
import { useGameModes } from '../data/useGameModes';

export const MultiplayerModes: React.FC = () => {
  const { modesMulti, isEn } = useGameModes();

  return (
    <section className="px-6 md:px-10 py-16 bg-[#0F1016] rounded-2xl border border-[#F4F1E8]/10 text-left">
      <h2 className="text-3xl font-black mb-12 flex items-baseline text-[#F4F1E8] uppercase italic font-manga">
        {isEn ? 'With Friends' : 'Entre Amis'}
        <span className="text-[#E8442B] text-3xl leading-none ml-1">.</span>
      </h2>
      <div className="flex flex-wrap gap-12 justify-center pb-4">
        {modesMulti.map((mode) => (
          <Link
            key={mode.titre}
            to={mode.url}
            className="bg-[#0B0C10] rounded-2xl p-8 relative flex items-center justify-between w-full md:w-[500px] h-[220px] transition-all duration-300 hover:scale-105 active:scale-95 no-underline group overflow-hidden border border-[#F4F1E8]/10 hover:border-[#FDB913]/50"
          >
            <div className="z-10 max-w-[60%]">
              <h3 className="text-[#F4F1E8] text-4xl font-black italic tracking-tighter font-manga leading-none">
                {mode.titre}
              </h3>
              <p className="text-[#8F94A5] text-xs font-bold uppercase tracking-widest mt-4 leading-relaxed">
                {mode.description}
              </p>
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
