import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import {
  Database,
  RefreshCw,
  Trash2,
  Plus,
  Check,
  AlertCircle,
  Wifi,
  WifiOff,
  ArrowLeft,
  Award,
} from 'lucide-react';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useTranslation } from 'react-i18next';

interface OfflineGame {
  game_mode:
    | 'classic'
    | 'emoji'
    | 'animinator'
    | 'paradox'
    | 'vision_quest'
    | 'blindtest'
    | 'covertest';
  media_type: string;
  score: number;
  attempts: number;
}

interface SyncResponse {
  status: string;
  synced_items: number;
  xp_gained: number;
  daily_total: number;
}

const OfflineSyncPage: React.FC = () => {
  const { t } = useTranslation();
  const [offlineGames, setOfflineGames] = useState<OfflineGame[]>(() => {
    try {
      const stored = localStorage.getItem('ANIMETIX_OFFLINE_GAMES');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Failed to load offline games cache', e);
      return [];
    }
  });
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [simulateOffline, setSimulateOffline] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  const syncMutation = useMutation<SyncResponse, Error, void>({
    mutationFn: () =>
      apiClient('/api/v1/sync/offline/', {
        method: 'POST',
        body: JSON.stringify(offlineGames),
      }),
    onMutate: () => {
      setError(null);
      setSyncResult(null);
    },
    onSuccess: (response) => {
      if (response && response.status === 'success') {
        setSyncResult(response);
        setOfflineGames([]);
        saveToStorage([]);
      } else {
        setError(t('social.offline.unknown_error', 'Une erreur inconnue est survenue.'));
      }
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : '';
      setError(
        message ||
          t(
            'social.offline.connection_error',
            'Erreur de connexion avec le serveur de synchronisation.',
          ),
      );
    },
  });

  const isSyncing = syncMutation.isPending;

  // Sync browser online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const saveToStorage = (games: OfflineGame[]) => {
    try {
      localStorage.setItem('ANIMETIX_OFFLINE_GAMES', JSON.stringify(games));
    } catch (e) {
      console.error('Failed to save offline games cache', e);
    }
  };

  const addSimulatedGame = () => {
    const modes: OfflineGame['game_mode'][] = [
      'classic',
      'emoji',
      'paradox',
      'blindtest',
      'covertest',
    ];
    const mediaTypes = ['Anime', 'Manga', 'Character'];

    const randomMode = modes[Math.floor(Math.random() * modes.length)];
    const randomMedia = mediaTypes[Math.floor(Math.random() * mediaTypes.length)];
    const randomAttempts = Math.floor(Math.random() * 5) + 1;

    const newGame: OfflineGame = {
      game_mode: randomMode,
      media_type: randomMedia,
      score: 100, // 100 score needed to count as a win and gain XP
      attempts: randomAttempts,
    };

    const updated = [...offlineGames, newGame];
    setOfflineGames(updated);
    saveToStorage(updated);
    setSyncResult(null);
  };

  const clearQueue = () => {
    setOfflineGames([]);
    saveToStorage([]);
    setSyncResult(null);
    setError(null);
  };

  const forceSync = () => {
    if (offlineGames.length === 0) return;
    syncMutation.mutate();
  };

  const activeOnline = isOnline && !simulateOffline;

  const ghostBtn =
    'inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-4 py-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <AnimatedPage>
        <div className="mx-auto max-w-4xl px-6 py-16">
          {/* Navigation retour */}
          <header className="relative mb-12">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-40"
              aria-hidden
            />
            <Link
              to="/social/dashboard/"
              className="relative mb-8 inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
            >
              <ArrowLeft className="h-4 w-4" />{' '}
              {t('social.offline.back_dashboard', 'Retour au Dashboard')}
            </Link>
            <div className="relative flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                同
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                {t('social.offline.eyebrow', 'Registre · Réconciliation')}
              </span>
            </div>
            <h1 className="font-manga mt-4 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
              {t('social.offline.title_prefix', 'SYNCHRONISATION')}{' '}
              <span className="text-[#E8442B]">
                {t('social.offline.title_accent', 'HORS-LIGNE')}
              </span>
            </h1>
            <p className="mt-4 text-sm font-black uppercase tracking-[0.2em] text-[#8F94A5]">
              {t(
                'social.offline.subtitle',
                'Visualisez et réconciliez vos sessions de jeu locales.',
              )}
            </p>
          </header>

          {/* Network status card */}
          <div className="mb-10 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex items-center justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5">
              <div className="flex items-center gap-3">
                {activeOnline ? (
                  <Wifi className="h-6 w-6 text-[#FDB913]" />
                ) : (
                  <WifiOff className="h-6 w-6 text-[#E8442B]" />
                )}
                <div>
                  <p className="m-0 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {t('social.offline.network_status', 'Statut Réseau')}
                  </p>
                  <p className="m-0 text-sm font-bold text-[#F4F1E8]">
                    {activeOnline
                      ? t('social.offline.online', 'En ligne (Connecté)')
                      : t('social.offline.offline_label', 'Hors-ligne')}
                  </p>
                </div>
              </div>
              <button className={ghostBtn} onClick={() => setSimulateOffline(!simulateOffline)}>
                {simulateOffline
                  ? t('social.offline.reconnect', 'Reconnecter')
                  : t('social.offline.simulate_offline', 'Simuler Offline')}
              </button>
            </div>

            <div className="flex items-center gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5">
              <Database className="h-6 w-6 text-[#FDB913]" />
              <div>
                <p className="m-0 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('social.offline.queue', "File d'attente")}
                </p>
                <p className="m-0 text-sm font-bold text-[#F4F1E8]">
                  {t('social.offline.pending_count', '{{count}} partie(s) en attente', {
                    count: offlineGames.length,
                  })}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5">
              <Award className="h-6 w-6 text-[#FDB913]" />
              <div>
                <p className="m-0 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('social.offline.daily_max', 'Gain maximum quotidien')}
                </p>
                <p className="m-0 text-sm font-bold text-[#F4F1E8]">
                  {t('social.offline.daily_xp', '200 XP par jour')}
                </p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="mb-10 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
            <div className="flex flex-wrap gap-4">
              <button
                onClick={addSimulatedGame}
                className="font-manga inline-flex items-center gap-2 rounded-xl bg-[#E8442B] px-5 py-3 text-sm font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                <Plus className="h-4 w-4" />{' '}
                {t('social.offline.simulate_game', 'Simuler Partie Locale')}
              </button>
              {offlineGames.length > 0 && (
                <button
                  onClick={clearQueue}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#E8442B]/40 bg-transparent px-5 py-3 text-sm font-black uppercase text-[#E8442B] transition-colors hover:bg-[#E8442B]/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                >
                  <Trash2 className="h-4 w-4" /> {t('social.offline.clear_queue', 'Vider la file')}
                </button>
              )}
            </div>

            <button
              onClick={forceSync}
              disabled={!activeOnline || offlineGames.length === 0 || isSyncing}
              className="font-manga inline-flex items-center gap-2 rounded-xl bg-[#E8442B] px-5 py-3 text-sm font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
            >
              <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing
                ? t('social.offline.syncing', 'Synchronisation...')
                : t('social.offline.force_sync', 'Forcer la réconciliation')}
            </button>
          </div>

          {/* Alerts & Results */}
          {error && (
            <div className="mb-10 flex items-center gap-4 rounded-2xl border border-[#E8442B]/40 bg-[#E8442B]/10 p-5 text-[#E8442B]">
              <AlertCircle className="h-6 w-6 shrink-0" />
              <p className="m-0 text-sm font-bold">{error}</p>
            </div>
          )}

          {syncResult && (
            <div className="mb-10 rounded-2xl border border-[#FDB913]/40 bg-[#FDB913]/[0.06] p-6">
              <div className="mb-4 flex items-center gap-3 text-[#FDB913]">
                <Check className="h-6 w-6" />
                <h3 className="font-manga m-0 text-lg font-black uppercase italic">
                  {t('social.offline.sync_success', 'Synchronisation Réussie !')}
                </h3>
              </div>
              <div className="mt-2 grid grid-cols-3 gap-4 text-center">
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                  <p className="m-0 text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
                    {t('social.offline.synced_items', 'Parties synchronisées')}
                  </p>
                  <p className="font-manga m-0 text-2xl font-black italic text-[#FDB913]">
                    {syncResult.synced_items}
                  </p>
                </div>
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                  <p className="m-0 text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
                    {t('social.offline.xp_won', 'XP Remportés')}
                  </p>
                  <p className="font-manga m-0 text-2xl font-black italic text-[#FDB913]">
                    +{syncResult.xp_gained} XP
                  </p>
                </div>
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                  <p className="m-0 text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
                    {t('social.offline.daily_total', 'Cumul quotidien')}
                  </p>
                  <p className="font-manga m-0 text-2xl font-black italic text-[#FDB913]">
                    {syncResult.daily_total} / 200 XP
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Games Table/List */}
          <div className="overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]">
            <div className="border-b border-[#F4F1E8]/10 p-6">
              <h2 className="font-manga m-0 text-lg font-black uppercase italic text-[#F4F1E8]">
                {t('social.offline.pending_table_title', 'Parties en attente de synchronisation')}
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-[#F4F1E8]/10 bg-[#0B0C10]">
                    <th className="p-4 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                      {t('social.offline.th_game_mode', 'Mode de Jeu')}
                    </th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                      {t('social.offline.th_media_type', 'Type Média')}
                    </th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                      {t('common.score', 'Score')}
                    </th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                      {t('social.offline.th_attempts', 'Tentatives')}
                    </th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                      {t('social.offline.th_xp_estimated', 'XP Estimés')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {offlineGames.map((game, i) => (
                    <tr
                      key={i}
                      className="border-b border-[#F4F1E8]/10 transition-colors hover:bg-[#F4F1E8]/[0.03]"
                    >
                      <td className="p-4 text-xs font-bold capitalize text-[#F4F1E8]">
                        {game.game_mode}
                      </td>
                      <td className="p-4 text-xs font-bold text-[#F4F1E8]">{game.media_type}</td>
                      <td className="p-4 text-xs">
                        <span
                          className={`font-black italic ${game.score === 100 ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                        >
                          {game.score} / 100
                        </span>
                      </td>
                      <td className="p-4 text-xs font-bold text-[#F4F1E8]">{game.attempts}</td>
                      <td className="p-4 text-xs font-black text-[#FDB913]">
                        {game.score === 100 ? '+10 XP' : '0 XP'}
                      </td>
                    </tr>
                  ))}
                  {offlineGames.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="p-16 text-center text-xs font-bold uppercase tracking-widest text-[#8F94A5]/60"
                      >
                        {t(
                          'social.offline.empty_table',
                          'Aucune partie en attente. Utilisez le bouton "Simuler Partie Locale" pour en ajouter.',
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default OfflineSyncPage;
