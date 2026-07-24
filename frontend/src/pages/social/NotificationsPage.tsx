import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { BellOff, Info, CheckCircle2, AlertTriangle, Star } from 'lucide-react';
import { Notification } from '../../types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useNotificationStore } from '../../store/notificationStore';

const NotificationsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { clearUnread } = useNotificationStore();

  const { data: notifications, isLoading } = useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: () => apiClient('/api/v1/social/notifications/'),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/social/notifications/', { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      clearUnread();
    },
  });

  useEffect(() => {
    const handleNewNotification = () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    };

    window.addEventListener('animetix:new_notification', handleNewNotification);
    return () => {
      window.removeEventListener('animetix:new_notification', handleNewNotification);
    };
  }, [queryClient]);

  if (isLoading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <CardSkeleton />
          <div className="mt-6 space-y-6">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-4xl px-6 py-16">
        <header className="relative mb-12">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-40"
            aria-hidden
          />
          <div className="relative flex items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  報
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  {t('social.notifications.eyebrow', 'Registre · Signaux')}
                </span>
              </div>
              <h1 className="font-manga mt-4 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-5xl">
                {t('social.notifications.title_prefix', 'FLUX')}{' '}
                <span className="text-[#E8442B]">
                  {t('social.notifications.title_accent', 'SYSTÈME')}
                </span>
              </h1>
              <p className="mt-3 text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                {t('social.notifications.subtitle', 'Tes interactions récentes')}
              </p>
            </div>
            {notifications && notifications.some((n) => !n.is_read) && (
              <button
                className="inline-flex flex-none cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-4 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#E8442B] hover:text-[#E8442B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                onClick={() => markAllReadMutation.mutate()}
              >
                {t('social.notifications.mark_all_read', 'Tout marquer comme lu')}
              </button>
            )}
          </div>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        <div className="space-y-6">
          {!notifications || notifications.length === 0 ? (
            <div className="flex flex-col items-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-20 text-center">
              <BellOff className="mx-auto mb-4 h-16 w-16 text-[#8F94A5]/30" />
              <p className="text-lg font-bold italic text-[#8F94A5]">
                {t('social.notifications.empty', 'Aucune notification pour le moment.')}
              </p>
            </div>
          ) : (
            notifications.map((n: Notification) => (
              <div
                key={n.id}
                className={`flex items-start gap-6 rounded-2xl border p-5 transition-all ${
                  n.is_read
                    ? 'border-[#F4F1E8]/10 bg-[#0F1016] opacity-60 grayscale'
                    : 'border-[#E8442B]/40 bg-[#E8442B]/[0.06]'
                }`}
              >
                <div
                  className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ${
                    n.is_read
                      ? 'border border-[#F4F1E8]/10 bg-[#0B0C10]'
                      : 'border border-[#E8442B]/30 bg-[#0B0C10]'
                  }`}
                >
                  {getNotificationIcon(n.type)}
                </div>
                <div className="flex-grow">
                  <h3 className="font-manga mb-1 text-lg font-black uppercase italic leading-none text-[#F4F1E8]">
                    {n.title}
                  </h3>
                  <p className="font-medium text-[#8F94A5]">{n.message}</p>
                  <div className="mt-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]/70">
                    {new Date(n.created_at).toLocaleDateString('fr-FR', {
                      day: 'numeric',
                      month: 'long',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
                {!n.is_read && (
                  <div className="mt-1 h-3 w-3 flex-none rounded-full bg-[#FDB913]"></div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'achievement':
      return <Star className="h-6 w-6 text-[#FDB913]" />;
    case 'social':
      return <CheckCircle2 className="h-6 w-6 text-[#F4F1E8]" />;
    case 'system':
      return <Info className="h-6 w-6 text-[#8F94A5]" />;
    default:
      return <AlertTriangle className="h-6 w-6 text-[#E8442B]" />;
  }
};

export default NotificationsPage;
