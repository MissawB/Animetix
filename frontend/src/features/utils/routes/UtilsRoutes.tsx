import { Route } from 'react-router-dom';
import { lazy } from 'react';

const DailyChallengePage = lazy(() => import('../../../pages/utils/DailyChallengePage'));
const CustomConfigPage = lazy(() => import('../../../pages/utils/CustomConfigPage'));

export const UtilsRoutes = (
  <>
    <Route path="/daily-challenge/" element={<DailyChallengePage />} />
    <Route path="/custom-config/" element={<CustomConfigPage />} />
  </>
);
