import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AkinetixPage = lazy(() => import('../../../pages/games/AkinetixPage'));
const AkinetixLobbyPage = lazy(() => import('../../../pages/games/AkinetixLobbyPage'));
const QuiEstCePage = lazy(() => import('../../../pages/games/QuiEstCePage'));
const BlindtestPage = lazy(() => import('../../../pages/games/BlindtestPage'));
const BlindtestLobbyPage = lazy(() => import('../../../pages/games/BlindtestLobbyPage'));
const ClassicGamePage = lazy(() => import('../../../pages/games/ClassicGamePage'));
const ClassicLobbyPage = lazy(() => import('../../../pages/games/ClassicLobbyPage'));
const ParadoxGamePage = lazy(() => import('../../../pages/games/ParadoxGamePage'));
const UndercoverRoom = lazy(() => import('../../../pages/games/UndercoverRoom'));
const CodeMangaRoom = lazy(() => import('../../../pages/games/CodeMangaRoom'));
const AniminatorPage = lazy(() => import('../../../pages/games/AniminatorPage'));
const CovertestPage = lazy(() => import('../../../pages/games/CovertestPage'));
const CovertestLobbyPage = lazy(() => import('../../../pages/games/CovertestLobbyPage'));
const VisionPage = lazy(() => import('../../../pages/games/VisionPage'));
const EmojiPage = lazy(() => import('../../../pages/games/EmojiPage'));
const ForgePage = lazy(() => import('../../../pages/games/ForgePage'));
const ForgeVNPage = lazy(() => import('../../../pages/games/ForgeVNPage'));
const AkinetixRLPage = lazy(() => import('../../../pages/games/AkinetixRLPage'));
const VsBattlePage = lazy(() => import('../../../pages/games/VsBattlePage'));
const GamesHubPage = lazy(() => import('../../../pages/games/GamesHubPage'));
const TheaterPage = lazy(() => import('../../../pages/games/TheaterPage'));
const WorldBossPage = lazy(() => import('../../../pages/games/WorldBossPage'));
const DuelLobbyPage = lazy(() => import('../../../pages/games/DuelLobbyPage'));
const DuelArenaPage = lazy(() => import('../../../pages/games/DuelArenaPage'));

export const GameRoutes = () => (
  <>
    <Route path="/games/hub/" element={<GamesHubPage />} />
    <Route path="/theater/" element={<TheaterPage />} />
    <Route path="/game/classic/" element={<ClassicLobbyPage />} />
    <Route path="/game/classic/play/" element={<ClassicGamePage />} />
    <Route path="/game/vsbattle/" element={<VsBattlePage />} />
    <Route path="/game/world-boss/active/" element={<WorldBossPage />} />
    <Route path="/game/duel/lobby/" element={<DuelLobbyPage />} />
    <Route path="/game/duel/arena/:roomCode/" element={<DuelArenaPage />} />
    <Route path="/forge/" element={<ForgePage />} />
    <Route path="/forge/vn/:fusionId/" element={<ForgeVNPage />} />
    <Route path="/akinetix/" element={<AkinetixLobbyPage />} />
    <Route path="/akinetix/play/" element={<AkinetixPage />} />
    <Route path="/quiz-who/" element={<QuiEstCePage />} />
    <Route path="/akinetix-expert/" element={<AkinetixRLPage />} />
    <Route path="/emoji/" element={<EmojiPage />} />
    <Route path="/blindtest/" element={<BlindtestLobbyPage />} />
    <Route path="/blindtest/play/" element={<BlindtestPage />} />
    <Route path="/vision/" element={<VisionPage />} />
    <Route path="/paradox/" element={<ParadoxGamePage />} />
    <Route path="/covertest/" element={<CovertestLobbyPage />} />
    <Route path="/covertest/play/" element={<CovertestPage />} />
    <Route path="/animinator/" element={<AniminatorPage />} />
    <Route path="/undercover/room/:roomCode/" element={<UndercoverRoom />} />
    <Route path="/codemanga/room/:roomCode/" element={<CodeMangaRoom />} />
  </>
);
