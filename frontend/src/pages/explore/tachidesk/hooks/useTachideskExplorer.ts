import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import type { Source, Manga, Chapter, Extension, ExtensionAction, MangaDetails } from '../types';
import { apiClient } from '../../../../utils/apiClient';
import { useAuthStore } from '../../../../store/authStore';
import { exploreService } from '../../../../features/explore/services/exploreService';
import {
  useMangaProgress,
  mangaProgressKey,
} from '../../../../features/manga-reader/progress/useMangaProgress';
import { markChaptersRead } from '../../../../features/manga-reader/progress/progressService';

/**
 * Message d'erreur clair pour l'explorateur Suwayomi. Quand le backend renvoie
 * un 503 « suwayomi_unreachable » (serveur non démarré), on affiche son message
 * actionnable ; sinon on retombe sur un libellé générique.
 */
const suwayomiErrorMessage = (err: unknown, fallback: string): string => {
  const e = err as { status?: number; message?: string } | null;
  if (e?.status === 503 && e.message) return e.message;
  return fallback;
};

export const useTachideskExplorer = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'catalog' | 'extensions'>('catalog');

  // Catalog States
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [mangas, setMangas] = useState<Manga[]>([]);
  const [loadingSources, setLoadingSources] = useState<boolean>(false);
  const [loadingMangas, setLoadingMangas] = useState<boolean>(false);
  // Pagination du catalogue (fetchSourceManga est paginé côté Suwayomi).
  const [page, setPage] = useState<number>(1);
  const [hasNextPage, setHasNextPage] = useState<boolean>(false);
  // Dernière page (calculée en fond) : permet « aller à la fin » et de borner.
  const [lastPage, setLastPage] = useState<number | null>(null);

  // Extensions States
  const [extensions, setExtensions] = useState<Extension[]>([]);
  const [extensionSearchQuery, setExtensionSearchQuery] = useState<string>('');
  const [loadingExtensions, setLoadingExtensions] = useState<boolean>(false);
  const [actionProgress, setActionProgress] = useState<Record<string, boolean>>({});

  // Details Modal States
  const [selectedManga, setSelectedManga] = useState<Manga | null>(null);
  const [mangaDetails, setMangaDetails] = useState<MangaDetails | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [isFavorited, setIsFavorited] = useState<boolean>(false);
  const [favoriteStatus, setFavoriteStatus] = useState<
    'reading' | 'completed' | 'plan_to_read' | null
  >(null);
  const [togglingFavorite, setTogglingFavorite] = useState<boolean>(false);
  const [importingChapter, setImportingChapter] = useState<string | null>(null);

  // General States
  const [error, setError] = useState<string | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  // Progression de lecture (Task 7/9) : la popup est purement présentationnelle,
  // l'appel réseau (et son gating anonyme) vit ici. Même id que celui utilisé
  // par le lecteur pour un manga Suwayomi non encore importé.
  const isAuthenticated = useAuthStore.getState().isAuthenticated;
  const progressMediaId = selectedManga
    ? `suwayomi:${selectedSource}:${selectedManga.id}`
    : undefined;
  const { data: progressSummary, byChapter: progressByChapter } = useMangaProgress(
    progressMediaId,
    isAuthenticated,
  );

  const onToggleChapterRead = useCallback(
    (chapterNumber: number, next: boolean) => {
      if (!progressMediaId) return;
      void markChaptersRead(progressMediaId, [chapterNumber], next).then(() =>
        queryClient.invalidateQueries({ queryKey: mangaProgressKey(progressMediaId) }),
      );
    },
    [progressMediaId, queryClient],
  );

  const fetchSources = useCallback(async () => {
    setLoadingSources(true);
    setError(null);
    try {
      const data = await exploreService.getSuwayomiSources();
      setSources(data as unknown as Source[]);
      if (data.length > 0 && !selectedSource) {
        setSelectedSource(data[0].id);
      }
    } catch (err) {
      setError(suwayomiErrorMessage(err, 'Impossible de charger les sources Suwayomi'));
    } finally {
      setLoadingSources(false);
    }
  }, [selectedSource]);

  const fetchExtensions = useCallback(async () => {
    setLoadingExtensions(true);
    setError(null);
    try {
      const data = await exploreService.getSuwayomiExtensions();
      setExtensions(data as unknown as Extension[]);
    } catch (err) {
      setError(suwayomiErrorMessage(err, 'Impossible de charger les extensions Suwayomi'));
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

  const fetchMangas = useCallback(
    async (pageNum: number) => {
      if (!selectedSource) return;
      setLoadingMangas(true);
      setError(null);
      try {
        const data: { mangas?: Manga[]; hasNextPage?: boolean } = await apiClient(
          `/api/v1/explore/suwayomi/search/?source_id=${selectedSource}&q=${encodeURIComponent(
            searchQuery,
          )}&page=${pageNum}`,
          { skipToast: true },
        );
        setMangas(data?.mangas ?? []);
        setHasNextPage(!!data?.hasNextPage);
      } catch (err) {
        setMangas([]);
        setHasNextPage(false);
        setError(suwayomiErrorMessage(err, 'La recherche a échoué'));
      } finally {
        setLoadingMangas(false);
      }
    },
    [selectedSource, searchQuery],
  );

  // Dernière page, calculée en fond (le seek coûte quelques requêtes, mis en
  // cache côté backend). Débloque « aller à la fin » + affiche « / N ».
  const fetchLastPage = useCallback(async () => {
    if (!selectedSource) return;
    try {
      const d: { lastPage?: number } = await apiClient(
        `/api/v1/explore/suwayomi/last-page/?source_id=${selectedSource}&q=${encodeURIComponent(
          searchQuery,
        )}`,
        { skipToast: true },
      );
      setLastPage(typeof d?.lastPage === 'number' ? d.lastPage : null);
    } catch {
      setLastPage(null);
    }
  }, [selectedSource, searchQuery]);

  // Nouvelle recherche (submit ou changement de source) : on repart page 1
  // et on recalcule la dernière page pour la nouvelle requête.
  const handleSearch = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      setPage(1);
      setLastPage(null);
      await fetchMangas(1);
      void fetchLastPage();
    },
    [fetchMangas, fetchLastPage],
  );

  // Navigation de page (précédent / suivant / n° / première / dernière).
  const goToPage = useCallback(
    (pageNum: number) => {
      const target = Math.max(1, pageNum);
      setPage(target);
      void fetchMangas(target);
    },
    [fetchMangas],
  );

  // Saut alphabétique : va à la page où commence une lettre (catalogue trié).
  const seekLetter = useCallback(
    async (letter: string) => {
      if (!selectedSource) return;
      setLoadingMangas(true);
      try {
        const d: { page?: number; lastPage?: number } = await apiClient(
          `/api/v1/explore/suwayomi/seek-letter/?source_id=${selectedSource}&q=${encodeURIComponent(
            searchQuery,
          )}&letter=${encodeURIComponent(letter)}`,
          { skipToast: true },
        );
        if (typeof d?.lastPage === 'number') setLastPage(d.lastPage);
        const target = Math.max(1, d?.page ?? 1);
        setPage(target);
        await fetchMangas(target);
      } catch (err) {
        setError(suwayomiErrorMessage(err, 'Saut alphabétique impossible'));
        setLoadingMangas(false);
      }
    },
    [selectedSource, searchQuery, fetchMangas],
  );

  // Recharge la page 1 quand la source (ou l'onglet) change, et (re)calcule la
  // dernière page en tâche de fond.
  useEffect(() => {
    if (selectedSource && activeTab === 'catalog') {
      queueMicrotask(() => {
        setPage(1);
        setLastPage(null);
        void fetchMangas(1);
        void fetchLastPage();
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSource, activeTab]);

  const selectManga = useCallback(
    async (manga: Manga) => {
      setSelectedManga(manga);
      setChapters([]);
      setMangaDetails(null);
      setLoadingDetails(true);
      setError(null);
      setIsFavorited(false);
      setFavoriteStatus(null);

      // Fiche complète (description, titre, auteur, genres) en parallèle,
      // non bloquant : la popup s'ouvre tout de suite avec ce qu'on a.
      void apiClient(`/api/v1/explore/suwayomi/manga-details/?suwayomi_manga_id=${manga.id}`, {
        skipToast: true,
      })
        .then((data: MangaDetails) => setMangaDetails(data || null))
        .catch(() => setMangaDetails(null));

      try {
        const extId = `suwayomi:${selectedSource}:${manga.id}`;
        void apiClient(`/api/v1/media/Manga/${extId}/favorite/`, { skipToast: true })
          .then(
            (data: {
              is_favorite: boolean;
              status: 'reading' | 'completed' | 'plan_to_read' | null;
            }) => {
              setIsFavorited(data.is_favorite);
              setFavoriteStatus(data.status);
            },
          )
          .catch(() => {
            setIsFavorited(false);
            setFavoriteStatus(null);
          });
        // Chapitres lus DIRECTEMENT depuis Suwayomi (public, pas d'import :
        // l'import dans le catalogue local n'a lieu qu'à la lecture d'un chapitre).
        const chData: Chapter[] = await apiClient(
          `/api/v1/explore/suwayomi/manga-chapters/?suwayomi_manga_id=${manga.id}`,
          { skipToast: true },
        );
        setChapters(Array.isArray(chData) ? chData : []);
      } catch {
        // best-effort: the details panel simply stays empty on failure
      } finally {
        setLoadingDetails(false);
      }
    },
    [selectedSource],
  );

  const toggleFavorite = useCallback(async () => {
    if (!selectedManga) return;
    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
    setTogglingFavorite(true);
    try {
      const data: {
        is_favorite: boolean;
        status: 'reading' | 'completed' | 'plan_to_read' | null;
      } = await apiClient(`/api/v1/media/Manga/${extId}/favorite/`, {
        method: 'POST',
        body: JSON.stringify({ source_id: selectedSource, suwayomi_manga_id: selectedManga.id }),
        skipToast: true,
      });
      setIsFavorited(data.is_favorite);
      setFavoriteStatus(data.status);
    } catch {
      setError('Impossible de mettre à jour le statut favori');
    } finally {
      setTogglingFavorite(false);
    }
  }, [selectedManga, selectedSource]);

  const updateFavoriteStatus = useCallback(
    async (status: 'reading' | 'completed' | 'plan_to_read') => {
      if (!selectedManga) return;
      const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;
      setTogglingFavorite(true);
      try {
        const data: {
          is_favorite: boolean;
          status: 'reading' | 'completed' | 'plan_to_read' | null;
        } = await apiClient(`/api/v1/media/Manga/${extId}/favorite/`, {
          method: 'POST',
          body: JSON.stringify({
            source_id: selectedSource,
            suwayomi_manga_id: selectedManga.id,
            status,
          }),
          skipToast: true,
        });
        setIsFavorited(data.is_favorite);
        setFavoriteStatus(data.status);
      } catch {
        setError('Impossible de mettre à jour le statut favori');
      } finally {
        setTogglingFavorite(false);
      }
    },
    [selectedManga, selectedSource],
  );

  const handleReadChapter = useCallback(
    async (chapter: Chapter) => {
      if (!selectedManga) return;
      setImportingChapter(String(chapter.id));
      setImportStatus('Synchronisation en cours...');

      const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;

      try {
        await exploreService.importSuwayomiManga({
          sourceId: selectedSource,
          mangaUrl: selectedManga.id,
        });

        setImportStatus('Redirection vers le lecteur...');
        navigate(`/media/manga/${extId}/${chapter.chapterNumber}/`);
      } catch {
        setError("Impossible d'importer le chapitre. Vérifiez votre connexion Suwayomi.");
        setImportStatus(null);
      } finally {
        setImportingChapter(null);
      }
    },
    [selectedManga, selectedSource, navigate],
  );

  const handleExtensionAction = useCallback(
    async (pkgName: string, action: ExtensionAction) => {
      // Installer/mettre à jour/désinstaller mute le serveur Suwayomi → login requis.
      // On tranche en amont pour un message clair au lieu d'un 401 opaque (la liste,
      // elle, reste consultable en anonyme).
      if (!useAuthStore.getState().isAuthenticated) {
        setError('Connecte-toi pour installer ou mettre à jour des extensions.');
        return;
      }
      setActionProgress((prev) => ({ ...prev, [pkgName]: true }));
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
        setActionProgress((prev) => ({ ...prev, [pkgName]: false }));
      }
    },
    [fetchExtensions, fetchSources],
  );

  const getProxiedImageUrl = useCallback((url: string) => {
    if (!url) return 'https://via.placeholder.com/300x450';
    // Ne PAS re-proxifier une URL déjà servie par l'app (manga importé). En
    // revanche, les vignettes Suwayomi (`/api/v1/manga/{id}/thumbnail`) et icônes
    // d'extensions commencent aussi par `/api/` : elles DOIVENT passer par le proxy.
    if (url.startsWith('/api/v1/media/')) return url;
    try {
      const utf8Bytes = new TextEncoder().encode(url);
      const binaryString = Array.from(utf8Bytes, (byte) => String.fromCharCode(byte)).join('');
      const encoded = btoa(binaryString);
      return `/api/v1/media/Manga/suwayomi-image/?page_url=${encoded}`;
    } catch {
      return url;
    }
  }, []);

  // Extensions filtering
  const filteredExtensions = useMemo(
    () =>
      extensions.filter(
        (ext) =>
          ext.name.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
          ext.pkgName.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
          ext.lang.toLowerCase().includes(extensionSearchQuery.toLowerCase()),
      ),
    [extensions, extensionSearchQuery],
  );

  const updateExtensions = useMemo(
    () => filteredExtensions.filter((ext) => ext.hasUpdate),
    [filteredExtensions],
  );
  const installedExtensions = useMemo(
    () => filteredExtensions.filter((ext) => ext.isInstalled && !ext.hasUpdate),
    [filteredExtensions],
  );
  const availableExtensions = useMemo(
    () => filteredExtensions.filter((ext) => !ext.isInstalled),
    [filteredExtensions],
  );

  return {
    activeTab,
    setActiveTab,
    sources,
    selectedSource,
    setSelectedSource,
    searchQuery,
    setSearchQuery,
    mangas,
    page,
    hasNextPage,
    lastPage,
    goToPage,
    seekLetter,
    selectedManga,
    setSelectedManga,
    mangaDetails,
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
    // Visiteur anonyme : ces trois props restent `undefined`, c'est le signal
    // que consomme MangaDetailModal (purement présentationnel) pour afficher
    // l'invite « Connecte-toi » à la place du suivi de lecture.
    progressByChapter: isAuthenticated ? progressByChapter : undefined,
    progressSummary: isAuthenticated ? (progressSummary ?? null) : undefined,
    onToggleChapterRead: isAuthenticated ? onToggleChapterRead : undefined,
  };
};
