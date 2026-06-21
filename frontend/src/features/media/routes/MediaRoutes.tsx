import { Route } from 'react-router-dom';
import { lazy } from 'react';

const MediaDetailPage = lazy(() => import('../../../pages/media/MediaDetailPage'));
const MangaReaderPage = lazy(() => import('../../../pages/media/MangaReaderPage'));
const OfflineMangaPage = lazy(() => import('../../../pages/media/OfflineMangaPage'));
const CharacterDetailPage = lazy(() => import('../../../pages/media/CharacterDetailPage'));
const StaffDetailPage = lazy(() => import('../../../pages/media/StaffDetailPage'));

export const MediaRoutes = () => (
  <>
    <Route path="/media/:mediaId/" element={<MediaDetailPage />} />
    <Route path="/media/:mediaType/:itemId/" element={<MediaDetailPage />} />
    <Route path="/media/manga/offline/" element={<OfflineMangaPage />} />
    <Route path="/media/manga/:mediaId/:chapterId/" element={<MangaReaderPage />} />
    <Route path="/character/:characterId/" element={<CharacterDetailPage />} />
    <Route path="/staff/:staffId/" element={<StaffDetailPage />} />
  </>
);
