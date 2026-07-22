import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useProfile } from '../../features/social/hooks/useProfile';
import { socialService } from '../../features/social/services/socialService';
import { useAuthStore } from '../../store/authStore';
import { Card } from '../../components/ui/Card';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { GameHistoryPanel } from '../../features/social/components/GameHistoryPanel';

import { ProfileHeaderCard } from './components/ProfileHeaderCard';
import { ProfileStatsSection } from './components/ProfileStatsSection';
import { ProfileAchievementsCard } from './components/ProfileAchievementsCard';
import { ProfileFusionsCard } from './components/ProfileFusionsCard';
import { TrackerSyncPanel } from './components/TrackerSyncPanel';

const ProfilePage: React.FC = () => {
  const { t } = useTranslation();
  const { username } = useParams<{ username: string }>();
  const { data: profile, isLoading, isError } = useProfile(username);

  const { user: currentUser } = useAuthStore();
  const isOwnProfile = Boolean(currentUser && currentUser.username === username);

  const { data: connections } = useQuery({
    queryKey: ['trackerConnections'],
    queryFn: socialService.getTrackerConnections,
    enabled: isOwnProfile,
  });

  if (isLoading)
    return (
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] flex items-center justify-center">
        <div className="max-w-4xl w-full mx-auto px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError)
    return (
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] flex items-center justify-center">
        <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>
      </div>
    );

  if (!profile) return null;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-4xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card
            padding="none"
            className="overflow-hidden border-none shadow-2xl bg-white dark:bg-[#0f0f1a]"
          >
            {/* Profile Header */}
            <ProfileHeaderCard
              username={username}
              rank={profile.rank}
              level={profile.level}
              customUsernameColor={profile.custom_username_color}
              unlockedBadges={profile.unlocked_badges}
            />

            {/* Main Profile Body */}
            <div className="p-12 text-black dark:text-white">
              {/* Stats Grid */}
              <ProfileStatsSection
                xp={profile.xp}
                achievementsCount={profile.achievements_count}
                collectionCount={profile.collection_count}
              />

              {/* Achievements and Fusions */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-16">
                <ProfileAchievementsCard recentAchievements={profile.recent_achievements} />
                <ProfileFusionsCard topFusions={profile.top_fusions} />
              </div>

              {/* Game History Panel */}
              <div className="mt-12">
                <GameHistoryPanel />
              </div>

              {/* Tracker Synchronization (Own Profile only) */}
              {isOwnProfile && <TrackerSyncPanel connections={connections} />}

              {/* Footer Navigation Buttons */}
              <div className="flex flex-col sm:flex-row justify-center gap-4 mt-16">
                <Link
                  to="/social/dashboard/"
                  className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 border-2 border-gray-800 dark:border-white/20 hover:bg-gray-800 hover:text-white bg-transparent px-10 py-4 italic no-underline text-black dark:text-white"
                >
                  {t('social.profile.back_dashboard')}
                </Link>
                <Link
                  to="/social/archetype-nexus/"
                  className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 bg-blue-600 text-white px-10 py-4 italic no-underline border-none shadow-blue-500/20"
                >
                  <Brain className="w-5 h-5" /> ARCHETYPE NEXUS
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ProfilePage;
