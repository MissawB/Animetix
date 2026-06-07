import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AdminDPOPage = lazy(() => import('../../../pages/admin/AdminDPOPage'));
const AdminEvalPage = lazy(() => import('../../../pages/admin/AdminEvalPage'));
const AdminGoldDatasetPage = lazy(() => import('../../../pages/admin/AdminGoldDatasetPage'));
const GraphDebuggerPage = lazy(() => import('../../../pages/admin/GraphDebuggerPage'));
const HealthPage = lazy(() => import('../../../pages/admin/HealthPage'));
const SOTABenchmarkPage = lazy(() => import('../../../pages/admin/SOTABenchmarkPage'));
const TTCMonitoringPage = lazy(() => import('../../../pages/admin/TTCMonitoringPage'));

export const AdminRoutes = (
  <>
    <Route path="/admin/dpo/" element={<AdminDPOPage />} />
    <Route path="/admin/eval/" element={<AdminEvalPage />} />
    <Route path="/admin/gold-dataset/" element={<AdminGoldDatasetPage />} />
    <Route path="/admin/graph-debugger/" element={<GraphDebuggerPage />} />
    <Route path="/admin/health/" element={<HealthPage />} />
    <Route path="/admin/sota-benchmark/" element={<SOTABenchmarkPage />} />
    <Route path="/admin/ttc-monitoring/" element={<TTCMonitoringPage />} />
  </>
);
