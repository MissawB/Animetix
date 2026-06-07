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
const ClubEventPage = lazy(() => import('../ClubEventPage'));
const AIFeedbackHistoryPage = lazy(() => import('../AIFeedbackHistoryPage'));
const SocialHubPage = lazy(() => import('../SocialHubPage'));
const ArchetypeNexusPage = lazy(() => import('../ArchetypeNexusPage'));
const AIDebateArenaPage = lazy(() => import('../AIDebateArenaPage'));
const ExplorePage = lazy(() => import('../../explore/ExplorePage'));
const NeuroMemoryPage = lazy(() => import('../NeuroMemoryPage'));
const PricingPage = lazy(() => import('../../billing/PricingPage'));
const TreeOfThoughtsPage = lazy(() => import('../../labs/TreeOfThoughtsPage'));
const MultiverseGalleryPage = lazy(() => import('../../labs/MultiverseGalleryPage'));

export const SocialRoutes = (
  <>
    <Route path="/social/dashboard/" element={<SocialDashboard />} />
    <Route path="/social/hub/" element={<SocialHubPage />} />
    <Route path="/social/feed/" element={<CommunityFeedPage />} />
    <Route path="/leaderboard/" element={<LeaderboardPage />} />
    <Route path="/profile/:username/" element={<ProfilePage />} />
    <Route path="/achievements/" element={<AchievementsPage />} />
    <Route path="/social/collection/" element={<CollectionPage />} />
    <Route path="/notifications/" element={<NotificationsPage />} />
    <Route path="/transparency/" element={<TransparencyPage />} />
    <Route path="/social/archetype-nexus/" element={<ArchetypeNexusPage />} />
    <Route path="/social/neuro-memory/" element={<NeuroMemoryPage />} />
    <Route path="/social/debate-arena/" element={<AIDebateArenaPage />} />
    <Route path="/social/ai-feedback-history/" element={<AIFeedbackHistoryPage />} />
    <Route path="/explore/" element={<ExplorePage />} />
    <Route path="/pricing/" element={<PricingPage />} />
    <Route path="/lab/tot/" element={<TreeOfThoughtsPage />} />
    <Route path="/multiverse/gallery/" element={<MultiverseGalleryPage />} />
    <Route path="/clubs/" element={<ClubDiscoveryPage />} />
    <Route path="/clubs/:id/" element={<ClubDashboard />} />
    <Route path="/clubs/:id/events/:eventId/" element={<ClubEventPage />} />
  </>
);
