import { Route } from 'react-router-dom';
import { lazy } from 'react';

const PowerStationPage = lazy(() => import('../../../pages/billing/PowerStationPage'));

export const BillingRoutes = () => (
  <>
    <Route path="/pricing/" element={<PowerStationPage />} />
    <Route path="/power-station/" element={<PowerStationPage />} />
  </>
);
