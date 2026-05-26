import { Route } from 'react-router-dom';
import { lazy } from 'react';

const DailyChallengePage = lazy(() => import('../DailyChallengePage'));
const CustomConfigPage = lazy(() => import('../CustomConfigPage'));
const GraphPage = lazy(() => import('../../graph/GraphPage'));

export const UtilsRoutes = (
  <>
    <Route path="/daily-challenge/" element={<DailyChallengePage />} />
    <Route path="/custom-config/" element={<CustomConfigPage />} />
    <Route path="/graph/" element={<GraphPage />} />
  </>
);
