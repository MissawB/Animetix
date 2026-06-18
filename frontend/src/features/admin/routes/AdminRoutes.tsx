import { Route } from 'react-router-dom';
import { lazy } from 'react';

const AdminCurationPage = lazy(() => import('../../../pages/admin/AdminCurationPage'));
const AdminEvalPage = lazy(() => import('../../../pages/admin/AdminEvalPage'));
const AdminGoldDatasetPage = lazy(() => import('../../../pages/admin/AdminGoldDatasetPage'));
const AdminDSPyDashboard = lazy(() => import('../../../pages/admin/AdminDSPyDashboard'));
const GraphDebuggerPage = lazy(() => import('../../../pages/admin/GraphDebuggerPage'));
const HealthPage = lazy(() => import('../../../pages/admin/HealthPage'));
const MLOpsDashboard = lazy(() => import('../../../pages/admin/MLOpsDashboard'));
const SOTABenchmarkPage = lazy(() => import('../../../pages/admin/SOTABenchmarkPage'));
const TTCMonitoringPage = lazy(() => import('../../../pages/admin/TTCMonitoringPage'));
const UserManagementPage = lazy(() => import('../../../pages/admin/UserManagementPage'));
const AdminDashboardPage = lazy(() => import('../../../pages/admin/AdminDashboardPage'));
const FinancialDashboardPage = lazy(() => import('../../../pages/admin/FinancialDashboardPage'));
const AISafetyAuditPage = lazy(() => import('../../../pages/admin/AISafetyAuditPage'));
const EconomicAuditPage = lazy(() => import('../../../pages/admin/EconomicAuditPage'));
const ObservabilityConsolePage = lazy(() => import('../../../pages/dev/ObservabilityConsolePage'));

export const AdminRoutes = () => (
  <>
    <Route path="/admin/" element={<AdminDashboardPage />} />
    <Route path="/admin/dashboard/" element={<AdminDashboardPage />} />
    <Route path="/admin/mlops/" element={<MLOpsDashboard />} />
    <Route path="/admin/safety/" element={<AISafetyAuditPage />} />
    <Route path="/admin/safety-audit/" element={<AISafetyAuditPage />} />
    <Route path="/admin/economics/" element={<EconomicAuditPage />} />
    <Route path="/admin/observability/" element={<ObservabilityConsolePage />} />
    <Route path="/admin/curation/" element={<AdminCurationPage />} />
    <Route path="/admin/dspy/" element={<AdminDSPyDashboard />} />
    <Route path="/admin/eval/" element={<AdminEvalPage />} />
    <Route path="/admin/gold-dataset/" element={<AdminGoldDatasetPage />} />
    <Route path="/admin/graph-debugger/" element={<GraphDebuggerPage />} />
    <Route path="/admin/health/" element={<HealthPage />} />
    <Route path="/admin/monitoring/" element={<HealthPage />} />
    <Route path="/admin/sota-benchmark/" element={<SOTABenchmarkPage />} />
    <Route path="/admin/ttc-monitoring/" element={<TTCMonitoringPage />} />
    <Route path="/admin/financials/" element={<FinancialDashboardPage />} />
    <Route path="/admin/users/" element={<UserManagementPage />} />
  </>
);
