import React from 'react';
import type { Seiyuu } from '../../../types';

export const SeiyuuGrid: React.FC<{ seiyuu: Seiyuu[] }> = ({ seiyuu }) => (
  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
    {seiyuu.map((s) => (
      <div
        key={s.id}
        className="flex items-center gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#F4F1E8]/[0.03] p-3"
      >
        {s.image ? (
          <img
            src={s.image}
            className="h-10 w-10 flex-none rounded-full object-cover ring-1 ring-[#F4F1E8]/15"
            alt={s.name}
            loading="lazy"
            decoding="async"
          />
        ) : (
          <span className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-[#F4F1E8]/10 text-sm font-black text-[#F4F1E8]">
            {s.name.charAt(0)}
          </span>
        )}
        <div className="min-w-0">
          <p className="truncate text-xs font-bold italic text-[#F4F1E8]">{s.name}</p>
          {s.role && (
            <p className="truncate text-[10px] uppercase tracking-widest text-[#8F94A5]">
              {s.role}
            </p>
          )}
        </div>
      </div>
    ))}
  </div>
);
