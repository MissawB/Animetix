import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, Shield, Zap, Award } from 'lucide-react';
import { useProfile } from './hooks/useProfile';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';

const ProfilePage: React.FC = () => {
  const { t } = useTranslation();
  const { username } = useParams<{ username: string }>();
  const { data: profile, isLoading, isError } = useProfile(username);

  if (isLoading) return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <CardSkeleton />
    </div>
  );
  
  if (isError) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;
  if (!profile) return null;

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <Card padding="none" className="overflow-hidden">
        {/* Profile Header */}
        <div className="bg-gradient-to-r from-yellow-400 to-orange-500 p-12 text-black">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="w-32 h-32 bg-black rounded-[2.5rem] flex items-center justify-center text-white text-5xl font-black italic shadow-2xl">
              {username?.[0].toUpperCase()}
            </div>
            <div className="text-center md:text-left">
              <h1 className="text-5xl font-black italic manga-font tracking-tighter mb-2 uppercase">{username}</h1>
              <div className="flex flex-wrap justify-center md:justify-start gap-4">
                <Badge variant="neutral" className="bg-black text-white border-none py-2 px-4">
                  <Shield className="w-3 h-3" /> {t('social.profile.rank', { rank: profile.rank || 'Explorateur' })}
                </Badge>
                <Badge variant="neutral" className="bg-white/20 backdrop-blur-md border-none py-2 px-4">
                  <Zap className="w-3 h-3" /> {t('social.profile.level', { level: profile.level })}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="p-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <StatCard label={t('social.profile.xp')} value={profile.xp} icon={<Zap className="text-orange-500" />} />
            <StatCard label={t('social.profile.achievements')} value={profile.achievements_count || 0} icon={<Award className="text-yellow-500" />} />
            <StatCard label={t('social.profile.collection')} value={profile.collection_count || 0} icon={<User className="text-blue-500" />} />
          </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-16">
            {/* Latest Achievements */}
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                    <Award className="w-4 h-4 text-yellow-500" /> Succès Récents
                </h3>
                <div className="space-y-4">
                    {profile.recent_achievements?.map((ach: any, i: number) => (
                        <div key={i} className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 group hover:border-yellow-500/30 transition-all">
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
                <div className="mt-8 pt-8 border-t border-white/5">
                    <Link to="/achievements/" className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline">
                        Voir tous les succès <ArrowRight className="inline w-3 h-3 ml-1" />
                    </Link>
                </div>
            </Card>

            {/* Favorite Fusions */}
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                    <Zap className="w-4 h-4 text-blue-500" /> Fusions Favorites
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    {profile.top_fusions?.map((fusion: any, i: number) => (
                        <div key={i} className="aspect-video rounded-xl overflow-hidden relative group cursor-pointer border border-white/5 hover:border-blue-500/30 transition-all">
                            <img src={fusion.image_url} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                            <p className="absolute bottom-3 left-3 text-[8px] font-black uppercase text-white truncate w-[80%]">{fusion.title_a} x {fusion.title_b}</p>
                        </div>
                    ))}
                </div>
                {(!profile.top_fusions || profile.top_fusions.length === 0) && (
                    <p className="text-center py-8 opacity-20 italic">La collection est vide.</p>
                )}
                <div className="mt-8 pt-8 border-t border-white/5">
                    <Link to="/social/collection/" className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline">
                        Accéder à la collection <ArrowRight className="inline w-3 h-3 ml-1" />
                    </Link>
                </div>
            </Card>
        </div>

          <div className="flex flex-col sm:flex-row justify-center gap-4 mt-16">
              <Link to="/social/dashboard/" className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 border-2 border-gray-800 dark:border-white/20 hover:bg-gray-800 hover:text-white bg-transparent px-10 py-4 italic no-underline">
                  {t('social.profile.back_dashboard')}
              </Link>
              <Link to="/social/archetype-nexus/" className="font-black rounded-2xl transition-all shadow-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 bg-blue-600 text-white px-10 py-4 italic no-underline border-none shadow-blue-500/20">
                  <Brain className="w-5 h-5" /> ARCHETYPE NEXUS
              </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon }) => (
  <div className="bg-gray-50 dark:bg-navy-900 p-8 rounded-[2rem] text-center border border-gray-100 dark:border-white/5">
    <div className="w-12 h-12 bg-white dark:bg-navy-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-md border border-gray-100 dark:border-white/5">
      {icon}
    </div>
    <div className="text-3xl font-black text-blue-600 dark:text-blue-400 mb-1">{value}</div>
    <div className="text-[10px] font-black uppercase opacity-40 tracking-widest">{label}</div>
  </div>
);

export default ProfilePage;
