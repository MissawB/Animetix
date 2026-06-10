import React from 'react';
import { Link } from 'react-router-dom';
import { Users, UserMinus, Heart, Brain, Swords, Layers, Activity, Zap, Fingerprint } from 'lucide-react';
import { useSocialDashboard } from '../../features/social/hooks/useSocialDashboard';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from "../../components/ui/Skeleton";

const DashboardLinkCard: React.FC<{ title: string; desc: string; icon: React.ReactNode; to: string; accent: string }> = ({ title, desc, icon, to, accent }) => (
    <Link to={to} className="no-underline group">
        <Card padding="lg" className={`h-full border-white/5 hover:border-${accent}-500/30 transition-all hover:-translate-y-1 bg-navy-900/40`}>
            <div className={`w-12 h-12 rounded-2xl bg-${accent}-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                {icon}
            </div>
            <h4 className="font-black italic uppercase manga-font text-lg mb-2">{title}</h4>
            <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">{desc}</p>
        </Card>
    </Link>
);

const SocialDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError, toggleFollow } = useSocialDashboard();

  if (isLoading) return (
    <div className="space-y-12">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );

  if (isError || !data) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;

  return (
    <div className="space-y-12">
      {/* NEXUS TOOLS */}
      <section>
        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.3em] flex items-center gap-2 px-4">
            <Zap className="w-4 h-4 text-blue-500" /> Nexus Cognitive Suite
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <DashboardLinkCard 
                title="Archetype Nexus" 
                desc="Votre profil neuronal." 
                icon={<Brain className="text-blue-500" />} 
                to="/social/archetype-nexus/"
                accent="blue"
            />
            <DashboardLinkCard 
                title="AI Debate Arena" 
                desc="Duels sémantiques." 
                icon={<Swords className="text-red-500" />} 
                to="/social/debate-arena/"
                accent="red"
            />
            <DashboardLinkCard 
                title="Ma Collection" 
                desc="Fusions & Favoris." 
                icon={<Layers className="text-yellow-500" />} 
                to="/social/collection/"
                accent="yellow"
            />
            <DashboardLinkCard 
                title="Clubs" 
                desc="Communautés actives." 
                icon={<Users className="text-emerald-500" />} 
                to="/clubs/"
                accent="emerald"
            />
            <DashboardLinkCard 
                title="Neuro-Memory" 
                desc="Gérez votre empreinte." 
                icon={<Fingerprint className="text-purple-500" />} 
                to="/social/neuro-memory/"
                accent="purple"
            />
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

      {/* ABONNEMENTS */}
      <Card padding="lg">
        <h3 className="manga-font text-xl mb-6 flex items-center gap-3">
          <Users className="w-6 h-6 text-yellow-400" /> {t('social.dashboard.following_title')}
        </h3>
        <div className="space-y-4">
          {data.following.map((f: any) => (
            <div key={f.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl hover:scale-[1.02] transition-transform border border-gray-100 dark:border-white/5">
              <Link to={`/profile/${f.username}/`} className="flex items-center gap-4 no-underline text-current">
                <div className="w-12 h-12 bg-yellow-400 rounded-xl flex items-center justify-center font-black italic border-2 border-black text-black">
                  {f.username[0].toUpperCase()}
                </div>
                <div>
                  <div className="font-bold">{f.username}</div>
                  <div className="text-[10px] uppercase font-black opacity-40">{t('social.profile.level', { level: f.level })}</div>
                </div>
              </Link>
              <Button 
                variant="danger" 
                size="sm" 
                className="rounded-full px-4" 
                onClick={() => toggleFollow(f.to_user)}
              >
                <UserMinus className="w-4 h-4" /> {t('social.dashboard.unfollow')}
              </Button>
            </div>
          ))}
          {data.following.length === 0 && <p className="text-center py-8 opacity-30 italic">{t('social.dashboard.no_following')}</p>}
        </div>
      </Card>

      {/* ABONNÉS */}
      <Card padding="lg">
        <h3 className="manga-font text-xl mb-6 flex items-center gap-3">
          <Heart className="w-6 h-6 text-red-500" /> {t('social.dashboard.followers_title')}
        </h3>
        <div className="space-y-4">
          {data.followers.map((f: any) => (
            <div key={f.id} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl border border-gray-100 dark:border-white/5">
              <div className="w-12 h-12 bg-navy-700 rounded-xl flex items-center justify-center font-black italic border-2 border-white/10">
                {f.username[0].toUpperCase()}
              </div>
              <div>
                <div className="font-bold">{f.username}</div>
                <div className="text-[10px] uppercase font-black opacity-40">{t('social.profile.level', { level: f.level })}</div>
              </div>
            </div>
          ))}
          {data.followers.length === 0 && <p className="text-center py-8 opacity-30 italic">{t('social.dashboard.no_followers')}</p>}
        </div>
      </Card>
    </div>
  </div>
  );
};

export default SocialDashboard;


