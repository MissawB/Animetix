import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { pageVariants } from './ui/animations';
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

const NotFoundPage = lazy(() => import('../pages/utils/NotFoundPage'));

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

/**
 * Route transitions must wrap <Routes location={location}> directly :
 * l'arbre sortant conserve l'ancienne location en prop, sinon il re-rend la
 * nouvelle page pendant l'animation d'exit et AnimatePresence reste bloqué
 * (page invisible jusqu'au rechargement).
 */
const AnimatedRoutes: React.FC = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" onExitComplete={() => window.scrollTo(0, 0)}>
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <Suspense fallback={<Loading />}>
          <Routes location={location}>
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
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </motion.div>
    </AnimatePresence>
  );
};

const AppRouter: React.FC = () => {
  const basename = React.useMemo(() => getBasename(), []);

  return (
    <Router basename={basename}>
      <Layout>
        <AnimatedRoutes />
      </Layout>
    </Router>
  );
};

export default AppRouter;
