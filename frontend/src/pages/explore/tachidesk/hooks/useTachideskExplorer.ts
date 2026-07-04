import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Source, Manga, Chapter, Extension, ExtensionAction } from '../types';
import { apiClient } from '../../../../utils/apiClient';
import { useAuthStore } from '../../../../store/authStore';

export const useTachideskExplorer = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'catalog' | 'extensions'>('catalog');

  // Catalog States
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [mangas, setMangas] = useState<Manga[]>([]);
  const [selectedManga, setSelectedManga] = useState<Manga | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [isFavorited, setIsFavorited] = useState(false);
  const [favoriteStatus, setFavoriteStatus] = useState<'reading' | 'completed' | 'plan_to_read' | null>(null);
  const [togglingFavorite, setTogglingFavorite] = useState(false);

  // Extension States
  const [extensions, setExtensions] = useState<Extension[]>([]);
  const [extensionSearchQuery, setExtensionSearchQuery] = useState('');
  const [actionProgress, setActionProgress] = useState<Record<string, boolean>>({});

  // Loading States
  const [loadingSources, setLoadingSources] = useState(false);
  const [loadingMangas, setLoadingMangas] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [loadingExtensions, setLoadingExtensions] = useState(false);
  const [importingChapter, setImportingChapter] = useState<string | null>(null);

  // Feedback Messages
  const [error, setError] = useState<string | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setLoadingSources(true);
    setError(null);
    try {
      const data: Source[] = await apiClient('/api/v1/explore/suwayomi/sources/', { skipToast: true });
      setSources(data);
      if (data.length > 0 && !selectedSource) {
        setSelectedSource(data[0].id);
      }
    } catch {
      setError('Impossible de charger les sources Suwayomi');
    } finally {
      setLoadingSources(false);
    }
  }, [selectedSource]);

  const fetchExtensions = useCallback(async () => {
    setLoadingExtensions(true);
    setError(null);
    try {
      const data: Extension[] = await apiClient('/api/v1/explore/suwayomi/extensions/', { skipToast: true });
      setExtensions(data);
    } catch {
      setError('Impossible de charger les extensions Suwayomi');
    } finally {
      setLoadingExtensions(false);
    }
  }, []);

  // Fetch available sources on mount. Defer in a microtask so the effect body
  // does not synchronously reach setState (avoids cascading renders).
  useEffect(() => {
    queueMicrotask(() => {
      void fetchSources();
    });
  }, [fetchSources]);

  // Fetch extensions when tab changes
  useEffect(() => {
    if (activeTab === 'extensions') {
      queueMicrotask(() => {
        void fetchExtensions();
      });
    }
  }, [activeTab, fetchExtensions]);

  const handleSearch = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedSource) return;

    setLoadingMangas(true);
    setError(null);
    setMangas([]);
    try {
      const data: Manga[] = await apiClient(
        `/api/v1/explore/suwayomi/search/?source_id=${selectedSource}&q=${encodeURIComponent(searchQuery)}`,
        { skipToast: true },
      );
      setMangas(data);
    } catch {
      setError('La recherche a échoué');
    } finally {
      setLoadingMangas(false);
    }
  }, [selectedSource, searchQuery]);

  // Trigger search on source change
  useEffect(() => {
    if (selectedSource && activeTab === 'catalog') {
      queueMicrotask(() => {
        void handleSearch();
      });
    }
  }, [selectedSource, activeTab, handleSearch]);

  const selectManga = useCallback(async (manga: Manga) => {
    setSelectedManga(manga);
    setChapters([]);
    setLoadingDetails(true);
    setError(null);
    setIsFavorited(false);
    setFavoriteStatus(null);

    try {
      const extId = `suwayomi:${selectedSource}:${manga.id}`;
      void apiClient(`/api/v1/media/Manga/${extId}/favorite/`, { skipToast: true })
        .then((data: { is_favorite: boolean; status: 'reading' | 'completed' | 'plan_to_read' | null }) => {
          setIsFavorited(data.is_favorite);
          setFavoriteStatus(data.status);
        })
        .catch(() => {
          setIsFavorited(false);
          setFavoriteStatus(null);
        });
      try {
        const data: Chapter[] = await apiClient(`/api/v1/media/Manga/${extId}/chapters/`, { skipToast: true });
        setChapters(data);
      } catch {
        // Not imported yet — import from Suwayomi, then retry fetching chapters.
        await apiClient('/api/v1/explore/suwayomi/import/', {
          method: 'POST',
          body: JSON.stringify({ source_id: selectedSource, suwayomi_manga_id: manga.id }),
          skipToast: true,
        });
        const data: Chapter[] = await apiClient(`/api/v1/media/Manga/${extId}/chapters/`, { skipToast: true });
        setChapters(data);
      }
    } catch {
      // best-effort: the details panel simply stays empty on failure
    } finally {
      setLoadingDetails(false);
    }
  }, [selectedSource]);

  const toggleFavorite = useCallback(async () => {
    if (!selectedManga) return;
    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
    setTogglingFavorite(true);
    try {
      const data: { is_favorite: boolean; status: 'reading' | 'completed' | 'plan_to_read' | null } =
        await apiClient(`/api/v1/media/Manga/${extId}/favorite/`, {
          method: 'POST',
          body: JSON.stringify({ source_id: selectedSource, suwayomi_manga_id: selectedManga.id }),
          skipToast: true,
        });
      setIsFavorited(data.is_favorite);
      setFavoriteStatus(data.status);
    } catch {
      setError("Impossible de mettre à jour le statut favori");
    } finally {
      setTogglingFavorite(false);
    }
  }, [selectedManga, selectedSource]);

  const updateFavoriteStatus = useCallback(async (status: 'reading' | 'completed' | 'plan_to_read') => {
    if (!selectedManga) return;
    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
    setTogglingFavorite(true);
    try {
      const data: { is_favorite: boolean; status: 'reading' | 'completed' | 'plan_to_read' | null } =
        await apiClient(`/api/v1/media/Manga/${extId}/favorite/`, {
          method: 'POST',
          body: JSON.stringify({ source_id: selectedSource, suwayomi_manga_id: selectedManga.id, status }),
          skipToast: true,
        });
      setIsFavorited(data.is_favorite);
      setFavoriteStatus(data.status);
    } catch {
      setError("Impossible de mettre à jour le statut favori");
    } finally {
      setTogglingFavorite(false);
    }
  }, [selectedManga, selectedSource]);

  const handleReadChapter = useCallback(async (chapter: Chapter) => {
    if (!selectedManga) return;
    setImportingChapter(chapter.id);
    setImportStatus("Synchronisation en cours...");

    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;

    try {
      await apiClient('/api/v1/explore/suwayomi/import/', {
        method: 'POST',
        body: JSON.stringify({ source_id: selectedSource, suwayomi_manga_id: selectedManga.id }),
        skipToast: true,
      });

      setImportStatus("Redirection vers le lecteur...");
      navigate(`/media/manga/${extId}/${chapter.chapterNumber}/`);
    } catch {
      setError("Impossible d'importer le chapitre. Vérifiez votre connexion Suwayomi.");
      setImportStatus(null);
    } finally {
      setImportingChapter(null);
    }
  }, [selectedManga, selectedSource, navigate]);

  const handleExtensionAction = useCallback(async (pkgName: string, action: ExtensionAction) => {
    // Installer/mettre à jour/désinstaller mute le serveur Suwayomi → login requis.
    // On tranche en amont pour un message clair au lieu d'un 401 opaque (la liste,
    // elle, reste consultable en anonyme).
    if (!useAuthStore.getState().isAuthenticated) {
      setError('Connecte-toi pour installer ou mettre à jour des extensions.');
      return;
    }
    setActionProgress(prev => ({ ...prev, [pkgName]: true }));
    setError(null);
    try {
      await apiClient('/api/v1/explore/suwayomi/extensions/action/', {
        method: 'POST',
        body: JSON.stringify({ ids: [pkgName], action }),
        skipToast: true,
      });

      // Refresh both list of extensions and sources list to sync
      await fetchExtensions();
      await fetchSources();
    } catch {
      setError(`L'action ${action} a échoué`);
    } finally {
      setActionProgress(prev => ({ ...prev, [pkgName]: false }));
    }
  }, [fetchExtensions, fetchSources]);

  const getProxiedImageUrl = useCallback((url: string) => {
    if (!url) return 'https://via.placeholder.com/300x450';
    if (url.startsWith('/api/')) return url;
    try {
      const utf8Bytes = new TextEncoder().encode(url);
      const binaryString = Array.from(utf8Bytes, byte => String.fromCharCode(byte)).join('');
      const encoded = btoa(binaryString);
      return `/api/v1/media/Manga/suwayomi-image/?page_url=${encoded}`;
    } catch {
      return url;
    }
  }, []);

  // Extensions filtering
  const filteredExtensions = useMemo(() => extensions.filter(ext =>
    ext.name.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
    ext.pkgName.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
    ext.lang.toLowerCase().includes(extensionSearchQuery.toLowerCase())
  ), [extensions, extensionSearchQuery]);

  const updateExtensions = useMemo(() => filteredExtensions.filter(ext => ext.hasUpdate), [filteredExtensions]);
  const installedExtensions = useMemo(() => filteredExtensions.filter(ext => ext.isInstalled && !ext.hasUpdate), [filteredExtensions]);
  const availableExtensions = useMemo(() => filteredExtensions.filter(ext => !ext.isInstalled), [filteredExtensions]);

  return {
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
  };
};
