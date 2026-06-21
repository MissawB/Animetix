import React from 'react';
import { Loader2, Globe } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useMultiverseCatalog } from './multiverse-catalog/hooks/useMultiverseCatalog';
import CatalogHeader from './multiverse-catalog/components/CatalogHeader';
import CatalogControls from './multiverse-catalog/components/CatalogControls';
import GenreSidebar from './multiverse-catalog/components/GenreSidebar';
import UniverseGridCard from './multiverse-catalog/components/UniverseGridCard';
import UniverseListRow from './multiverse-catalog/components/UniverseListRow';
import ResultsPagination from './multiverse-catalog/components/ResultsPagination';
import UniverseDetailPanel from './multiverse-catalog/components/UniverseDetailPanel';

// ─── Main Catalog Page ───────────────────────────────────────────────
const MultiverseCatalogPage: React.FC = () => {
  const {
    search,
    debouncedSearch,
    genre,
    sort,
    viewMode,
    selectedUniverse,
    showFilters,
    data,
    isLoading,
    isFetching,
    sortOptions,
    hasActiveFilters,
    handleClearFilters,
    handleSearchChange,
    handleClearSearch,
    handleSortChange,
    handleToggleFilters,
    handleViewModeChange,
    handleSelectGenre,
    handleSelectUniverse,
    handleCloseDetail,
    handlePrevPage,
    handleNextPage,
    handleSelectPage,
  } = useMultiverseCatalog();

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        {/* ── Hero Header ─────────────────────────────────────── */}
        <CatalogHeader total={data?.pagination.total} />

        {/* ── Controls Bar ────────────────────────────────────── */}
        <CatalogControls
          search={search}
          sort={sort}
          viewMode={viewMode}
          showFilters={showFilters}
          hasActiveFilters={!!hasActiveFilters}
          sortOptions={sortOptions}
          onSearchChange={handleSearchChange}
          onClearSearch={handleClearSearch}
          onSortChange={handleSortChange}
          onToggleFilters={handleToggleFilters}
          onViewModeChange={handleViewModeChange}
          onClearFilters={handleClearFilters}
        />

        {/* ── Main Content ────────────────────────────────────── */}
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex gap-8">
            {/* Sidebar: Genre filters */}
            <GenreSidebar
              showFilters={showFilters}
              genre={genre}
              total={data?.pagination.total}
              availableGenres={data?.available_genres}
              onSelectGenre={handleSelectGenre}
            />

            {/* Results */}
            <main className="flex-1 min-w-0">
              {/* Results header */}
              <div className="flex items-center justify-between mb-6">
                <p className="text-[10px] font-black uppercase opacity-30 tracking-widest">
                  {data ? `${data.pagination.total} univers trouvé${data.pagination.total > 1 ? 's' : ''}` : ''}
                  {debouncedSearch && ` pour "${debouncedSearch}"`}
                  {genre && ` • ${genre}`}
                </p>
                {isFetching && !isLoading && (
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                )}
              </div>

              {/* Loading state */}
              {isLoading && (
                <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-3'}>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className={`bg-white/[0.02] rounded-2xl animate-pulse ${viewMode === 'grid' ? 'h-72' : 'h-20'}`} />
                  ))}
                </div>
              )}

              {/* Empty state */}
              {!isLoading && data && data.results.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <Globe className="w-16 h-16 text-white/10 mb-6" />
                  <h3 className="text-xl font-black italic manga-font uppercase text-white/40 mb-2">Aucun univers trouvé</h3>
                  <p className="text-[10px] font-bold uppercase opacity-20 tracking-wider mb-6">
                    {debouncedSearch ? 'Essayez un autre terme de recherche' : 'Aucun univers synthétique ne correspond aux filtres sélectionnés'}
                  </p>
                  {hasActiveFilters && (
                    <button onClick={handleClearFilters} className="px-6 py-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-black uppercase tracking-widest text-cyan-400 hover:bg-cyan-500/20 transition-colors">
                      Réinitialiser les filtres
                    </button>
                  )}
                </div>
              )}

              {/* Grid view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'grid' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {data.results.map((u, i) => (
                    <UniverseGridCard key={u.id} universe={u} index={i} onSelect={handleSelectUniverse} />
                  ))}
                </div>
              )}

              {/* List view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'list' && (
                <div className="space-y-3">
                  {data.results.map((u, i) => (
                    <UniverseListRow key={u.id} universe={u} index={i} onSelect={handleSelectUniverse} />
                  ))}
                </div>
              )}

              {/* Pagination */}
              {data && data.pagination.total_pages > 1 && (
                <ResultsPagination
                  pagination={data.pagination}
                  onPrev={handlePrevPage}
                  onNext={handleNextPage}
                  onSelectPage={handleSelectPage}
                />
              )}
            </main>
          </div>
        </div>

        {/* ── Detail Modal ────────────────────────────────────── */}
        <AnimatePresence>
          {selectedUniverse && (
            <UniverseDetailPanel
              universe={selectedUniverse}
              onClose={handleCloseDetail}
            />
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  );
};

export default MultiverseCatalogPage;
