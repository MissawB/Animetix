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

const LABEL = 'text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5]';
const FIELD =
  'w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] px-4 py-3 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]';

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
    <div className="flex flex-col items-stretch gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 md:flex-row md:items-end">
      <div className="flex w-full flex-col gap-1.5 md:w-1/3">
        <label htmlFor="tachidesk-source-select" className={LABEL}>
          Source Suwayomi
        </label>
        <select
          id="tachidesk-source-select"
          value={selectedSource}
          onChange={(e) => onSourceChange(e.target.value)}
          className={FIELD}
        >
          {sources.length === 0 && !loadingSources ? (
            <option value="">Aucune source installée</option>
          ) : (
            sources.map((src) => (
              <option key={src.id} value={src.id} className="bg-[#0F1016] text-[#F4F1E8]">
                {src.name} ({src.lang.toUpperCase()})
              </option>
            ))
          )}
        </select>
      </div>

      <form onSubmit={onSubmit} className="flex w-full flex-col gap-1.5 md:flex-1">
        <label htmlFor="tachidesk-search-input" className={LABEL}>
          Rechercher
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]/60" />
          <input
            id="tachidesk-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            aria-label="Rechercher un manga"
            placeholder="Rechercher un manga (ex : Solo Leveling)…"
            className={`${FIELD} pl-11`}
          />
        </div>
      </form>

      <button
        type="button"
        onClick={() => onSubmit()}
        disabled={loadingMangas}
        className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] px-8 py-3 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
      >
        {loadingMangas ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Scanner'}
      </button>
    </div>
  );
};

export const CatalogToolbar = React.memo(CatalogToolbarComponent);
