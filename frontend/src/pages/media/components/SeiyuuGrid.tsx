import React from 'react';
import type { Seiyuu } from '../../../types';

export const SeiyuuGrid: React.FC<{ seiyuu: Seiyuu[] }> = ({ seiyuu }) => (
  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
    {seiyuu.map((s) => (
      <div
        key={s.id}
        className="flex items-center gap-3 p-3 bg-gray-900 rounded-2xl border border-white/5"
      >
        {s.image ? (
          <img
            src={s.image}
            className="w-10 h-10 rounded-full object-cover flex-none"
            alt={s.name}
            loading="lazy"
            decoding="async"
          />
        ) : (
          <span className="w-10 h-10 rounded-full bg-white/10 text-white flex items-center justify-center font-black text-sm flex-none">
            {s.name.charAt(0)}
          </span>
        )}
        <div className="min-w-0">
          <p className="text-xs font-bold italic truncate text-white">{s.name}</p>
          {s.role && <p className="text-[10px] text-gray-500 uppercase truncate">{s.role}</p>}
        </div>
      </div>
    ))}
  </div>
);
