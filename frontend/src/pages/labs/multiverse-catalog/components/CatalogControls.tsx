import React from 'react';
import {
  Search,
  LayoutGrid,
  LayoutList,
  X,
  ArrowUpDown,
  Filter,
} from 'lucide-react';
import type { SortOption, ViewMode } from '../types';

interface CatalogControlsProps {
  search: string;
  sort: string;
  viewMode: ViewMode;
  showFilters: boolean;
  hasActiveFilters: boolean;
  sortOptions: SortOption[];
  onSearchChange: (value: string) => void;
  onClearSearch: () => void;
  onSortChange: (value: string) => void;
  onToggleFilters: () => void;
  onViewModeChange: (mode: ViewMode) => void;
  onClearFilters: () => void;
}

// ─── Controls Bar ────────────────────────────────────────────────────
const CatalogControls: React.FC<CatalogControlsProps> = ({
  search,
  sort,
  viewMode,
  showFilters,
  hasActiveFilters,
  sortOptions,
  onSearchChange,
  onClearSearch,
  onSortChange,
  onToggleFilters,
  onViewModeChange,
  onClearFilters,
}) => {
  return (
    <div className="sticky top-0 z-30 bg-[#05050a]/90 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center">
          {/* Search */}
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 opacity-30" />
            <input
              id="catalog-search"
              aria-label="Rechercher un univers ou une cosmologie"
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Rechercher un univers, une cosmologie..."
              className="w-full pl-11 pr-10 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold placeholder:opacity-30 focus:outline-none focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/10 transition-all"
            />
            {search && (
              <button
                onClick={onClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 transition-colors"
              >
                <X className="w-3.5 h-3.5 opacity-40" />
              </button>
            )}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 opacity-30 shrink-0" />
            <select
              id="catalog-sort"
              value={sort}
              onChange={(e) => onSortChange(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black uppercase tracking-widest focus:outline-none focus:border-cyan-500/40 transition-all appearance-none cursor-pointer"
            >
              {sortOptions.map(opt => (
                <option key={opt.value} value={opt.value} className="bg-[#0a0a14]">{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Filter toggle (mobile) */}
          <button
            onClick={onToggleFilters}
            className={`md:hidden flex items-center gap-2 px-4 py-3 rounded-xl border transition-all text-[10px] font-black uppercase tracking-widest ${
              showFilters ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-white/5 border-white/10'
            }`}
          >
            <Filter className="w-3.5 h-3.5" /> Filtres
          </button>

          {/* View toggle */}
          <div className="flex bg-white/5 border border-white/10 rounded-xl overflow-hidden shrink-0">
            <button
              id="view-grid"
              onClick={() => onViewModeChange('grid')}
              className={`p-3 transition-colors ${viewMode === 'grid' ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 opacity-40'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              id="view-list"
              onClick={() => onViewModeChange('list')}
              className={`p-3 transition-colors ${viewMode === 'list' ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 opacity-40'}`}
            >
              <LayoutList className="w-4 h-4" />
            </button>
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <X className="w-3 h-3" /> Réinitialiser
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(CatalogControls);
