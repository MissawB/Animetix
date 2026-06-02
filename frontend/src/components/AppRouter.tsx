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

const App = React.lazy(() => import('../App'));

const Loading: React.FC = () => <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em]">Initialisation du système...</div>;


const getBasename = () => {
  const match = window.location.pathname.match(/^\/(fr|en)(\/|$)/);
  return match ? match[0].replace(/\/$/, '') : '';
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
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

export default AppRouter;
