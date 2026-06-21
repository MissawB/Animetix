import React from 'react';
import { Search, Loader2 } from 'lucide-react';
import type { Source } from '../types';

interface CatalogToolbarProps {
  sources: Source[];
  selectedSource: string;
  searchQuery: string;
  loadingSources: boolean;
  loadingMangas: boolean;
  onSourceChange: (value: string) => void;
  onSearchQueryChange: (value: string) => void;
  onSubmit: (e?: React.FormEvent) => void;
}

const CatalogToolbarComponent: React.FC<CatalogToolbarProps> = ({
  sources,
  selectedSource,
  searchQuery,
  loadingSources,
  loadingMangas,
  onSourceChange,
  onSearchQueryChange,
  onSubmit,
}) => {
  return (
    <div className="bg-navy-950/20 backdrop-blur-md border border-white/5 p-6 rounded-3xl flex flex-col md:flex-row gap-4 items-center">
      <div className="w-full md:w-1/3 flex flex-col gap-1.5">
        <label htmlFor="tachidesk-source-select" className="text-[10px] font-black uppercase tracking-widest text-gray-500">Source Suwayomi</label>
        <select
          id="tachidesk-source-select"
          value={selectedSource}
          onChange={(e) => onSourceChange(e.target.value)}
          className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-semibold"
        >
          {sources.length === 0 && !loadingSources ? (
            <option value="">Aucune source installée</option>
          ) : (
            sources.map((src) => (
              <option key={src.id} value={src.id}>
                {src.name} ({src.lang.toUpperCase()})
              </option>
            ))
          )}
        </select>
      </div>

      <form onSubmit={onSubmit} className="w-full md:flex-1 flex flex-col gap-1.5">
        <label htmlFor="tachidesk-search-input" className="text-[10px] font-black uppercase tracking-widest text-gray-500">Rechercher</label>
        <div className="relative">
          <input
            id="tachidesk-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder="Rechercher un manga (ex: Solo Leveling)..."
            className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-medium"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        </div>
      </form>

      <button
        onClick={() => onSubmit()}
        disabled={loadingMangas}
        className="mt-5 w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-black uppercase italic rounded-xl flex items-center justify-center gap-2 transition-all"
      >
        {loadingMangas ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rechercher'}
      </button>
    </div>
  );
};

export const CatalogToolbar = React.memo(CatalogToolbarComponent);
