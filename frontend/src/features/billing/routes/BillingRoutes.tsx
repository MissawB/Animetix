import { Route } from 'react-router-dom';
import { lazy } from 'react';

const PricingPage = lazy(() => import('../../../pages/billing/PricingPage'));

export const BillingRoutes = (
  <>
    <Route path="/pricing/" element={<PricingPage />} />
  </>
);
