import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SupportDashboardPage = lazy(() => import('../../../pages/support/SupportDashboardPage'));

export const SupportRoutes = (
  <>
    <Route path="/support/" element={<SupportDashboardPage />} />
  </>
);
