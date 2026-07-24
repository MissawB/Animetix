import React, { useState } from 'react';
import { Link2, Link2Off, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../../components/ui/Card';
import { Modal } from '../../../components/ui/Modal';
import { socialService } from '../../../features/social/services/socialService';
import { TrackerConnection } from '../../../features/social/types/profileTypes';

interface TrackerSyncPanelProps {
  connections: TrackerConnection[] | undefined;
}

export const TrackerSyncPanel: React.FC<TrackerSyncPanelProps> = ({ connections }) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [linkingTracker, setLinkingTracker] = useState<'myanimelist' | 'anilist' | null>(null);
  const [trackerUsername, setTrackerUsername] = useState('');
  const [trackerToken, setTrackerToken] = useState('');
  const [linkError, setLinkError] = useState('');

  const linkMutation = useMutation({
    mutationFn: ({
      tracker,
      username,
      token,
    }: {
      tracker: string;
      username: string;
      token: string;
    }) => socialService.linkTracker(tracker, username, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackerConnections'] });
      setLinkingTracker(null);
      setTrackerUsername('');
      setTrackerToken('');
      setLinkError('');
    },
    onError: (err: unknown) => {
      setLinkError(err instanceof Error ? err.message : 'Failed to link tracker');
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: (tracker: string) => socialService.unlinkTracker(tracker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackerConnections'] });
    },
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

  return (
    <Card
      padding="lg"
      className="mt-12 bg-gray-50 dark:bg-black/20 border-none shadow-xl text-black dark:text-white"
    >
      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
        <Link2 className="w-4 h-4 text-blue-500" />{' '}
        {t('social.profile.tracker_sync', 'Synchronisation des Trackers')}
      </h3>
      <p className="text-xs opacity-60 mb-6">
        {t(
          'social.profile.tracker_desc',
          'Associez vos comptes pour synchroniser automatiquement votre progression de lecture de mangas.',
        )}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* MyAnimeList */}
        <div className="p-6 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 flex flex-col justify-between min-h-[160px]">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-black italic uppercase text-sm">MyAnimeList</span>
              {connections?.some((c) => c.tracker === 'myanimelist') ? (
                <span className="text-[10px] bg-green-500/10 text-green-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
                  {t('social.profile.connected', 'Connecté')}
                </span>
              ) : (
                <span className="text-[10px] bg-gray-500/10 text-gray-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
                  {t('social.profile.not_connected', 'Non connecté')}
                </span>
              )}
            </div>
            {connections?.some((c) => c.tracker === 'myanimelist') ? (
              <p className="text-xs opacity-60">
                {t('social.profile.user_label', 'Utilisateur')} :{' '}
                <span className="font-bold">
                  {connections.find((c) => c.tracker === 'myanimelist')?.username}
                </span>
              </p>
            ) : (
              <p className="text-xs opacity-40 italic">
                {t(
                  'social.profile.mal_hint',
                  'Mettez à jour votre liste MAL en lisant vos mangas.',
                )}
              </p>
            )}
          </div>
          <div className="mt-4">
            {connections?.some((c) => c.tracker === 'myanimelist') ? (
              <button
                onClick={() => unlinkMutation.mutate('myanimelist')}
                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
              >
                <Link2Off className="w-3.5 h-3.5" /> {t('social.profile.unlink', 'Dissocier')}
              </button>
            ) : (
              <button
                onClick={() => setLinkingTracker('myanimelist')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
              >
                <Link2 className="w-3.5 h-3.5" /> {t('social.profile.link_mal', 'Associer MAL')}
              </button>
            )}
          </div>
        </div>

        {/* AniList */}
        <div className="p-6 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 flex flex-col justify-between min-h-[160px]">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-black italic uppercase text-sm">AniList</span>
              {connections?.some((c) => c.tracker === 'anilist') ? (
                <span className="text-[10px] bg-green-500/10 text-green-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
                  {t('social.profile.connected', 'Connecté')}
                </span>
              ) : (
                <span className="text-[10px] bg-gray-500/10 text-gray-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
                  {t('social.profile.not_connected', 'Non connecté')}
                </span>
              )}
            </div>
            {connections?.some((c) => c.tracker === 'anilist') ? (
              <p className="text-xs opacity-60">
                {t('social.profile.user_label', 'Utilisateur')} :{' '}
                <span className="font-bold">
                  {connections.find((c) => c.tracker === 'anilist')?.username}
                </span>
              </p>
            ) : (
              <p className="text-xs opacity-40 italic">
                {t(
                  'social.profile.anilist_hint',
                  'Mettez à jour votre liste AniList automatiquement.',
                )}
              </p>
            )}
          </div>
          <div className="mt-4">
            {connections?.some((c) => c.tracker === 'anilist') ? (
              <button
                onClick={() => unlinkMutation.mutate('anilist')}
                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
              >
                <Link2Off className="w-3.5 h-3.5" /> {t('social.profile.unlink', 'Dissocier')}
              </button>
            ) : (
              <button
                onClick={() => setLinkingTracker('anilist')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1.5 border-none cursor-pointer"
              >
                <Link2 className="w-3.5 h-3.5" />{' '}
                {t('social.profile.link_anilist', 'Associer AniList')}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Linking Form Overlay/Modal */}
      <Modal
        isOpen={Boolean(linkingTracker)}
        onClose={() => setLinkingTracker(null)}
        title={
          <span className="text-xs font-black uppercase tracking-wider text-blue-400">
            {t('social.profile.link_tracker', 'Associer')}{' '}
            {linkingTracker === 'anilist' ? 'AniList' : 'MyAnimeList'}
          </span>
        }
        size="md"
        contentClassName="bg-[#0d0f17] border border-blue-500/30 rounded-2xl shadow-2xl"
      >
        <form onSubmit={handleLinkSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="tracker-username"
                className="text-[9px] font-black uppercase tracking-widest opacity-60 text-white"
              >
                {t('social.profile.username_label', "Nom d'utilisateur")}
              </label>
              <input
                id="tracker-username"
                type="text"
                aria-label={t('social.profile.username_label', "Nom d'utilisateur")}
                value={trackerUsername}
                onChange={(e) => setTrackerUsername(e.target.value)}
                required
                placeholder="Ex: OtakuMaster"
                className="bg-[#05050a]/50 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-semibold"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="tracker-token"
                className="text-[9px] font-black uppercase tracking-widest opacity-60 text-white"
              >
                {t('social.profile.token_label', "Jeton d'accès (Access Token)")}
              </label>
              <input
                id="tracker-token"
                type="password"
                aria-label={t('social.profile.token_label', "Jeton d'accès")}
                value={trackerToken}
                onChange={(e) => setTrackerToken(e.target.value)}
                required
                placeholder={t('social.profile.token_placeholder', 'Entrez votre jeton API')}
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
            {linkMutation.isPending ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              t('social.profile.save_connection', 'Enregistrer la connexion')
            )}
          </button>
        </form>
      </Modal>
    </Card>
  );
};
