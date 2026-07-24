import React, { useState } from 'react';

import { Users, UserPlus, Search, UserMinus, ChevronRight } from 'lucide-react';
import { socialService } from '../../features/social/services/socialService';
import { Link } from 'react-router-dom';
import { User } from '../../types';
import { useToastStore } from '../../store/toastStore';
import { useTranslation } from 'react-i18next';
import { useSocialDashboard } from '../../features/social/hooks/useSocialDashboard';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { LAB_INPUT } from '../labs/components/shared/LabKit';

const SocialHubPage: React.FC = () => {
  const { addToast } = useToastStore();
  const { t } = useTranslation();
  const { data: dashboardData, isLoading: isDashboardLoading, toggleFollow } = useSocialDashboard();

  const [searchResults, setSearchUsers] = useState<(User & { is_following: boolean })[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'following' | 'followers' | 'discovery'>('following');

  const following = dashboardData?.following || [];
  const followers = dashboardData?.followers || [];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.length < 2) return;
    try {
      const results = await socialService.searchUsers(searchQuery);
      setSearchUsers(results);
      setActiveTab('discovery');
    } catch (_err) {
      addToast(t('social.hub.search_error', 'Erreur lors de la recherche.'), 'error');
    }
  };

  const handleToggleFollow = async (userId: number) => {
    try {
      toggleFollow(userId, {
        onSuccess: () => {
          addToast(t('social.hub.action_success', 'Action effectuée avec succès !'), 'success');
          if (activeTab === 'discovery') {
            // Optimistic or manual update of search results if needed
            setSearchUsers((prev) =>
              prev.map((u) => (u.id === userId ? { ...u, is_following: !u.is_following } : u)),
            );
          }
        },
        onError: () => {
          addToast(t('social.hub.action_error', 'Action impossible.'), 'error');
        },
      });
    } catch (_err) {
      addToast(t('social.hub.action_error', 'Action impossible.'), 'error');
    }
  };

  if (isDashboardLoading) {
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
        <div className="animate-pulse p-20 text-center font-black uppercase tracking-[0.3em] text-[#8F94A5]">
          {t('social.hub.loading', 'Initialisation du réseau social...')}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <AnimatedPage>
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          {/* ── Header ─────────────────────────────────────────────── */}
          <header className="relative mb-12">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
              aria-hidden
            />
            <div className="relative flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div>
                <div className="flex items-center gap-3">
                  <span className="explore-stamp -rotate-2" aria-hidden>
                    交
                  </span>
                  <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                    {t('social.hub.eyebrow', 'Registre · Liens')}
                  </span>
                </div>
                <h1 className="font-manga mt-4 flex items-center gap-3 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-5xl">
                  <Users className="h-9 w-9 text-[#E8442B]" aria-hidden="true" />{' '}
                  {t('social.hub.title', 'HUB SOCIAL')}
                </h1>
                <p className="mt-4 max-w-xl text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'social.hub.subtitle',
                    'Gérez vos connexions, découvrez de nouveaux héros et restez informé.',
                  )}
                </p>
              </div>

              {/* Search Bar */}
              <form onSubmit={handleSearch} className="relative w-full md:w-96">
                <input
                  type="text"
                  aria-label="Rechercher un utilisateur"
                  placeholder={t('social.hub.search_placeholder', 'Rechercher un utilisateur...')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`${LAB_INPUT} pr-12`}
                />
                <button
                  type="submit"
                  aria-label={t('social.hub.search_placeholder', 'Rechercher un utilisateur...')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 cursor-pointer border-none bg-transparent text-[#8F94A5] transition-colors hover:text-[#FDB913]"
                >
                  <Search className="h-5 w-5" />
                </button>
              </form>
            </div>
            <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
          </header>

          {/* Tabs */}
          <div className="no-scrollbar mb-8 flex gap-3 overflow-x-auto pb-2">
            {(['following', 'followers', 'discovery'] as const).map((tabId) => {
              const tabLabel =
                tabId === 'following'
                  ? t('social.hub.tab_following', 'Abonnements')
                  : tabId === 'followers'
                    ? t('social.hub.tab_followers', 'Abonnés')
                    : t('social.hub.tab_discovery', 'Découverte');
              const tabCount =
                tabId === 'following'
                  ? following.length
                  : tabId === 'followers'
                    ? followers.length
                    : searchResults.length;

              return (
                <button
                  key={tabId}
                  onClick={() => setActiveTab(tabId)}
                  className={`whitespace-nowrap rounded-full border px-6 py-2.5 text-xs font-black uppercase tracking-widest transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] ${
                    activeTab === tabId
                      ? 'border-[#E8442B] bg-[#E8442B] text-[#F4F1E8]'
                      : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                  }`}
                >
                  {tabLabel} (<span className="text-[#FDB913]">{tabCount}</span>)
                </button>
              );
            })}
          </div>

          {/* Grid Content */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {activeTab === 'following' &&
              following.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors hover:border-[#FDB913]/50"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 flex-none items-center justify-center rounded-2xl bg-[#FDB913] text-xl font-black italic text-[#0B0C10]">
                      {item.username[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <Link
                        to={`/profile/${item.username}/`}
                        className="block truncate font-black uppercase tracking-tight text-[#F4F1E8] no-underline transition-colors hover:text-[#FDB913]"
                      >
                        {item.username}
                      </Link>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="rounded border border-[#F4F1E8]/10 px-2 py-0.5 text-[10px] font-black uppercase text-[#8F94A5]">
                          {t('social.hub.level_short', 'Niv. {{level}}', { level: item.level })}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleToggleFollow(item.to_user)}
                      className="inline-flex flex-none cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-3 py-2 text-[#8F94A5] transition-colors hover:border-[#E8442B] hover:text-[#E8442B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                    >
                      <UserMinus className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}

            {activeTab === 'followers' &&
              followers.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors hover:border-[#FDB913]/40"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 flex-none items-center justify-center rounded-2xl bg-[#F4F1E8] text-xl font-black italic text-[#0B0C10]">
                      {item.username[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <Link
                        to={`/profile/${item.username}/`}
                        className="block truncate font-black uppercase tracking-tight text-[#F4F1E8] no-underline transition-colors hover:text-[#FDB913]"
                      >
                        {item.username}
                      </Link>
                      <p className="mt-0.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('social.hub.follows_you', 'Vous suit')}
                      </p>
                    </div>
                    <Link
                      to={`/profile/${item.username}/`}
                      className="flex-none text-[#8F94A5] transition-colors hover:text-[#FDB913]"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Link>
                  </div>
                </div>
              ))}

            {activeTab === 'discovery' &&
              searchResults.map((user) => (
                <div
                  key={user.id}
                  className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors hover:border-[#FDB913]/40"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 flex-none items-center justify-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] text-xl font-black italic text-[#F4F1E8]">
                      {user.username[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <Link
                        to={`/profile/${user.username}/`}
                        className="block truncate font-black uppercase tracking-tight text-[#F4F1E8] no-underline transition-colors hover:text-[#FDB913]"
                      >
                        {user.username}
                      </Link>
                      <p className="mt-0.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('social.hub.level_label', 'Niveau {{level}}', {
                          level: user.level || 1,
                        })}
                      </p>
                    </div>
                    <button
                      onClick={() => handleToggleFollow(user.id)}
                      className={`inline-flex flex-none cursor-pointer items-center gap-2 rounded-full px-3 py-2 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] ${
                        user.is_following
                          ? 'border border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#E8442B] hover:text-[#E8442B]'
                          : 'border-none bg-[#E8442B] text-[#F4F1E8] hover:bg-[#c93a24]'
                      }`}
                    >
                      {user.is_following ? (
                        <UserMinus className="h-4 w-4" />
                      ) : (
                        <UserPlus className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              ))}

            {/* Empty States */}
            {((activeTab === 'following' && following.length === 0) ||
              (activeTab === 'followers' && followers.length === 0) ||
              (activeTab === 'discovery' && searchResults.length === 0)) && (
              <div className="col-span-full flex flex-col items-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-20 text-center">
                <Users className="mb-4 h-14 w-14 text-[#8F94A5]/30" />
                <p className="text-sm font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('social.hub.empty_state', 'Rien à afficher ici pour le moment.')}
                </p>
              </div>
            )}
          </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default SocialHubPage;
