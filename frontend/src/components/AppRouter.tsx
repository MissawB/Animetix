import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './Layout';
import { GameRoutes } from '../features/games/routes/GameRoutes';
import { SocialRoutes } from '../features/social/routes/SocialRoutes';
import { LabRoutes } from '../features/labs/routes/LabRoutes';
import { AdminRoutes } from '../features/admin/routes/AdminRoutes';
import { UtilsRoutes } from '../features/utils/routes/UtilsRoutes';

const App = React.lazy(() => import('../App'));

const Loading: React.FC = () => <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em]">Initialisation du système...</div>;


const AppRouter: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<App />} />
            {SocialRoutes}
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
