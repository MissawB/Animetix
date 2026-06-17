import { Route, Navigate } from 'react-router-dom';
import { lazy } from 'react';

const LabHubPage = lazy(() => import('../../../pages/labs/LabHubPage'));
const AudioLabPage = lazy(() => import('../../../pages/labs/AudioLabPage'));
const VideoLabPage = lazy(() => import('../../../pages/labs/VideoLabPage'));
const MangaLabPage = lazy(() => import('../../../pages/labs/MangaLabPage'));
const MangaVoicePage = lazy(() => import('../../../pages/labs/MangaVoicePage'));
const QuantumLabPage = lazy(() => import('../../../pages/labs/QuantumLabPage'));
const SynapticLabPage = lazy(() => import('../../../pages/labs/SynapticLabPage'));
const SwarmLabPage = lazy(() => import('../../../pages/labs/SwarmLabPage'));
const VisualNexusPage = lazy(() => import('../../../pages/labs/VisualNexusPage'));
const LatentSpacePage = lazy(() => import('../../../pages/labs/LatentSpacePage'));
const SpatialLabPage = lazy(() => import('../../../pages/labs/SpatialLabPage'));
const DioramaGalleryPage = lazy(() => import('../../../pages/labs/DioramaGalleryPage'));
const SoundscapeLabPage = lazy(() => import('../../../pages/labs/SoundscapeLabPage'));
const SpeechToSpeechLabPage = lazy(() => import('../../../pages/labs/SpeechToSpeechLabPage'));
const CinematicReconstructionPage = lazy(() => import('../../../pages/labs/CinematicReconstructionPage'));
const CompilerLabPage = lazy(() => import('../../../pages/labs/CompilerLabPage'));
const ForgeHubPage = lazy(() => import('../../../pages/labs/ForgeHubPage'));
const LiquidNeuralNetworkLabPage = lazy(() => import('../../../pages/labs/LiquidNeuralNetworkLabPage'));
const TreeOfThoughtsPage = lazy(() => import('../../../pages/labs/TreeOfThoughtsPage'));
const CognitionHubPage = lazy(() => import('../../../pages/labs/CognitionHubPage'));
const VoiceLabPage = lazy(() => import('../../../pages/labs/VoiceLabPage'));
const NeuralDiagnosticsPage = lazy(() => import('../../../pages/labs/NeuralDiagnosticsPage'));
const CoveOraclePage = lazy(() => import('../../../pages/labs/CoveOraclePage'));
const StrategyLabPage = lazy(() => import('../../../pages/labs/StrategyLabPage'));
const VideoRagPage = lazy(() => import('../../../pages/labs/VideoRagPage'));
const SingularityCommandCenterPage = lazy(() => import('../../../pages/labs/SingularityCommandCenterPage'));
const DeveloperPortalPage = lazy(() => import('../../../pages/dev/DeveloperPortalPage'));
const MonitoringConsolePage = lazy(() => import('../../../pages/dev/MonitoringConsolePage'));
const ApiHubPage = lazy(() => import('../../../pages/dev/ApiHubPage'));
const MultiverseStudioPage = lazy(() => import('../../../pages/labs/MultiverseStudioPage'));
const SeiyuuDiscoveryPage = lazy(() => import('../../../pages/labs/SeiyuuDiscoveryPage'));
const ObservabilityConsolePage = lazy(() => import('../../../pages/dev/ObservabilityConsolePage'));
const MLOpsConsolePage = lazy(() => import('../../../pages/dev/MLOpsConsolePage'));

export const LabRoutes = () => (
  <>
    <Route path="/lab/" element={<LabHubPage />} />
    <Route path="/lab/audio/" element={<AudioLabPage />} />
    <Route path="/lab/audio/seiyuu/" element={<SeiyuuDiscoveryPage />} />
    <Route path="/lab/video/" element={<VideoLabPage />} />
    <Route path="/lab/manga/" element={<MangaLabPage />} />
    <Route path="/lab/manga-voice/" element={<MangaVoicePage />} />
    <Route path="/lab/quantum/" element={<QuantumLabPage />} />
    <Route path="/lab/synaptic/" element={<SynapticLabPage />} />
    <Route path="/lab/swarm/" element={<SwarmLabPage />} />
    <Route path="/lab/visual-nexus/" element={<VisualNexusPage />} />
    <Route path="/lab/latent-space/" element={<LatentSpacePage />} />
    <Route path="/lab/spatial/" element={<SpatialLabPage />} />
    <Route path="/lab/spatial/gallery/" element={<DioramaGalleryPage />} />
    <Route path="/lab/soundscape/" element={<SoundscapeLabPage />} />
    <Route path="/lab/speech-to-speech/" element={<SpeechToSpeechLabPage />} />
    <Route path="/lab/cinematic/" element={<CinematicReconstructionPage />} />
    <Route path="/lab/compiler/" element={<CompilerLabPage />} />
    <Route path="/lab/forge-hub/" element={<ForgeHubPage />} />
    <Route path="/lab/liquid-neural-networks/" element={<LiquidNeuralNetworkLabPage />} />
    <Route path="/lab/tree-of-thoughts/" element={<TreeOfThoughtsPage />} />
    <Route path="/lab/tot/" element={<TreeOfThoughtsPage />} />
    <Route path="/lab/multiverse/" element={<MultiverseStudioPage />} />
    <Route path="/lab/multiverse-generator/" element={<Navigate to="/lab/multiverse/" replace />} />
    <Route path="/lab/multiverse-gallery/" element={<Navigate to="/lab/multiverse/" replace />} />

    <Route path="/lab/cognition-hub/" element={<CognitionHubPage />} />
    <Route path="/lab/voice/" element={<VoiceLabPage />} />
    <Route path="/lab/diagnostics/" element={<NeuralDiagnosticsPage />} />
    <Route path="/lab/cove-oracle/" element={<CoveOraclePage />} />
    <Route path="/lab/strategy/" element={<StrategyLabPage />} />
    <Route path="/lab/video-rag/" element={<VideoRagPage />} />
    <Route path="/lab/singularity/command-center/" element={<SingularityCommandCenterPage />} />
    <Route path="/developer/" element={<DeveloperPortalPage />} />
    <Route path="/dev/api-hub/" element={<ApiHubPage />} />
    <Route path="/dev/monitoring/" element={<MonitoringConsolePage />} />
    <Route path="/dev/observability/" element={<ObservabilityConsolePage />} />
    <Route path="/dev/mlops/" element={<MLOpsConsolePage />} />
  </>
);
