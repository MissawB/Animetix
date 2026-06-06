import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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

const App = React.lazy(() => import('../App'));

const Loading: React.FC = () => <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em]">Initialisation du système...</div>;

const getBasename = () => {
  const path = window.location.pathname;

  // Handle /static/ or /static prefix
  if (path === '/static' || path.startsWith('/static/')) {
    const subPath = path.startsWith('/static/') ? path.substring(8) : '';
    const languageMatch = subPath.match(/^(fr|en)(\/|$)/);
    return languageMatch ? `/static/${languageMatch[1]}` : '/static';
  }

  // Handle root language prefix
  const languageMatch = path.match(/^\/(fr|en)(\/|$)/);
  return languageMatch ? languageMatch[0].replace(/\/$/, '') : '';
};

const AppRouter: React.FC = () => {
  return (
    <Router basename={getBasename()}>
      <Layout>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<App />} />
            {AuthRoutes}
            {SocialRoutes}
            {MediaRoutes}
            {SearchRoutes}
            {CompanionRoutes}
            {GameRoutes}
            {LabRoutes}
            {UtilsRoutes}
            {AdminRoutes}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

export default AppRouter;
