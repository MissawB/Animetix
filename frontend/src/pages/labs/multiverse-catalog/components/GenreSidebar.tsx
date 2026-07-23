import React from 'react';
import { Link } from 'react-router-dom';
import { SlidersHorizontal, Network } from 'lucide-react';
import type { GenreOption } from '../types';

interface GenreSidebarProps {
  showFilters: boolean;
  genre: string;
  total: number | undefined;
  availableGenres: GenreOption[] | undefined;
  onSelectGenre: (genre: string) => void;
}

// ─── Sidebar: Genre filters ──────────────────────────────────────────
const GenreSidebar: React.FC<GenreSidebarProps> = ({
  showFilters,
  genre,
  total,
  availableGenres,
  onSelectGenre,
}) => {
  return (
    <aside className={`shrink-0 w-56 space-y-3 ${showFilters ? 'block' : 'hidden md:block'}`}>
      <h3 className="mb-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
        <SlidersHorizontal className="h-3.5 w-3.5" /> Genres
      </h3>

      <button
        onClick={() => onSelectGenre('')}
        className={`w-full cursor-pointer rounded-xl px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest transition-colors ${
          !genre
            ? 'border border-[#FDB913]/60 bg-[#FDB913]/10 text-[#FDB913]'
            : 'border border-transparent bg-[#0F1016] text-[#8F94A5] hover:text-[#F4F1E8]'
        }`}
      >
        Tous les genres
        <span className="float-right text-[#8F94A5]">{total ?? 0}</span>
      </button>

      {availableGenres?.map((g) => {
        const isActive = genre.toLowerCase() === g.name.toLowerCase();
        return (
          <button
            key={g.name}
            onClick={() => onSelectGenre(g.name)}
            className={`w-full cursor-pointer rounded-xl px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest transition-colors ${
              isActive
                ? 'border border-[#FDB913]/60 bg-[#FDB913]/10 text-[#FDB913]'
                : 'border border-transparent bg-[#0F1016] text-[#8F94A5] hover:text-[#F4F1E8]'
            }`}
          >
            {g.name}
            <span className="float-right text-[#8F94A5]">{g.count}</span>
          </button>
        );
      })}

      {/* Nexus link */}
      <div className="border-t border-[#F4F1E8]/10 pt-6">
        <Link to="/lab/multiverse/" className="group block no-underline">
          <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-4 transition-colors group-hover:border-[#FDB913]/60">
            <div className="flex items-center gap-3">
              <Network className="h-5 w-5 text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#F4F1E8]">
                  Nexus Map
                </p>
                <p className="text-[8px] font-bold uppercase text-[#8F94A5]">Vue graphe 3D</p>
              </div>
            </div>
          </div>
        </Link>
      </div>
    </aside>
  );
};

export default React.memo(GenreSidebar);
