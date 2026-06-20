import React from 'react';
import { Link } from 'react-router-dom';
import { Users, UserMinus, UserPlus, Search, Heart, ArrowLeft } from 'lucide-react';
import { useSocialDashboard } from '../../features/social/hooks/useSocialDashboard';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { useTranslation } from 'react-i18next';
import { Friendship } from '../../types';

const FriendCard: React.FC<{
  friend: Friendship;
  type: 'following' | 'follower';
  onUnfollow?: (userId: number) => void;
}> = ({ friend, type, onUnfollow }) => (
  <div className="flex items-center justify-between p-5 bg-gray-50 dark:bg-navy-900/60 rounded-2xl hover:scale-[1.01] transition-all border border-gray-100 dark:border-white/5 group">
    <Link to={`/profile/${friend.username}/`} className="flex items-center gap-4 no-underline text-current flex-1 min-w-0">
      <div className="w-14 h-14 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-2xl flex items-center justify-center font-black italic text-xl border-2 border-black text-black shadow-lg group-hover:scale-110 transition-transform shrink-0">
        {friend.username[0].toUpperCase()}
      </div>
      <div className="min-w-0">
        <div className="font-black text-lg truncate">{friend.username}</div>
        <div className="text-[10px] uppercase font-black opacity-40 tracking-widest">
          Niveau {friend.level} • Depuis {new Date(friend.created_at).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })}
        </div>
      </div>
    </Link>
    {type === 'following' && onUnfollow && (
      <Button
        variant="danger"
        size="sm"
        className="rounded-full px-4 ml-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => onUnfollow(friend.to_user)}
      >
        <UserMinus className="w-4 h-4" /> Unfollow
      </Button>
    )}
  </div>
);

const FriendsPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError, toggleFollow } = useSocialDashboard();

  if (isLoading) return (
    <div className="max-w-5xl mx-auto px-6 py-16 space-y-12">
      <div className="space-y-4">
        <CardSkeleton /><CardSkeleton /><CardSkeleton />
      </div>
    </div>
  );

  if (isError || !data) return (
    <div className="text-center py-20 text-red-500 font-bold">{t('common.error')}</div>
  );

  return (
    <AnimatedPage>
      <div className="max-w-5xl mx-auto px-6 py-16">
        {/* Header */}
        <header className="mb-16">
          <Link to="/social/dashboard/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest opacity-40 hover:opacity-100 transition-opacity mb-8 no-underline text-current">
            <ArrowLeft className="w-4 h-4" /> Retour au Dashboard
          </Link>
          <h1 className="text-5xl md:text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
            MON <span className="text-yellow-400 text-glow">RÉSEAU</span>
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em]">
            Gérez vos abonnements et vos abonnés.
          </p>
        </header>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-6 mb-16">
          <Card padding="lg" className="text-center bg-gradient-to-br from-yellow-400/5 to-orange-500/5 border-yellow-500/10">
            <Users className="w-10 h-10 text-yellow-400 mx-auto mb-4" />
            <div className="text-4xl font-black italic manga-font text-yellow-400">{data.following.length}</div>
            <div className="text-[10px] font-black uppercase tracking-widest opacity-40 mt-2">Abonnements</div>
          </Card>
          <Card padding="lg" className="text-center bg-gradient-to-br from-red-400/5 to-pink-500/5 border-red-500/10">
            <Heart className="w-10 h-10 text-red-500 mx-auto mb-4" />
            <div className="text-4xl font-black italic manga-font text-red-500">{data.followers.length}</div>
            <div className="text-[10px] font-black uppercase tracking-widest opacity-40 mt-2">Abonnés</div>
          </Card>
        </div>

        {/* Following */}
        <section className="mb-16">
          <h2 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.3em] flex items-center gap-2 px-4">
            <UserPlus className="w-4 h-4 text-yellow-400" /> Abonnements ({data.following.length})
          </h2>
          <div className="space-y-4">
            {data.following.map((f: Friendship) => (
              <FriendCard key={f.id} friend={f} type="following" onUnfollow={toggleFollow} />
            ))}
            {data.following.length === 0 && (
              <div className="text-center py-16 opacity-20">
                <Search className="w-16 h-16 mx-auto mb-4" />
                <p className="text-lg font-black italic manga-font uppercase">
                  Vous ne suivez personne pour l'instant.
                </p>
                <p className="text-xs opacity-60 mt-2">
                  Explorez les profils et commencez à suivre d'autres joueurs !
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Followers */}
        <section>
          <h2 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.3em] flex items-center gap-2 px-4">
            <Heart className="w-4 h-4 text-red-500" /> Abonnés ({data.followers.length})
          </h2>
          <div className="space-y-4">
            {data.followers.map((f: Friendship) => (
              <FriendCard key={f.id} friend={f} type="follower" />
            ))}
            {data.followers.length === 0 && (
              <div className="text-center py-16 opacity-20">
                <Users className="w-16 h-16 mx-auto mb-4" />
                <p className="text-lg font-black italic manga-font uppercase">
                  Pas encore d'abonnés.
                </p>
                <p className="text-xs opacity-60 mt-2">
                  Jouez, créez des fusions et grimpez le classement pour attirer des abonnés !
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </AnimatedPage>
  );
};

export default FriendsPage;
