import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './Layout';
import { GameRoutes } from '../features/games/routes/GameRoutes';
import { SocialRoutes } from '../features/social/routes/SocialRoutes';
import { LabRoutes } from '../features/labs/routes/LabRoutes';
import { MediaRoutes } from '../features/media/routes/MediaRoutes';
import { CompanionRoutes } from '../features/companion/routes/CompanionRoutes';
import { SearchRoutes } from '../features/search/routes/SearchRoutes';
import { AdminRoutes } from '../features/admin/routes/AdminRoutes';
import { UtilsRoutes } from '../features/utils/routes/UtilsRoutes';
import { AuthRoutes } from '../features/auth/routes/AuthRoutes';
import { GraphRoutes } from '../features/graph/routes/GraphRoutes';
import { BillingRoutes } from '../features/billing/routes/BillingRoutes';
import { ExploreRoutes } from '../features/explore/routes/ExploreRoutes';
import { SupportRoutes } from '../features/support/routes/SupportRoutes';
import { ResearchRoutes } from '../features/research/routes/ResearchRoutes';
import App from '../App';

const Loading: React.FC = () => <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em]">Initialisation du système...</div>;

/**
 * Determine the app basename based on URL structure.
 * Handles /static/ prefix from Django/Vite and potential language prefixes.
 */
const getBasename = () => {
  const path = window.location.pathname;
  
  // Dev mode with Vite often uses /static/ as base
  if (path.startsWith('/static')) {
    const parts = path.split('/');
    // Check if next part is a language code (fr/en)
    if (parts.length > 2 && ['fr', 'en'].includes(parts[2])) {
      return `/static/${parts[2]}`;
    }
    return '/static';
  }
  
  // Production or direct root access
  const match = path.match(/^\/(fr|en)(\/|$)/);
  return match ? match[0].replace(/\/$/, '') : '';
};

const AppRouter: React.FC = () => {
  const basename = React.useMemo(() => getBasename(), []);

  return (
    <Router basename={basename}>
      <Layout>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<App />} />
            {AuthRoutes()}
            {SocialRoutes()}
            {MediaRoutes()}
            {SearchRoutes()}
            {CompanionRoutes()}
            {GraphRoutes()}
            {GameRoutes()}
            {LabRoutes()}
            {UtilsRoutes()}
            {AdminRoutes()}
            {BillingRoutes()}
            {ExploreRoutes()}
            {SupportRoutes()}
            {ResearchRoutes()}
            {/* Catch-all is removed for debugging if it causes loops */}
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

export default AppRouter;
