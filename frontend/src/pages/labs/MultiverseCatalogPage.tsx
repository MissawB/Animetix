import React from 'react';
import { Loader2, Globe } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
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
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
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
              <div className="mb-6 flex items-center justify-between">
                <p className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {data
                    ? data.pagination.total > 1
                      ? t('labs.multiverse.total_found_plural', '{{count}} universes found', {
                          count: data.pagination.total,
                        })
                      : t('labs.multiverse.total_found_singular', '{{count}} universe found', {
                          count: data.pagination.total,
                        })
                    : ''}
                  {debouncedSearch && ` pour "${debouncedSearch}"`}
                  {genre && ` • ${genre}`}
                </p>
                {isFetching && !isLoading && (
                  <Loader2 className="h-4 w-4 animate-spin text-[#FDB913]" />
                )}
              </div>

              {/* Loading state */}
              {isLoading && (
                <div
                  className={
                    viewMode === 'grid'
                      ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6'
                      : 'space-y-3'
                  }
                >
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className={`animate-pulse rounded-2xl border border-[#F4F1E8]/5 bg-[#0F1016] ${viewMode === 'grid' ? 'h-72' : 'h-20'}`}
                    />
                  ))}
                </div>
              )}

              {/* Empty state */}
              {!isLoading && data && data.results.length === 0 && (
                <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#F4F1E8]/15 px-8 py-24 text-center">
                  <Globe className="mb-6 h-16 w-16 text-[#8F94A5]/40" />
                  <h3 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/60">
                    {t('labs.multiverse.no_universe_found', 'Aucun univers trouvé')}
                  </h3>
                  <p className="mt-3 mb-6 max-w-md text-sm leading-relaxed text-[#8F94A5]">
                    {debouncedSearch
                      ? t('labs.multiverse.try_another_term', 'Essayez un autre terme de recherche')
                      : t(
                          'labs.multiverse.no_universe_filters',
                          'Aucun univers synthétique ne correspond aux filtres sélectionnés',
                        )}
                  </p>
                  {hasActiveFilters && (
                    <button
                      onClick={handleClearFilters}
                      className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-5 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
                    >
                      {t('labs.multiverse.reset_filters', 'Réinitialiser les filtres')}
                    </button>
                  )}
                </div>
              )}

              {/* Grid view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'grid' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {data.results.map((u, i) => (
                    <UniverseGridCard
                      key={u.id}
                      universe={u}
                      index={i}
                      onSelect={handleSelectUniverse}
                    />
                  ))}
                </div>
              )}

              {/* List view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'list' && (
                <div className="space-y-3">
                  {data.results.map((u, i) => (
                    <UniverseListRow
                      key={u.id}
                      universe={u}
                      index={i}
                      onSelect={handleSelectUniverse}
                    />
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
            <UniverseDetailPanel universe={selectedUniverse} onClose={handleCloseDetail} />
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  );
};

export default MultiverseCatalogPage;
