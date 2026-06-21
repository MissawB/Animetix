import React, { useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useTachideskExplorer } from './tachidesk/hooks/useTachideskExplorer';
import { ExplorerHeader } from './tachidesk/components/ExplorerHeader';
import { ErrorPanel } from './tachidesk/components/ErrorPanel';
import { CatalogToolbar } from './tachidesk/components/CatalogToolbar';
import { MangaGrid } from './tachidesk/components/MangaGrid';
import { MangaDetailDrawer } from './tachidesk/components/MangaDetailDrawer';
import { ExtensionsTab } from './tachidesk/components/ExtensionsTab';

const TachideskExplorerPage: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    sources,
    selectedSource,
    setSelectedSource,
    searchQuery,
    setSearchQuery,
    mangas,
    selectedManga,
    setSelectedManga,
    chapters,
    extensions,
    extensionSearchQuery,
    setExtensionSearchQuery,
    actionProgress,
    loadingSources,
    loadingMangas,
    loadingDetails,
    loadingExtensions,
    importingChapter,
    error,
    setError,
    importStatus,
    fetchSources,
    fetchExtensions,
    handleSearch,
    selectManga,
    handleReadChapter,
    handleExtensionAction,
    getProxiedImageUrl,
    filteredExtensions,
    updateExtensions,
    installedExtensions,
    availableExtensions,
    isFavorited,
    favoriteStatus,
    togglingFavorite,
    toggleFavorite,
    updateFavoriteStatus,
  } = useTachideskExplorer();

  const handleSelectCatalogTab = useCallback(() => {
    setActiveTab('catalog');
  }, [setActiveTab]);

  const handleSelectExtensionsTab = useCallback(() => {
    setSelectedManga(null); // Close detail drawer
    setActiveTab('extensions');
  }, [setSelectedManga, setActiveTab]);

  const handleRefresh = useCallback(() => {
    if (activeTab === 'catalog') {
      void fetchSources();
    } else {
      void fetchExtensions();
    }
  }, [activeTab, fetchSources, fetchExtensions]);

  const handleDismissError = useCallback(() => {
    setError(null);
  }, [setError]);

  const handleCloseDrawer = useCallback(() => {
    setSelectedManga(null);
  }, [setSelectedManga]);

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white flex flex-col">
        {/* Header navigation bar */}
        <ExplorerHeader
          activeTab={activeTab}
          loadingSources={loadingSources}
          loadingExtensions={loadingExtensions}
          onSelectCatalogTab={handleSelectCatalogTab}
          onSelectExtensionsTab={handleSelectExtensionsTab}
          onRefresh={handleRefresh}
        />

        {/* Error panel */}
        {error && <ErrorPanel error={error} onDismiss={handleDismissError} />}

        <div className="flex-1 flex overflow-hidden">
          {/* Main panel */}
          {activeTab === 'catalog' ? (
            /* CATALOG TAB VIEW */
            <>
              <main className="flex-1 overflow-y-auto px-8 py-8 space-y-8">
                {/* Search and Source Selector */}
                <CatalogToolbar
                  sources={sources}
                  selectedSource={selectedSource}
                  searchQuery={searchQuery}
                  loadingSources={loadingSources}
                  loadingMangas={loadingMangas}
                  onSourceChange={setSelectedSource}
                  onSearchQueryChange={setSearchQuery}
                  onSubmit={handleSearch}
                />

                {/* Results Grid */}
                <MangaGrid
                  mangas={mangas}
                  selectedManga={selectedManga}
                  loadingMangas={loadingMangas}
                  onSelectManga={selectManga}
                  getProxiedImageUrl={getProxiedImageUrl}
                />
              </main>

              {/* Right panel: Sidebar Details */}
              <AnimatePresence>
                {selectedManga && (
                  <MangaDetailDrawer
                    selectedManga={selectedManga}
                    chapters={chapters}
                    loadingDetails={loadingDetails}
                    importStatus={importStatus}
                    importingChapter={importingChapter}
                    onClose={handleCloseDrawer}
                    onReadChapter={handleReadChapter}
                    getProxiedImageUrl={getProxiedImageUrl}
                    isFavorited={isFavorited}
                    favoriteStatus={favoriteStatus}
                    togglingFavorite={togglingFavorite}
                    onToggleFavorite={toggleFavorite}
                    onUpdateFavoriteStatus={updateFavoriteStatus}
                  />
                )}
              </AnimatePresence>
            </>
          ) : (
            /* EXTENSIONS TAB VIEW */
            <ExtensionsTab
              extensions={extensions}
              filteredExtensions={filteredExtensions}
              updateExtensions={updateExtensions}
              installedExtensions={installedExtensions}
              availableExtensions={availableExtensions}
              extensionSearchQuery={extensionSearchQuery}
              loadingExtensions={loadingExtensions}
              actionProgress={actionProgress}
              onSearchQueryChange={setExtensionSearchQuery}
              onAction={handleExtensionAction}
              getProxiedImageUrl={getProxiedImageUrl}
            />
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TachideskExplorerPage;
