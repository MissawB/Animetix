import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Source, Manga, Chapter, Extension, ExtensionAction } from '../types';

const getErrorMessage = (err: unknown): string | undefined =>
  err instanceof Error ? err.message : undefined;

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
      const res = await fetch('/api/v1/explore/suwayomi/sources/');
      if (!res.ok) throw new Error('Impossible de charger les sources Suwayomi');
      const data: Source[] = await res.json();
      setSources(data);
      if (data.length > 0 && !selectedSource) {
        setSelectedSource(data[0].id);
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err) || 'Une erreur est survenue lors du chargement des sources');
    } finally {
      setLoadingSources(false);
    }
  }, [selectedSource]);

  const fetchExtensions = useCallback(async () => {
    setLoadingExtensions(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/explore/suwayomi/extensions/');
      if (!res.ok) throw new Error('Impossible de charger les extensions Suwayomi');
      const data: Extension[] = await res.json();
      setExtensions(data);
    } catch (err: unknown) {
      setError(getErrorMessage(err) || 'Erreur lors du chargement des extensions');
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
      const res = await fetch(`/api/v1/explore/suwayomi/search/?source_id=${selectedSource}&q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error('La recherche a échoué');
      const data: Manga[] = await res.json();
      setMangas(data);
    } catch (err: unknown) {
      setError(getErrorMessage(err) || 'Erreur lors de la recherche des mangas');
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

    try {
      const extId = `suwayomi:${selectedSource}:${manga.id}`;
      void fetch(`/api/v1/media/Manga/${extId}/favorite/`)
        .then(res => res.ok ? res.json() : { is_favorite: false })
        .then((data: { is_favorite: boolean }) => {
          setIsFavorited(data.is_favorite);
        })
        .catch(() => setIsFavorited(false));
      const res = await fetch(`/api/v1/media/Manga/${extId}/chapters/`);
      if (res.ok) {
        const data: Chapter[] = await res.json();
        setChapters(data);
      } else {
        const importRes = await fetch('/api/v1/explore/suwayomi/import/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            source_id: selectedSource,
            suwayomi_manga_id: manga.id
          })
        });
        if (importRes.ok) {
          const chRes = await fetch(`/api/v1/media/Manga/${extId}/chapters/`);
          if (chRes.ok) {
            setChapters(await chRes.json());
          }
        }
      }
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  }, [selectedSource]);

  const toggleFavorite = useCallback(async () => {
    if (!selectedManga) return;
    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
    setTogglingFavorite(true);
    try {
      const res = await fetch(`/api/v1/media/Manga/${extId}/favorite/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_id: selectedSource,
          suwayomi_manga_id: selectedManga.id
        })
      });
      if (res.ok) {
        const data: { is_favorite: boolean } = await res.json();
        setIsFavorited(data.is_favorite);
      } else {
        throw new Error('Failed to toggle favorite');
      }
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
      const res = await fetch('/api/v1/explore/suwayomi/import/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_id: selectedSource,
          suwayomi_manga_id: selectedManga.id
        })
      });

      if (!res.ok) throw new Error("Erreur d'importation");

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
    setActionProgress(prev => ({ ...prev, [pkgName]: true }));
    setError(null);
    try {
      const res = await fetch('/api/v1/explore/suwayomi/extensions/action/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ids: [pkgName],
          action
        })
      });
      if (!res.ok) throw new Error(`L'action ${action} a échoué`);

      // Refresh both list of extensions and sources list to sync
      await fetchExtensions();
      await fetchSources();
    } catch (err: unknown) {
      setError(getErrorMessage(err) || `Une erreur est survenue lors de l'exécution de l'action ${action}`);
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
    togglingFavorite,
    toggleFavorite,
  };
};
