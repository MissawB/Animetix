import { Route } from 'react-router-dom';
import { lazy } from 'react';

const PowerStationPage = lazy(() => import('../../../pages/billing/PowerStationPage'));
const PricingPage = lazy(() => import('../../../pages/billing/PricingPage'));

export const BillingRoutes = () => (
  <>
    <Route path="/pricing/" element={<PowerStationPage />} />
    <Route path="/sponsors/" element={<PricingPage />} />
    <Route path="/power-station/" element={<PowerStationPage />} />
  </>
);
