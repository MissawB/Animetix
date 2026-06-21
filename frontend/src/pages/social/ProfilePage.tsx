import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, Shield, Zap, Award, ArrowRight, Brain, Sparkles } from 'lucide-react';
import { useProfile } from '../../features/social/hooks/useProfile';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from "../../components/ui/Skeleton";
import { GameHistoryPanel } from '../../features/social/components/GameHistoryPanel';
import type { components } from '../../types/api';

import { useAuthStore } from '../../store/authStore';
import { getTrackerConnections, linkTracker, unlinkTracker } from '../../api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link2, Link2Off, RefreshCw } from 'lucide-react';

import { AnimatedPage } from "../../components/ui/AnimatedPage";

type ApiAchievement = components["schemas"]["Achievement"];
type ApiCreativeFusion = components["schemas"]["CreativeFusion"];

const StatCard: React.FC<{ label: string; value: number; icon: React.ReactNode }> = ({ label, value, icon }) => (
  <div className="bg-gray-50 dark:bg-black/20 p-8 rounded-[2rem] text-center border border-black/5 dark:border-white/5 shadow-inner">
    <div className="w-12 h-12 bg-white dark:bg-[#0f0f1a] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-md border border-black/5 dark:border-white/5">
      {icon}
    </div>
    <div className="text-3xl font-black text-blue-600 dark:text-blue-400 mb-1">{value}</div>
    <div className="text-[10px] font-black uppercase opacity-40 tracking-widest text-black dark:text-white">{label}</div>
  </div>
);

const ProfilePage: React.FC = () => {
  const { t } = useTranslation();
  const { username } = useParams<{ username: string }>();
  const { data: profile, isLoading, isError } = useProfile(username);

  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const isOwnProfile = currentUser && currentUser.username === username;

  const { data: connections } = useQuery({
    queryKey: ['trackerConnections'],
    queryFn: getTrackerConnections,
    enabled: !!isOwnProfile,
  });

  const [linkingTracker, setLinkingTracker] = useState<'myanimelist' | 'anilist' | null>(null);
  const [trackerUsername, setTrackerUsername] = useState('');
  const [trackerToken, setTrackerToken] = useState('');
  const [linkError, setLinkError] = useState('');

  const linkMutation = useMutation({
    mutationFn: ({ tracker, username, token }: { tracker: string; username: string; token: string }) =>
      linkTracker(tracker, username, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackerConnections'] });
      setLinkingTracker(null);
      setTrackerUsername('');
      setTrackerToken('');
      setLinkError('');
    },
    onError: (err: unknown) => {
      setLinkError(err instanceof Error ? err.message : "Failed to link tracker");
    }
  });

  const unlinkMutation = useMutation({
    mutationFn: (tracker: string) => unlinkTracker(tracker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackerConnections'] });
    }
  });

  const handleLinkSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackerUsername || !trackerToken || !linkingTracker) return;
    linkMutation.mutate({
      tracker: linkingTracker,
      username: trackerUsername,
      token: trackerToken,
    });
  };

  if (isLoading) return (
    <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] flex items-center justify-center">
        <div className="max-w-4xl w-full mx-auto px-6 py-16">
            <CardSkeleton />
        </div>
    </div>
  );
  
  if (isError) return (
    <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] flex items-center justify-center">
        <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>
    </div>
  );
  
  if (!profile) return null;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-4xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Card padding="none" className="overflow-hidden border-none shadow-2xl bg-white dark:bg-[#0f0f1a]">
            {/* Profile Header */}
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 p-12 text-black relative overflow-hidden">
              <div className="absolute top-0 right-0 p-12 opacity-10">
                  <User className="w-64 h-64 -rotate-12" />
              </div>
              <div className="flex flex-col md:flex-row items-center gap-8 relative z-10">
                <div className="w-32 h-32 bg-black rounded-[2.5rem] flex items-center justify-center text-white text-5xl font-black italic shadow-2xl border-4 border-white/20">
                  {username?.[0].toUpperCase()}
                </div>
                <div className="text-center md:text-left">
                  <h1 
                    className="text-5xl font-black italic manga-font tracking-tighter mb-2 uppercase drop-shadow-sm animate-in fade-in duration-300"
                    style={{ color: profile.custom_username_color || undefined }}
                  >
                    {username}
                  </h1>
                  <div className="flex flex-wrap justify-center md:justify-start gap-4">
                    <Badge variant="neutral" className="bg-black text-white border-none py-2 px-4 shadow-lg">
                      <Shield className="w-3 h-3" /> {t('social.profile.rank', { rank: profile.rank || 'Explorateur' })}
                    </Badge>
                    <Badge variant="neutral" className="bg-white/30 backdrop-blur-md text-black border-none py-2 px-4 shadow-lg">
                      <Zap className="w-3 h-3" /> {t('social.profile.level', { level: profile.level })}
                    </Badge>
                    {profile.unlocked_badges?.includes('Sponsor Or') && (
                      <Badge variant="neutral" className="bg-gradient-to-r from-yellow-400 to-amber-500 text-black border-none py-2 px-4 shadow-lg font-black animate-pulse flex items-center gap-1.5">
                        <Sparkles className="w-3 h-3 text-black animate-spin" style={{ animationDuration: '3s' }} /> SPONSOR OR
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="p-12 text-black dark:text-white">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <StatCard label={t('social.profile.xp')} value={profile.xp} icon={<Zap className="text-orange-500" />} />
                <StatCard label={t('social.profile.achievements')} value={profile.achievements_count || 0} icon={<Award className="text-yellow-500" />} />
                <StatCard label={t('social.profile.collection')} value={profile.collection_count || 0} icon={<User className="text-blue-500" />} />
              </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-16">
                {/* Latest Achievements */}
                <Card padding="lg" className="bg-gray-50 dark:bg-black/20 border-none shadow-xl">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Award className="w-4 h-4 text-yellow-500" /> Succès Récents
                    </h3>
                    <div className="space-y-4">
                        {profile.recent_achievements?.map((ach: ApiAchievement, i: number) => (
                            <div key={i} className="flex items-center gap-4 p-4 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 group hover:border-yellow-400 transition-all shadow-sm">
                                <div className="w-10 h-10 bg-yellow-500/10 rounded-xl flex items-center justify-center text-yellow-500 group-hover:scale-110 transition-transform">
                                    <Award className="w-6 h-6" />
                                </div>
                                <div>
                                    <p className="text-sm font-black italic uppercase">{ach.name}</p>
                                    <p className="text-[10px] opacity-40 uppercase font-bold">{ach.description}</p>
                                </div>
                            </div>
                        ))}
                        {(!profile.recent_achievements || profile.recent_achievements.length === 0) && (
                            <p className="text-center py-8 opacity-20 italic">Aucun succès débloqué pour le moment.</p>
                        )}
                    </div>
                    <div className="mt-8 pt-8 border-t border-black/5 dark:border-white/5">
                        <Link to="/achievements/" className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline">
                            Voir tous les succès <ArrowRight className="inline w-3 h-3 ml-1" />
                        </Link>
                    </div>
                </Card>

                {/* Favorite Fusions */}
                <Card padding="lg" className="bg-gray-50 dark:bg-black/20 border-none shadow-xl">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Zap className="w-4 h-4 text-blue-500" /> Fusions Favorites
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        {profile.top_fusions?.map((fusion: ApiCreativeFusion, i: number) => (
                            <div key={i} className="aspect-video rounded-xl overflow-hidden relative group cursor-pointer border border-black/5 dark:border-white/5 hover:border-blue-500 transition-all shadow-sm">
                                <img src={fusion.image_url ?? undefined} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="" loading="lazy" decoding="async" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                                <p className="absolute bottom-3 left-3 text-[8px] font-black uppercase text-white truncate w-[80%]">{fusion.title_a} x {fusion.title_b}</p>
                            </div>
                        ))}
                    </div>
                    {(!profile.top_fusions || profile.top_fusions.length === 0) && (
                        <p className="text-center py-8 opacity-20 italic">La collection est vide.</p>
                    )}
                    <div className="mt-8 pt-8 border-t border-black/5 dark:border-white/5">
                        <Link to="/social/collection/" className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline">
                            Accéder à la collection <ArrowRight className="inline w-3 h-3 ml-1" />
                        </Link>
                    </div>
                </Card>
            </div>

            {/* Game History Panel */}
            <div className="mt-12">
                <GameHistoryPanel />
            </div>

            {isOwnProfile && (
              <Card padding="lg" className="mt-12 bg-gray-50 dark:bg-black/20 border-none shadow-xl text-black dark:text-white">
                <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                  <Link2 className="w-4 h-4 text-blue-500" /> Synchronisation des Trackers
                </h3>
                <p className="text-xs opacity-60 mb-6">
                  Associez vos comptes pour synchroniser automatiquement votre progression de lecture de mangas.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* MyAnimeList */}
                  <div className="p-6 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 flex flex-col justify-between min-h-[160px]">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-black italic uppercase text-sm">MyAnimeList</span>
                        {connections?.some(c => c.tracker === 'myanimelist') ? (
                          <span className="text-[10px] bg-green-500/10 text-green-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">Connecté</span>
                        ) : (
                          <span className="text-[10px] bg-gray-500/10 text-gray-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">Non connecté</span>
                        )}
                      </div>
                      {connections?.some(c => c.tracker === 'myanimelist') ? (
                        <p className="text-xs opacity-60">
                          Utilisateur : <span className="font-bold">{connections.find(c => c.tracker === 'myanimelist')?.username}</span>
                        </p>
                      ) : (
                        <p className="text-xs opacity-40 italic">Mettez à jour votre liste MAL en lisant vos mangas.</p>
                      )}
                    </div>
                    <div className="mt-4">
                      {connections?.some(c => c.tracker === 'myanimelist') ? (
                        <button
                          onClick={() => unlinkMutation.mutate('myanimelist')}
                          className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
                        >
                          <Link2Off className="w-3.5 h-3.5" /> Dissocier
                        </button>
                      ) : (
                        <button
                          onClick={() => setLinkingTracker('myanimelist')}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
                        >
                          <Link2 className="w-3.5 h-3.5" /> Associer MAL
                        </button>
                      )}
                    </div>
                  </div>

                  {/* AniList */}
                  <div className="p-6 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 flex flex-col justify-between min-h-[160px]">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-black italic uppercase text-sm">AniList</span>
                        {connections?.some(c => c.tracker === 'anilist') ? (
                          <span className="text-[10px] bg-green-500/10 text-green-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">Connecté</span>
                        ) : (
                          <span className="text-[10px] bg-gray-500/10 text-gray-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">Non connecté</span>
                        )}
                      </div>
                      {connections?.some(c => c.tracker === 'anilist') ? (
                        <p className="text-xs opacity-60">
                          Utilisateur : <span className="font-bold">{connections.find(c => c.tracker === 'anilist')?.username}</span>
                        </p>
                      ) : (
                        <p className="text-xs opacity-40 italic">Mettez à jour votre liste AniList automatiquement.</p>
                      )}
                    </div>
                    <div className="mt-4">
                      {connections?.some(c => c.tracker === 'anilist') ? (
                        <button
                          onClick={() => unlinkMutation.mutate('anilist')}
                          className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
                        >
                          <Link2Off className="w-3.5 h-3.5" /> Dissocier
                        </button>
                      ) : (
                        <button
                          onClick={() => setLinkingTracker('anilist')}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
                        >
                          <Link2 className="w-3.5 h-3.5" /> Associer AniList
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Linking Form Overlay/Modal */}
                {linkingTracker && (
                  <div className="mt-8 p-6 bg-white/50 dark:bg-black/30 rounded-2xl border border-blue-500/30">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-xs font-black uppercase tracking-wider text-blue-400">
                        Associer {linkingTracker === 'anilist' ? 'AniList' : 'MyAnimeList'}
                      </h4>
                      <button onClick={() => setLinkingTracker(null)} className="text-gray-400 hover:text-white text-xs border-none bg-transparent cursor-pointer font-bold">Annuler</button>
                    </div>

                    <form onSubmit={handleLinkSubmit} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex flex-col gap-1.5">
                          <label htmlFor="tracker-username" className="text-[9px] font-black uppercase tracking-widest opacity-60">Nom d'utilisateur</label>
                          <input
                            id="tracker-username"
                            type="text"
                            aria-label="Nom d'utilisateur"
                            value={trackerUsername}
                            onChange={(e) => setTrackerUsername(e.target.value)}
                            required
                            placeholder="Ex: OtakuMaster"
                            className="bg-[#05050a]/50 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-semibold"
                          />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <label htmlFor="tracker-token" className="text-[9px] font-black uppercase tracking-widest opacity-60">Jeton d'accès (Access Token)</label>
                          <input
                            id="tracker-token"
                            type="password"
                            aria-label="Jeton d'accès"
                            value={trackerToken}
                            onChange={(e) => setTrackerToken(e.target.value)}
                            required
                            placeholder="Entrez votre jeton API"
                            className="bg-[#05050a]/50 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-semibold"
                          />
                        </div>
                      </div>
                      {linkError && <p className="text-[10px] text-red-400 font-bold">{linkError}</p>}
                      <button
                        type="submit"
                        disabled={linkMutation.isPending}
                        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer border-none flex items-center justify-center gap-2"
                      >
                        {linkMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Enregistrer la connexion'}
                      </button>
                    </form>
                  </div>
                )}
              </Card>
            )}

              <div className="flex flex-col sm:flex-row justify-center gap-4 mt-16">
                  <Link to="/social/dashboard/" className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 border-2 border-gray-800 dark:border-white/20 hover:bg-gray-800 hover:text-white bg-transparent px-10 py-4 italic no-underline text-black dark:text-white">
                      {t('social.profile.back_dashboard')}
                  </Link>
                  <Link to="/social/archetype-nexus/" className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 bg-blue-600 text-white px-10 py-4 italic no-underline border-none shadow-blue-500/20">
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


