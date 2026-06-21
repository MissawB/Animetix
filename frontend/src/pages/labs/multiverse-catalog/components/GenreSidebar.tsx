import React from 'react';
import { Link } from 'react-router-dom';
import { SlidersHorizontal, Network } from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { getGenreAccent } from '../genre';
import type { GenreOption } from '../types';

interface GenreSidebarProps {
  showFilters: boolean;
  genre: string;
  total: number | undefined;
  availableGenres: GenreOption[] | undefined;
  onSelectGenre: (genre: string) => void;
}

// ─── Sidebar: Genre filters ──────────────────────────────────────────
const GenreSidebar: React.FC<GenreSidebarProps> = ({ showFilters, genre, total, availableGenres, onSelectGenre }) => {
  return (
    <aside className={`shrink-0 w-56 space-y-4 ${showFilters ? 'block' : 'hidden md:block'}`}>
      <h3 className="text-[10px] font-black uppercase tracking-widest opacity-30 flex items-center gap-2 mb-4">
        <SlidersHorizontal className="w-3.5 h-3.5" /> Genres
      </h3>

      <button
        onClick={() => onSelectGenre('')}
        className={`w-full text-left px-4 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
          !genre ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400' : 'bg-white/[0.02] border border-transparent hover:bg-white/5 opacity-60 hover:opacity-100'
        }`}
      >
        Tous les genres
        <span className="float-right opacity-40">{total ?? 0}</span>
      </button>

      {availableGenres?.map(g => {
        const accent = getGenreAccent(g.name);
        const isActive = genre.toLowerCase() === g.name.toLowerCase();
        return (
          <button
            key={g.name}
            onClick={() => onSelectGenre(g.name)}
            className={`w-full text-left px-4 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              isActive
                ? `bg-white/5 border border-white/10 ${accent}`
                : 'bg-white/[0.02] border border-transparent hover:bg-white/5 opacity-60 hover:opacity-100'
            }`}
          >
            {g.name}
            <span className="float-right opacity-40">{g.count}</span>
          </button>
        );
      })}

      {/* Nexus link */}
      <div className="pt-6 border-t border-white/5">
        <Link to="/lab/multiverse/" className="block">
          <Card padding="sm" className="bg-cyan-500/5 border-cyan-500/20 hover:bg-cyan-500/10 transition-colors group">
            <div className="flex items-center gap-3">
              <Network className="w-5 h-5 text-cyan-500 group-hover:scale-110 transition-transform" />
              <div>
                <p className="text-[10px] font-black uppercase text-cyan-400">Nexus Map</p>
                <p className="text-[8px] font-bold opacity-30 uppercase">Vue graphe 3D</p>
              </div>
            </div>
          </Card>
        </Link>
      </div>
    </aside>
  );
};

export default React.memo(GenreSidebar);
