import { Route } from 'react-router-dom';
import { lazy } from 'react';

const GraphPage = lazy(() => import('../GraphPage'));
const LoreWorldMapPage = lazy(() => import('../LoreWorldMapPage'));

export const GraphRoutes = (
  <>
    <Route path="/graph/" element={<GraphPage />} />
    <Route path="/graph/map/" element={<LoreWorldMapPage />} />
  </>
);
