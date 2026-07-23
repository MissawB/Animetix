import React from 'react';
import { Search, LayoutGrid, LayoutList, X, ArrowUpDown, Filter } from 'lucide-react';
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
    <div className="sticky top-0 z-30 border-b border-[#F4F1E8]/10 bg-[#0B0C10]/90 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6">
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center">
          {/* Search */}
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]" />
            <input
              id="catalog-search"
              aria-label="Rechercher un univers ou une cosmologie"
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Rechercher un univers, une cosmologie..."
              className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0F1016] py-3 pl-11 pr-10 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
            />
            {search && (
              <button
                onClick={onClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer rounded-full border-none bg-transparent p-1 text-[#8F94A5] transition-colors hover:text-[#F4F1E8]"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="h-3.5 w-3.5 shrink-0 text-[#8F94A5]" />
            <select
              id="catalog-sort"
              value={sort}
              onChange={(e) => onSortChange(e.target.value)}
              className="cursor-pointer appearance-none rounded-xl border border-[#F4F1E8]/15 bg-[#0F1016] px-4 py-3 text-[10px] font-black uppercase tracking-widest text-[#F4F1E8] outline-none transition-colors focus:border-[#FDB913]"
            >
              {sortOptions.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#0F1016]">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Filter toggle (mobile) */}
          <button
            onClick={onToggleFilters}
            className={`md:hidden flex cursor-pointer items-center gap-2 rounded-xl border bg-[#0F1016] px-4 py-3 text-[10px] font-black uppercase tracking-widest transition-colors ${
              showFilters
                ? 'border-[#FDB913]/60 text-[#FDB913]'
                : 'border-[#F4F1E8]/15 text-[#8F94A5]'
            }`}
          >
            <Filter className="h-3.5 w-3.5" /> Filtres
          </button>

          {/* View toggle */}
          <div className="flex shrink-0 overflow-hidden rounded-xl border border-[#F4F1E8]/15 bg-[#0F1016]">
            <button
              id="view-grid"
              onClick={() => onViewModeChange('grid')}
              className={`cursor-pointer border-none bg-transparent p-3 transition-colors ${
                viewMode === 'grid'
                  ? 'bg-[#FDB913]/15 text-[#FDB913]'
                  : 'text-[#8F94A5] hover:text-[#F4F1E8]'
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              id="view-list"
              onClick={() => onViewModeChange('list')}
              className={`cursor-pointer border-none bg-transparent p-3 transition-colors ${
                viewMode === 'list'
                  ? 'bg-[#FDB913]/15 text-[#FDB913]'
                  : 'text-[#8F94A5] hover:text-[#F4F1E8]'
              }`}
            >
              <LayoutList className="h-4 w-4" />
            </button>
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="flex cursor-pointer items-center gap-1.5 rounded-lg border-none bg-transparent px-3 py-2 text-[9px] font-black uppercase tracking-widest text-[#E8442B] transition-colors hover:bg-[#E8442B]/10"
            >
              <X className="h-3 w-3" /> Réinitialiser
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(CatalogControls);
