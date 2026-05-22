import React from 'react';
import { Link } from 'react-router-dom';
import { Users, UserMinus, Heart } from 'lucide-react';
import { useSocialDashboard } from './hooks/useSocialDashboard';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';

const SocialDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError, toggleFollow } = useSocialDashboard();

  if (isLoading) return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <CardSkeleton />
      <CardSkeleton />
    </div>
  );
  
  if (isError || !data) return <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>;

  return (
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
  );
};

export default SocialDashboard;
