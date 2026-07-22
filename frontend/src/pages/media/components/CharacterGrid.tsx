import React from 'react';
import { Link } from 'react-router-dom';
import type { MediaCharacter } from '../../../features/media/hooks/useMediaCharacters';

export const CharacterGrid: React.FC<{ characters: MediaCharacter[] }> = ({ characters }) => (
  <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-6">
    {characters.map((c) => (
      <Link
        key={c.id}
        to={`/media/Character/${c.id}/`}
        className="group block no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913]"
      >
        <div className="mb-2 aspect-[3/4] overflow-hidden rounded-[4px] bg-[#F4F1E8]/5 ring-1 ring-[#F4F1E8]/10 transition-all group-hover:-translate-y-1 group-hover:ring-[#FDB913]/60">
          {c.image ? (
            <img
              src={c.image}
              className="h-full w-full object-cover"
              alt={c.name}
              loading="lazy"
              decoding="async"
            />
          ) : (
            <span className="flex h-full w-full items-center justify-center text-2xl font-black text-[#F4F1E8]/30">
              {c.name.charAt(0)}
            </span>
          )}
        </div>
        <p className="line-clamp-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors group-hover:text-[#F4F1E8]">
          {c.name}
        </p>
      </Link>
    ))}
  </div>
);
