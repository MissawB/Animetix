import { Route } from 'react-router-dom';
import { lazy } from 'react';

const DailyChallengePage = lazy(() => import('../DailyChallengePage'));
const CustomConfigPage = lazy(() => import('../CustomConfigPage'));
const GraphPage = lazy(() => import('../../graph/GraphPage'));
const LoreWorldMapPage = lazy(() => import('../../graph/LoreWorldMapPage'));

export const UtilsRoutes = (
  <>
    <Route path="/daily-challenge/" element={<DailyChallengePage />} />
    <Route path="/custom-config/" element={<CustomConfigPage />} />
    <Route path="/graph/" element={<GraphPage />} />
    <Route path="/graph/world-map/" element={<LoreWorldMapPage />} />
  </>
);
