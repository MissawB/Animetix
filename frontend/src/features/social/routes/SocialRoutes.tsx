import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SocialDashboard = lazy(() => import('../../../pages/social/SocialDashboard'));
const AchievementsPage = lazy(() => import('../../../pages/social/AchievementsPage'));
const LeaderboardPage = lazy(() => import('../../../pages/social/LeaderboardPage'));
const ProfilePage = lazy(() => import('../../../pages/social/ProfilePage'));
const CollectionPage = lazy(() => import('../../../pages/social/CollectionPage'));
const NotificationsPage = lazy(() => import('../../../pages/social/NotificationsPage'));
const TransparencyPage = lazy(() => import('../../../pages/social/TransparencyPage'));
const CommunityFeedPage = lazy(() => import('../../../pages/social/CommunityFeedPage'));
const ClubDiscoveryPage = lazy(() => import('../../../pages/social/ClubDiscoveryPage'));
const ClubDashboard = lazy(() => import('../../../pages/social/ClubDashboard'));
const ClubEventPage = lazy(() => import('../../../pages/social/ClubEventPage'));
const AIFeedbackHistoryPage = lazy(() => import('../../../pages/social/AIFeedbackHistoryPage'));
const SocialHubPage = lazy(() => import('../../../pages/social/SocialHubPage'));
const ArchetypeNexusPage = lazy(() => import('../../../pages/social/ArchetypeNexusPage'));
const AIDebateArenaPage = lazy(() => import('../../../pages/social/AIDebateArenaPage'));
const NeuroMemoryPage = lazy(() => import('../../../pages/social/NeuroMemoryPage'));
const FriendsPage = lazy(() => import('../../../pages/social/FriendsPage'));

export const SocialRoutes = () => (
  <>
    <Route path="/social/dashboard/" element={<SocialDashboard />} />
    <Route path="/social/friends/" element={<FriendsPage />} />
    <Route path="/social/hub/" element={<SocialHubPage />} />
    <Route path="/social/feed/" element={<CommunityFeedPage />} />
    <Route path="/leaderboard/" element={<LeaderboardPage />} />
    <Route path="/profile/:username/" element={<ProfilePage />} />
    <Route path="/achievements/" element={<AchievementsPage />} />
    <Route path="/social/collection/" element={<CollectionPage />} />
    <Route path="/notifications/" element={<NotificationsPage />} />
    <Route path="/social/transparency/" element={<TransparencyPage />} />
    <Route path="/social/nexus/" element={<ArchetypeNexusPage />} />
    <Route path="/social/archetype-nexus/" element={<ArchetypeNexusPage />} />
    <Route path="/social/neuro-memory/" element={<NeuroMemoryPage />} />
    <Route path="/social/debate-arena/" element={<AIDebateArenaPage />} />
    <Route path="/social/ai-feedback-history/" element={<AIFeedbackHistoryPage />} />
    <Route path="/clubs/" element={<ClubDiscoveryPage />} />
    <Route path="/clubs/:id/" element={<ClubDashboard />} />
    <Route path="/clubs/:id/events/:eventId/" element={<ClubEventPage />} />
  </>
);

