import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SocialDashboard = lazy(() => import('../SocialDashboard'));
const AchievementsPage = lazy(() => import('../AchievementsPage'));
const LeaderboardPage = lazy(() => import('../LeaderboardPage'));
const ProfilePage = lazy(() => import('../ProfilePage'));
const CollectionPage = lazy(() => import('../CollectionPage'));
const NotificationsPage = lazy(() => import('../NotificationsPage'));
const TransparencyPage = lazy(() => import('../TransparencyPage'));
const ClubDiscoveryPage = lazy(() => import('../ClubDiscoveryPage'));
const ClubDashboard = lazy(() => import('../ClubDashboard'));

export const SocialRoutes = (
  <>
    <Route path="/social/dashboard/" element={<SocialDashboard />} />
    <Route path="/leaderboard/" element={<LeaderboardPage />} />
    <Route path="/profile/:username/" element={<ProfilePage />} />
    <Route path="/achievements/" element={<AchievementsPage />} />
    <Route path="/social/collection/" element={<CollectionPage />} />
    <Route path="/notifications/" element={<NotificationsPage />} />
    <Route path="/transparency/" element={<TransparencyPage />} />
    <Route path="/clubs/" element={<ClubDiscoveryPage />} />
    <Route path="/clubs/:id/" element={<ClubDashboard />} />
  </>
);
