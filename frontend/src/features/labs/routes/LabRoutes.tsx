import { Route } from 'react-router-dom';
import { lazy } from 'react';

const LabHubPage = lazy(() => import('../../../pages/labs/LabHubPage'));
const AudioLabPage = lazy(() => import('../../../pages/labs/AudioLabPage'));
const VideoLabPage = lazy(() => import('../../../pages/labs/VideoLabPage'));
const MangaLabPage = lazy(() => import('../../../pages/labs/MangaLabPage'));
const QuantumLabPage = lazy(() => import('../../../pages/labs/QuantumLabPage'));
const SynapticLabPage = lazy(() => import('../../../pages/labs/SynapticLabPage'));
const SwarmLabPage = lazy(() => import('../../../pages/labs/SwarmLabPage'));
const VisualNexusPage = lazy(() => import('../../../pages/labs/VisualNexusPage'));
const LatentSpacePage = lazy(() => import('../../../pages/labs/LatentSpacePage'));
const SpatialLabPage = lazy(() => import('../../../pages/labs/SpatialLabPage'));
const SoundscapeLabPage = lazy(() => import('../../../pages/labs/SoundscapeLabPage'));
const SpeechToSpeechLabPage = lazy(() => import('../../../pages/labs/SpeechToSpeechLabPage'));
const CinematicReconstructionPage = lazy(() => import('../../../pages/labs/CinematicReconstructionPage'));
const CompilerLabPage = lazy(() => import('../../../pages/labs/CompilerLabPage'));
const ForgeHubPage = lazy(() => import('../../../pages/labs/ForgeHubPage'));
const LiquidNeuralNetworkLabPage = lazy(() => import('../../../pages/labs/LiquidNeuralNetworkLabPage'));
const TreeOfThoughtsPage = lazy(() => import('../../../pages/labs/TreeOfThoughtsPage'));
const MultiverseLabPage = lazy(() => import('../../../pages/labs/MultiverseLabPage'));
const MultiverseGalleryPage = lazy(() => import('../../../pages/labs/MultiverseGalleryPage'));
const CognitionHubPage = lazy(() => import('../../../pages/labs/CognitionHubPage'));

export const LabRoutes = (
  <>
    <Route path="/lab/" element={<LabHubPage />} />
    <Route path="/lab/audio/" element={<AudioLabPage />} />
    <Route path="/lab/video/" element={<VideoLabPage />} />
    <Route path="/lab/manga/" element={<MangaLabPage />} />
    <Route path="/lab/quantum/" element={<QuantumLabPage />} />
    <Route path="/lab/synaptic/" element={<SynapticLabPage />} />
    <Route path="/lab/swarm/" element={<SwarmLabPage />} />
    <Route path="/lab/visual-nexus/" element={<VisualNexusPage />} />
    <Route path="/lab/latent-space/" element={<LatentSpacePage />} />
    <Route path="/lab/spatial/" element={<SpatialLabPage />} />
    <Route path="/lab/soundscape/" element={<SoundscapeLabPage />} />
    <Route path="/lab/speech-to-speech/" element={<SpeechToSpeechLabPage />} />
    <Route path="/lab/cinematic/" element={<CinematicReconstructionPage />} />
    <Route path="/lab/compiler/" element={<CompilerLabPage />} />
    <Route path="/lab/forge-hub/" element={<ForgeHubPage />} />
    <Route path="/lab/liquid-neural-networks/" element={<LiquidNeuralNetworkLabPage />} />
    <Route path="/lab/tree-of-thoughts/" element={<TreeOfThoughtsPage />} />
    <Route path="/lab/multiverse-generator/" element={<MultiverseLabPage />} />
    <Route path="/lab/multiverse-gallery/" element={<MultiverseGalleryPage />} />
    <Route path="/lab/cognition-hub/" element={<CognitionHubPage />} />
  </>
);
