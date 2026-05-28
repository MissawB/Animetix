import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AkinetixPage = lazy(() => import('../AkinetixPage'));
const BlindtestPage = lazy(() => import('../BlindtestPage'));
const ClassicGamePage = lazy(() => import('../ClassicGamePage'));
const ParadoxGamePage = lazy(() => import('../ParadoxGamePage'));
const UndercoverRoom = lazy(() => import('../UndercoverRoom'));
const CodeMangaRoom = lazy(() => import('../CodeMangaRoom'));
const AniminatorPage = lazy(() => import('../AniminatorPage'));
const CovertestPage = lazy(() => import('../CovertestPage'));
const VisionPage = lazy(() => import('../VisionPage'));
const EmojiPage = lazy(() => import('../EmojiPage'));
const ForgePage = lazy(() => import('../ForgePage'));
const ForgeVNPage = lazy(() => import('../ForgeVNPage'));
const AkinetixRLPage = lazy(() => import('../AkinetixRLPage'));
const VsBattlePage = lazy(() => import('../VsBattlePage'));

export const GameRoutes = (
  <>
    <Route path="/game/classic/" element={<ClassicGamePage />} />
    <Route path="/game/vsbattle/" element={<VsBattlePage />} />
    <Route path="/forge/" element={<ForgePage />} />
    <Route path="/forge/vn/:fusionId/" element={<ForgeVNPage />} />
    <Route path="/akinetix/" element={<AkinetixPage />} />
    <Route path="/akinetix-expert/" element={<AkinetixRLPage />} />
    <Route path="/emoji/" element={<EmojiPage />} />
    <Route path="/blindtest/" element={<BlindtestPage />} />
    <Route path="/vision/" element={<VisionPage />} />
    <Route path="/paradox/" element={<ParadoxGamePage />} />
    <Route path="/covertest/" element={<CovertestPage />} />
    <Route path="/animinator/" element={<AniminatorPage />} />
    <Route path="/undercover/room/:roomCode/" element={<UndercoverRoom />} />
    <Route path="/codemanga/room/:roomCode/" element={<CodeMangaRoom />} />
  </>
);
