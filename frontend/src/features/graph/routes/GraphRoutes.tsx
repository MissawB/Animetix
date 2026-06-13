import { Route } from 'react-router-dom';
import { lazy } from 'react';

const GraphPage = lazy(() => import('../../../pages/graph/GraphPage'));
const LoreWorldMapPage = lazy(() => import('../../../pages/graph/LoreWorldMapPage'));
const GraphNeighborhoodPage = lazy(() => import('../../../pages/graph/GraphNeighborhoodPage'));

export const GraphRoutes = (
  <>
    <Route path="/graph/" element={<GraphPage />} />
    <Route path="/graph/map/" element={<LoreWorldMapPage />} />
    <Route path="/graph/neighborhood/" element={<GraphNeighborhoodPage />} />
  </>
);
