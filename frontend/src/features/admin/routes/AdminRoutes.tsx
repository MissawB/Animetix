import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AdminEvalPage = lazy(() => import('../AdminEvalPage'));
const HealthPage = lazy(() => import('../HealthPage'));
const AdminDPOPage = lazy(() => import('../AdminDPOPage'));
const MLOpsDashboard = lazy(() => import('../MLOpsDashboard'));
const AdminDSPyDashboard = lazy(() => import('../AdminDSPyDashboard'));
const AdminGoldDatasetPage = lazy(() => import('../AdminGoldDatasetPage'));
const CurationDashboard = lazy(() => import('../CurationDashboard'));
const SOTABenchmarkPage = lazy(() => import('../SOTABenchmarkPage'));
const GraphDebuggerPage = lazy(() => import('../GraphDebuggerPage'));

export const AdminRoutes = (
  <>
    <Route path="/admin/dashboard/" element={<MLOpsDashboard />} />
    <Route path="/admin/dspy-optimizer/" element={<AdminDSPyDashboard />} />
    <Route path="/admin/ai_eval/" element={<AdminEvalPage />} />
    <Route path="/admin/health/" element={<HealthPage />} />
    <Route path="/admin/dpo-curation/" element={<AdminDPOPage />} />
    <Route path="/admin/gold-dataset/" element={<AdminGoldDatasetPage />} />
    <Route path="/admin/curation/" element={<CurationDashboard />} />
    <Route path="/admin/sota-benchmarks/" element={<SOTABenchmarkPage />} />
    <Route path="/admin/graph-debugger/" element={<GraphDebuggerPage />} />
  </>
);
