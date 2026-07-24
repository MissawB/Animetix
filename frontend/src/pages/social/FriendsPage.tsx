import React from 'react';
import { Link } from 'react-router-dom';
import { Users, UserMinus, UserPlus, Search, Heart, ArrowLeft } from 'lucide-react';
import { useSocialDashboard } from '../../features/social/hooks/useSocialDashboard';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { Friendship } from '../../types';

const FriendCard: React.FC<{
  friend: Friendship;
  type: 'following' | 'follower';
  onUnfollow?: (userId: number) => void;
}> = ({ friend, type, onUnfollow }) => {
  const { t } = useTranslation();
  return (
    <div className="group flex items-center justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors hover:border-[#F4F1E8]/20">
      <Link
        to={`/profile/${friend.username}/`}
        className="flex min-w-0 flex-1 items-center gap-4 text-current no-underline"
      >
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#E8442B]/15 text-xl font-black italic text-[#E8442B] transition-transform group-hover:scale-110">
          {friend.username[0].toUpperCase()}
        </div>
        <div className="min-w-0">
          <div className="truncate text-lg font-black text-[#F4F1E8]">{friend.username}</div>
          <div className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
            {t('social.friends.level_since', 'Niveau {{level}} • Depuis {{date}}', {
              level: friend.level,
              date: new Date(friend.created_at).toLocaleDateString('fr-FR', {
                month: 'short',
                year: 'numeric',
              }),
            })}
          </div>
        </div>
      </Link>
      {type === 'following' && onUnfollow && (
        <Button
          variant="danger"
          size="sm"
          className="ml-4 shrink-0 rounded-full px-4 opacity-0 transition-opacity group-hover:opacity-100 !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8]"
          onClick={() => onUnfollow(friend.to_user)}
        >
          <UserMinus className="w-4 h-4" /> Unfollow
        </Button>
      )}
    </div>
  );
};

const FriendsPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError, toggleFollow } = useSocialDashboard();

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] max-w-5xl mx-auto px-6 py-16 space-y-12">
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError || !data)
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-20 text-[#E8442B] font-bold">
        {t('common.error')}
      </div>
    );

  return (
    <AnimatedPage>
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          {/* Header */}
          <header className="relative mb-16">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
              aria-hidden
            />
            <Link
              to="/social/dashboard/"
              className="relative inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] hover:text-[#F4F1E8] transition-colors mb-8 no-underline"
            >
              <ArrowLeft className="w-4 h-4" />{' '}
              {t('social.friends.back_to_dashboard', 'Retour au Dashboard')}
            </Link>
            <div className="relative flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                友
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                Nexus social · Réseau
              </span>
            </div>
            <h1 className="font-manga relative mt-4 text-5xl md:text-7xl font-black italic tracking-tighter uppercase text-[#F4F1E8]">
              {t('social.friends.title_my', 'MON')}{' '}
              <span className="text-[#E8442B]">{t('social.friends.title_network', 'RÉSEAU')}</span>
            </h1>
            <p className="relative mt-4 text-base font-medium text-[#8F94A5] uppercase tracking-[0.2em]">
              {t('social.friends.subtitle', 'Gérez vos abonnements et vos abonnés.')}
            </p>
          </header>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-6 mb-16">
            <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-6 py-8 text-center">
              <Users className="mx-auto mb-4 h-10 w-10 text-[#FDB913]" />
              <div className="font-manga text-4xl font-black italic text-[#FDB913]">
                {data.following.length}
              </div>
              <div className="mt-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                {t('social.friends.following', 'Abonnements')}
              </div>
            </div>
            <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-6 py-8 text-center">
              <Heart className="mx-auto mb-4 h-10 w-10 text-[#E8442B]" />
              <div className="font-manga text-4xl font-black italic text-[#E8442B]">
                {data.followers.length}
              </div>
              <div className="mt-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                {t('social.friends.followers', 'Abonnés')}
              </div>
            </div>
          </div>

          {/* Following */}
          <section className="mb-16">
            <h2 className="mb-8 flex items-center gap-2 px-4 text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
              <UserPlus className="w-4 h-4 text-[#FDB913]" />{' '}
              {t('social.friends.following_count', 'Abonnements ({{count}})', {
                count: data.following.length,
              })}
            </h2>
            <div className="space-y-4">
              {data.following.map((f: Friendship) => (
                <FriendCard key={f.id} friend={f} type="following" onUnfollow={toggleFollow} />
              ))}
              {data.following.length === 0 && (
                <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 py-16 text-center">
                  <Search className="mx-auto mb-4 h-16 w-16 text-[#8F94A5]/30" />
                  <p className="font-manga text-lg font-black italic uppercase text-[#F4F1E8]/50">
                    {t('social.friends.no_following', "Vous ne suivez personne pour l'instant.")}
                  </p>
                  <p className="mt-2 text-xs text-[#8F94A5]">
                    {t(
                      'social.friends.no_following_desc',
                      "Explorez les profils et commencez à suivre d'autres joueurs !",
                    )}
                  </p>
                </div>
              )}
            </div>
          </section>

          {/* Followers */}
          <section>
            <h2 className="mb-8 flex items-center gap-2 px-4 text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
              <Heart className="w-4 h-4 text-[#E8442B]" />{' '}
              {t('social.friends.followers_count', 'Abonnés ({{count}})', {
                count: data.followers.length,
              })}
            </h2>
            <div className="space-y-4">
              {data.followers.map((f: Friendship) => (
                <FriendCard key={f.id} friend={f} type="follower" />
              ))}
              {data.followers.length === 0 && (
                <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 py-16 text-center">
                  <Users className="mx-auto mb-4 h-16 w-16 text-[#8F94A5]/30" />
                  <p className="font-manga text-lg font-black italic uppercase text-[#F4F1E8]/50">
                    {t('social.friends.no_followers', "Pas encore d'abonnés.")}
                  </p>
                  <p className="mt-2 text-xs text-[#8F94A5]">
                    {t(
                      'social.friends.no_followers_desc',
                      'Jouez, créez des fusions et grimpez le classement pour attirer des abonnés !',
                    )}
                  </p>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default FriendsPage;
