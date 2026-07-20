import React from 'react';
import { Link } from 'react-router-dom';
import type { MediaCharacter } from '../../../features/media/hooks/useMediaCharacters';

export const CharacterGrid: React.FC<{ characters: MediaCharacter[] }> = ({ characters }) => (
  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
    {characters.map((c) => (
      <Link key={c.id} to={`/media/Character/${c.id}/`} className="no-underline group block">
        <div className="aspect-[3/4] rounded-xl overflow-hidden bg-gray-900 mb-2 border border-white/5 group-hover:border-blue-500/40 transition-all shadow-xl">
          {c.image ? (
            <img
              src={c.image}
              className="w-full h-full object-cover"
              alt={c.name}
              loading="lazy"
              decoding="async"
            />
          ) : (
            <span className="w-full h-full flex items-center justify-center text-2xl font-black text-white/30">
              {c.name.charAt(0)}
            </span>
          )}
        </div>
        <p className="text-[10px] font-black uppercase tracking-tighter line-clamp-1 opacity-60 group-hover:opacity-100 group-hover:text-blue-400 transition-all">
          {c.name}
        </p>
      </Link>
    ))}
  </div>
);
