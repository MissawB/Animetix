import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AdminEvalPage = lazy(() => import('../AdminEvalPage'));
const HealthPage = lazy(() => import('../HealthPage'));
const AdminDPOPage = lazy(() => import('../AdminDPOPage'));
const MLOpsDashboard = lazy(() => import('../MLOpsDashboard'));

export const AdminRoutes = (
  <>
    <Route path="/admin/dashboard/" element={<MLOpsDashboard />} />
    <Route path="/admin/ai_eval/" element={<AdminEvalPage />} />
    <Route path="/admin/health/" element={<HealthPage />} />
    <Route path="/admin/dpo-curation/" element={<AdminDPOPage />} />
  </>
);
