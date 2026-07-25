import React from 'react';
import { User as UserIcon, Shield, Zap, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../../components/ui/Badge';
import { Avatar } from '../../../components/ui/Avatar';

interface ProfileHeaderCardProps {
  username: string | undefined;
  avatar?: string | null;
  rank?: string;
  level?: number;
  customUsernameColor?: string | null;
  unlockedBadges?: string[];
}

export const ProfileHeaderCard: React.FC<ProfileHeaderCardProps> = ({
  username,
  avatar,
  rank,
  level,
  customUsernameColor,
  unlockedBadges,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-gradient-to-r from-yellow-400 to-orange-500 p-12 text-black relative overflow-hidden">
      <div className="absolute top-0 right-0 p-12 opacity-10">
        <UserIcon className="w-64 h-64 -rotate-12" />
      </div>
      <div className="flex flex-col md:flex-row items-center gap-8 relative z-10">
        <Avatar
          src={avatar}
          name={username ?? '?'}
          className="w-32 h-32 rounded-[2.5rem] text-5xl font-black italic shadow-2xl border-4 border-white/20"
          fallbackClassName="bg-black text-white"
        />
        <div className="text-center md:text-left">
          <h1
            className="text-5xl font-black italic manga-font tracking-tighter mb-2 uppercase drop-shadow-sm animate-in fade-in duration-300"
            style={{ color: customUsernameColor || undefined }}
          >
            {username}
          </h1>
          <div className="flex flex-wrap justify-center md:justify-start gap-4">
            <Badge
              variant="neutral"
              className="bg-black text-white border-none py-2 px-4 shadow-lg"
            >
              <Shield className="w-3 h-3" />{' '}
              {t('social.profile.rank', { rank: rank || 'Explorateur' })}
            </Badge>
            <Badge
              variant="neutral"
              className="bg-white/30 backdrop-blur-md text-black border-none py-2 px-4 shadow-lg"
            >
              <Zap className="w-3 h-3" /> {t('social.profile.level', { level })}
            </Badge>
            {unlockedBadges?.includes('Sponsor Or') && (
              <Badge
                variant="neutral"
                className="bg-gradient-to-r from-yellow-400 to-amber-500 text-black border-none py-2 px-4 shadow-lg font-black animate-pulse flex items-center gap-1.5"
              >
                <Sparkles
                  className="w-3 h-3 text-black animate-spin"
                  style={{ animationDuration: '3s' }}
                />{' '}
                SPONSOR OR
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
