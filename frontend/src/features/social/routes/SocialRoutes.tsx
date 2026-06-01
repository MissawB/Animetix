import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SocialDashboard = lazy(() => import('../SocialDashboard'));
const AchievementsPage = lazy(() => import('../AchievementsPage'));
const LeaderboardPage = lazy(() => import('../LeaderboardPage'));
const ProfilePage = lazy(() => import('../ProfilePage'));
const CollectionPage = lazy(() => import('../CollectionPage'));
const NotificationsPage = lazy(() => import('../NotificationsPage'));
const TransparencyPage = lazy(() => import('../TransparencyPage'));
const CommunityFeedPage = lazy(() => import('../CommunityFeedPage'));
const ClubDiscoveryPage = lazy(() => import('../ClubDiscoveryPage'));
const ClubDashboard = lazy(() => import('../ClubDashboard'));
const ArchetypeNexusPage = lazy(() => import('../ArchetypeNexusPage'));
const AIDebateArenaPage = lazy(() => import('../AIDebateArenaPage'));
const ExplorePage = lazy(() => import('../../explore/ExplorePage'));

export const SocialRoutes = (
  <>
    <Route path="/social/dashboard/" element={<SocialDashboard />} />
    <Route path="/social/feed/" element={<CommunityFeedPage />} />
    <Route path="/leaderboard/" element={<LeaderboardPage />} />
    <Route path="/profile/:username/" element={<ProfilePage />} />
    <Route path="/achievements/" element={<AchievementsPage />} />
    <Route path="/social/collection/" element={<CollectionPage />} />
    <Route path="/notifications/" element={<NotificationsPage />} />
    <Route path="/transparency/" element={<TransparencyPage />} />
    <Route path="/social/archetype-nexus/" element={<ArchetypeNexusPage />} />
    <Route path="/social/debate-arena/" element={<AIDebateArenaPage />} />
    <Route path="/explore/" element={<ExplorePage />} />
    <Route path="/clubs/" element={<ClubDiscoveryPage />} />
    <Route path="/clubs/:id/" element={<ClubDashboard />} />
  </>
);
