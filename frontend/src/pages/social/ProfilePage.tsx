import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useProfile } from '../../features/social/hooks/useProfile';
import { socialService } from '../../features/social/services/socialService';
import { useAuthStore } from '../../store/authStore';
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
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] flex items-center justify-center">
        <div className="max-w-4xl w-full mx-auto px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError)
    return (
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] flex items-center justify-center">
        <div className="text-center py-20 text-[#E8442B] font-bold">{t('common.error')}</div>
      </div>
    );

  if (!profile) return null;

  return (
    <AnimatedPage>
      <div className="relative min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8] transition-colors duration-500 bg-manga-overlay">
        <span className="explore-stamp absolute right-6 top-6 -rotate-2 z-10" aria-hidden>
          印
        </span>
        <div className="max-w-4xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <section className="overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] shadow-2xl">
            {/* Profile Header */}
            <ProfileHeaderCard
              username={username}
              avatar={profile.avatar}
              rank={profile.rank}
              level={profile.level}
              customUsernameColor={profile.custom_username_color}
              unlockedBadges={profile.unlocked_badges}
            />

            {/* Main Profile Body */}
            <div className="p-12 text-[#F4F1E8]">
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
                  className="flex items-center justify-center gap-2 rounded-2xl border border-[#F4F1E8]/15 bg-transparent px-10 py-4 font-manga font-black italic uppercase text-[#8F94A5] no-underline transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
                >
                  {t('social.profile.back_dashboard')}
                </Link>
                <Link
                  to="/social/archetype-nexus/"
                  className="flex items-center justify-center gap-2 rounded-2xl border-none bg-[#E8442B] px-10 py-4 font-manga font-black italic uppercase text-[#F4F1E8] no-underline transition-colors hover:bg-[#c93a24]"
                >
                  <Brain className="w-5 h-5" /> ARCHETYPE NEXUS
                </Link>
              </div>
            </div>
          </section>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ProfilePage;
