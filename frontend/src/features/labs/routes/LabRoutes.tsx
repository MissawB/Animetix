import { Route } from 'react-router-dom';
import { lazy } from 'react';

const MangaLabPage = lazy(() => import('../MangaLabPage'));
const AudioLabPage = lazy(() => import('../AudioLabPage'));
const LatentSpacePage = lazy(() => import('../LatentSpacePage'));
const SpatialLabPage = lazy(() => import('../SpatialLabPage'));
const VideoLabPage = lazy(() => import('../VideoLabPage'));
const SoundscapeLabPage = lazy(() => import('../SoundscapeLabPage'));
const SpeechToSpeechLabPage = lazy(() => import('../SpeechToSpeechLabPage'));
const SingularityLabPage = lazy(() => import('../SingularityLabPage'));
const LiquidNeuralNetworkLabPage = lazy(() => import('../LiquidNeuralNetworkLabPage'));
const VisualNexusPage = lazy(() => import('../VisualNexusPage'));
const LabHubPage = lazy(() => import('../LabHubPage'));

export const LabRoutes = (
  <>
    <Route path="/lab/" element={<LabHubPage />} />
    <Route path="/manga_lab/" element={<MangaLabPage />} />
    <Route path="/audio_lab/" element={<AudioLabPage />} />
    <Route path="/latent-space/" element={<LatentSpacePage />} />
    <Route path="/spatial-lab/" element={<SpatialLabPage />} />
    <Route path="/video-lab/" element={<VideoLabPage />} />
    <Route path="/visual-nexus/" element={<VisualNexusPage />} />
    <Route path="/soundscape-lab/" element={<SoundscapeLabPage />} />
    <Route path="/s2s-lab/" element={<SpeechToSpeechLabPage />} />
    <Route path="/experimental/" element={<SingularityLabPage />} />
    <Route path="/liquid-nn/" element={<LiquidNeuralNetworkLabPage />} />
  </>
);
