import React, { useEffect } from 'react';
import { BellOff, Info, CheckCircle2, AlertTriangle, Star } from 'lucide-react';
import { Notification } from '../../types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useNotificationStore } from '../../store/notificationStore';

import { useTranslation } from 'react-i18next';

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

  if (isLoading) return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <CardSkeleton />
      <div className="mt-6 space-y-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );

  return (
    
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="flex justify-between items-end mb-12">
          <div>
              <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase">
              FLUX <span className="text-blue-500">SYSTÈME</span>
              </h1>
              <p className="text-xs font-black uppercase opacity-40 mt-2 tracking-widest">Tes interactions récentes</p>
          </div>
          {notifications && notifications.some(n => !n.is_read) && (
              <Button 
                variant="outline" 
                size="sm" 
                className="text-[10px] uppercase border-none text-blue-500 hover:text-blue-600"
                onClick={() => markAllReadMutation.mutate()}
              >
                  Tout marquer comme lu
              </Button>
          )}
        </div>

        <div className="space-y-6">
          {!notifications || notifications.length === 0 ? (
            <Card padding="lg" className="text-center py-20 bg-white/5 border-white/5">
              <BellOff className="w-16 h-16 text-white opacity-10 mx-auto mb-4" />
              <p className="text-lg font-bold opacity-30 italic">Aucune notification pour le moment.</p>
            </Card>
          ) : (
            notifications.map((n: any) => (
              <Card 
                key={n.id} 
                padding="md" 
                className={`flex items-start gap-6 transition-all ${n.is_read ? 'opacity-60 grayscale' : 'bg-brand-primary text-white border-none scale-[1.02] shadow-brand-primary/20'}`}
              >
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 shadow-lg ${n.is_read ? 'bg-gray-100 dark:bg-navy-900' : 'bg-white/20'}`}>
                  {getNotificationIcon(n.type)}
                </div>
                <div className="flex-grow">
                  <h3 className="font-black italic manga-font text-lg mb-1 leading-none uppercase">{n.title}</h3>
                  <p className="font-medium opacity-80">{n.message}</p>
                  <div className="mt-3 text-[10px] font-black uppercase opacity-40 tracking-widest">
                    {new Date(n.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                {!n.is_read && <div className="w-3 h-3 bg-yellow-400 rounded-full shadow-[0_0_10px_rgba(250,204,21,0.5)]"></div>}
              </Card>
            ))
          )}
        </div>
      </div>
    
  );
};

const getNotificationIcon = (type: string) => {
    switch(type) {
        case 'achievement': return <Star className="w-6 h-6 text-yellow-500 shadow-sm" />;
        case 'social': return <CheckCircle2 className="w-6 h-6 text-green-500 shadow-sm" />;
        case 'system': return <Info className="w-6 h-6 text-blue-500 shadow-sm" />;
        default: return <AlertTriangle className="w-6 h-6 text-orange-500 shadow-sm" />;
    }
};

export default NotificationsPage;
