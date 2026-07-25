import React from 'react';
import { Shield, Zap, Sparkles, Camera, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Avatar } from '../../../components/ui/Avatar';

interface ProfileHeaderCardProps {
  username: string | undefined;
  avatar?: string | null;
  rank?: string;
  level?: number;
  customUsernameColor?: string | null;
  unlockedBadges?: string[];
  isOwnProfile?: boolean;
  isUploadingAvatar?: boolean;
  onAvatarSelected?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const ProfileHeaderCard: React.FC<ProfileHeaderCardProps> = ({
  username,
  avatar,
  rank,
  level,
  customUsernameColor,
  unlockedBadges,
  isOwnProfile,
  isUploadingAvatar,
  onAvatarSelected,
}) => {
  const { t } = useTranslation();

  const avatarNode = (
    <Avatar
      src={avatar}
      name={username ?? '?'}
      className="h-32 w-32 rounded-[2rem] border border-[#F4F1E8]/10 text-5xl font-black italic shadow-2xl"
      fallbackClassName="bg-[#FDB913] text-[#0B0C10]"
    />
  );

  return (
    <div className="relative overflow-hidden bg-[#0F1016] px-8 py-12 md:px-12">
      {/* Trame demi-teinte + filet éditorial shu, signature de l'édition de nuit */}
      <div
        className="explore-halftone pointer-events-none absolute inset-0 opacity-[0.05]"
        aria-hidden
      />
      <span
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-[#E8442B] via-[#E8442B]/20 to-transparent"
        aria-hidden
      />
      {/* Sceau kanji « dossier » en filigrane */}
      <span
        className="font-manga pointer-events-none absolute -right-4 top-1/2 -translate-y-1/2 text-[11rem] font-black italic leading-none text-[#F4F1E8]/[0.03] select-none"
        aria-hidden
      >
        録
      </span>

      <div className="relative z-10 flex flex-col items-center gap-8 md:flex-row">
        {/* Avatar — avec upload en overlay sur son propre profil */}
        {isOwnProfile && onAvatarSelected ? (
          <label className="group/av relative shrink-0 cursor-pointer rounded-[2rem]">
            {avatarNode}
            <span className="absolute inset-0 flex flex-col items-center justify-center gap-1 rounded-[2rem] bg-[#0B0C10]/75 opacity-0 backdrop-blur-sm transition-opacity group-hover/av:opacity-100">
              {isUploadingAvatar ? (
                <Loader2 className="h-6 w-6 animate-spin text-[#FDB913]" />
              ) : (
                <Camera className="h-6 w-6 text-[#FDB913]" />
              )}
              <span className="text-[9px] font-black uppercase tracking-widest text-[#F4F1E8]">
                {isUploadingAvatar
                  ? t('auth.settings.avatar_uploading', 'Envoi…')
                  : t('auth.settings.avatar_change', 'Changer')}
              </span>
            </span>
            <span className="absolute -bottom-1.5 -right-1.5 grid h-8 w-8 place-items-center rounded-xl border border-[#0F1016] bg-[#E8442B] text-[#F4F1E8] shadow-lg transition-transform group-hover/av:scale-110">
              <Camera className="h-4 w-4" />
            </span>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={onAvatarSelected}
              disabled={isUploadingAvatar}
              aria-label={t('auth.settings.avatar_label', 'Photo de profil')}
            />
          </label>
        ) : (
          <div className="shrink-0">{avatarNode}</div>
        )}

        <div className="text-center md:text-left">
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
            {t('social.profile.eyebrow', 'Dossier · 探索者')}
          </p>
          <h1
            className="font-manga mb-4 text-5xl font-black uppercase italic tracking-tighter text-[#F4F1E8] drop-shadow-sm animate-in fade-in duration-300"
            style={{ color: customUsernameColor || undefined }}
          >
            {username}
          </h1>
          <div className="flex flex-wrap justify-center gap-3 md:justify-start">
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#E8442B]/25 bg-[#E8442B]/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
              <Shield className="h-3 w-3" />
              {t('social.profile.rank', { rank: rank || 'Explorateur' })}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#FDB913]/25 bg-[#FDB913]/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
              <Zap className="h-3 w-3 fill-current" />
              {t('social.profile.level', { level })}
            </span>
            {unlockedBadges?.includes('Sponsor Or') && (
              <span className="inline-flex items-center gap-1.5 rounded-lg border-none bg-gradient-to-r from-[#FDB913] to-[#E8442B] px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-[#0B0C10] shadow-lg">
                <Sparkles className="h-3 w-3 animate-spin" style={{ animationDuration: '3s' }} />
                SPONSOR OR
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
