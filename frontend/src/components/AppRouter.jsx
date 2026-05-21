import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './Layout';

const App = lazy(() => import('../App'));
const SocialDashboard = lazy(() => import('./SocialDashboard'));
const AchievementsPage = lazy(() => import('./AchievementsPage'));
const CovertestPage = lazy(() => import('./CovertestPage'));
const AkinetixPage = lazy(() => import('./AkinetixPage'));
const EmojiPage = lazy(() => import('./EmojiPage'));
const BlindtestPage = lazy(() => import('./BlindtestPage'));
const VisionPage = lazy(() => import('./VisionPage'));
const MangaLabPage = lazy(() => import('./MangaLabPage'));
const AdminEvalPage = lazy(() => import('./AdminEvalPage'));
const HealthPage = lazy(() => import('./HealthPage'));

const Loading = () => <div className="p-20 text-center">Chargement...</div>;

const AppRouter = () => {
  return (
    <Router>
      <Layout>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="/social/dashboard/" element={<SocialDashboard />} />
            <Route path="/achievements/" element={<AchievementsPage />} />
            <Route path="/covertest/" element={<CovertestPage />} />
            <Route path="/akinetix/" element={<AkinetixPage />} />
            <Route path="/emoji/" element={<EmojiPage />} />
            <Route path="/blindtest/" element={<BlindtestPage />} />
            <Route path="/vision/" element={<VisionPage />} />
            <Route path="/manga_lab/" element={<MangaLabPage />} />
            <Route path="/admin/ai_eval/" element={<AdminEvalPage />} />
            <Route path="/admin/health/" element={<HealthPage />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

export default AppRouter;
