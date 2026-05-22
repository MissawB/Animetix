import { Route } from 'react-router-dom';
import { lazy } from 'react';

const MangaLabPage = lazy(() => import('../MangaLabPage'));
const AudioLabPage = lazy(() => import('../AudioLabPage'));
const LatentSpacePage = lazy(() => import('../LatentSpacePage'));
const SpatialLabPage = lazy(() => import('../SpatialLabPage'));

export const LabRoutes = (
  <>
    <Route path="/manga_lab/" element={<MangaLabPage />} />
    <Route path="/audio_lab/" element={<AudioLabPage />} />
    <Route path="/latent-space/" element={<LatentSpacePage />} />
    <Route path="/spatial-lab/" element={<SpatialLabPage />} />
  </>
);
