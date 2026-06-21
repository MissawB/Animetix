import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Database, RefreshCw, Trash2, Plus, Check, AlertCircle, Wifi, WifiOff, ArrowLeft, Award } from 'lucide-react';
import { apiClient } from '../../utils/apiClient';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

interface OfflineGame {
  game_mode: "classic" | "emoji" | "animinator" | "paradox" | "vision_quest" | "blindtest" | "covertest";
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
  const [offlineGames, setOfflineGames] = useState<OfflineGame[]>(() => {
    try {
      const stored = localStorage.getItem('ANIMETIX_OFFLINE_GAMES');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error("Failed to load offline games cache", e);
      return [];
    }
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [simulateOffline, setSimulateOffline] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

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
      console.error("Failed to save offline games cache", e);
    }
  };

  const addSimulatedGame = () => {
    const modes: OfflineGame["game_mode"][] = ['classic', 'emoji', 'paradox', 'blindtest', 'covertest'];
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

  const forceSync = async () => {
    if (offlineGames.length === 0) return;
    setIsSyncing(true);
    setError(null);
    setSyncResult(null);

    try {
      const response = await apiClient('/api/v1/sync/offline/', {
        method: 'POST',
        body: JSON.stringify(offlineGames),
      });

      if (response && response.status === 'success') {
        setSyncResult(response);
        // Clear local queue on success
        setOfflineGames([]);
        saveToStorage([]);
      } else {
        throw new Error(response?.error || 'Une erreur inconnue est survenue.');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      setError(message || 'Erreur de connexion avec le serveur de synchronisation.');
    } finally {
      setIsSyncing(false);
    }
  };

  const activeOnline = isOnline && !simulateOffline;

  return (
    <AnimatedPage>
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Navigation retour */}
        <header className="mb-12">
          <Link to="/social/dashboard/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest opacity-40 hover:opacity-100 transition-opacity mb-8 no-underline text-current">
            <ArrowLeft className="w-4 h-4" /> Retour au Dashboard
          </Link>
          <h1 className="text-5xl md:text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
            SYNCHRONISATION <span className="text-yellow-400 text-glow">HORS-LIGNE</span>
          </h1>
          <p className="text-lg font-bold opacity-30 uppercase tracking-[0.2em]">
            Visualisez et réconciliez vos sessions de jeu locales.
          </p>
        </header>

        {/* Network status card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <Card padding="md" className="flex items-center justify-between bg-[#1a1a2e]/60 border-white/5">
            <div className="flex items-center gap-3">
              {activeOnline ? (
                <Wifi className="w-6 h-6 text-green-500 animate-pulse" />
              ) : (
                <WifiOff className="w-6 h-6 text-red-500" />
              )}
              <div>
                <p className="text-[10px] font-black uppercase opacity-40 m-0">Statut Réseau</p>
                <p className="text-sm font-bold m-0">
                  {activeOnline ? 'En ligne (Connecté)' : 'Hors-ligne'}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-[10px] px-2 py-1 h-auto"
              onClick={() => setSimulateOffline(!simulateOffline)}
            >
              {simulateOffline ? 'Reconnecter' : 'Simuler Offline'}
            </Button>
          </Card>

          <Card padding="md" className="flex items-center gap-4 bg-[#1a1a2e]/60 border-white/5">
            <Database className="w-6 h-6 text-yellow-400" />
            <div>
              <p className="text-[10px] font-black uppercase opacity-40 m-0">File d'attente</p>
              <p className="text-sm font-bold m-0">
                {offlineGames.length} partie(s) en attente
              </p>
            </div>
          </Card>

          <Card padding="md" className="flex items-center gap-4 bg-[#1a1a2e]/60 border-white/5">
            <Award className="w-6 h-6 text-cyan-400" />
            <div>
              <p className="text-[10px] font-black uppercase opacity-40 m-0">Gain maximum quotidien</p>
              <p className="text-sm font-bold m-0">200 XP par jour</p>
            </div>
          </Card>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 justify-between items-center mb-10 bg-white/5 dark:bg-black/20 p-6 rounded-3xl border border-white/5">
          <div className="flex gap-4">
            <Button onClick={addSimulatedGame} className="gap-2">
              <Plus className="w-4 h-4" /> Simuler Partie Locale
            </Button>
            {offlineGames.length > 0 && (
              <Button variant="danger" onClick={clearQueue} className="gap-2">
                <Trash2 className="w-4 h-4" /> Vider la file
              </Button>
            )}
          </div>

          <Button
            variant={activeOnline && offlineGames.length > 0 ? "primary" : "outline"}
            onClick={forceSync}
            disabled={!activeOnline || offlineGames.length === 0 || isSyncing}
            className="gap-2 bg-yellow-400 text-black hover:bg-yellow-500 disabled:opacity-40"
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Synchronisation...' : 'Forcer la réconciliation'}
          </Button>
        </div>

        {/* Alerts & Results */}
        {error && (
          <div className="flex items-center gap-4 p-5 bg-red-500/10 border border-red-500/30 text-red-500 rounded-2xl mb-10">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <p className="text-sm font-bold m-0">{error}</p>
          </div>
        )}

        {syncResult && (
          <div className="p-6 bg-green-500/10 border border-green-500/30 text-green-500 rounded-2xl mb-10">
            <div className="flex items-center gap-3 mb-4">
              <Check className="w-6 h-6" />
              <h3 className="text-lg font-black uppercase italic m-0">Synchronisation Réussie !</h3>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center mt-2">
              <div className="bg-green-500/5 p-4 rounded-xl border border-green-500/10">
                <p className="text-[10px] uppercase font-bold opacity-60 m-0">Parties synchronisées</p>
                <p className="text-2xl font-black italic manga-font m-0">{syncResult.synced_items}</p>
              </div>
              <div className="bg-green-500/5 p-4 rounded-xl border border-green-500/10">
                <p className="text-[10px] uppercase font-bold opacity-60 m-0">XP Remportés</p>
                <p className="text-2xl font-black italic manga-font m-0">+{syncResult.xp_gained} XP</p>
              </div>
              <div className="bg-green-500/5 p-4 rounded-xl border border-green-500/10">
                <p className="text-[10px] uppercase font-bold opacity-60 m-0">Cumul quotidien</p>
                <p className="text-2xl font-black italic manga-font m-0">{syncResult.daily_total} / 200 XP</p>
              </div>
            </div>
          </div>
        )}

        {/* Games Table/List */}
        <Card padding="none" className="bg-[#1a1a2e]/30 border-white/5 overflow-hidden">
          <div className="p-6 border-b border-white/5">
            <h2 className="text-lg font-black uppercase italic m-0">Parties en attente de synchronisation</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="p-4 text-[10px] uppercase font-black tracking-wider opacity-60">Mode de Jeu</th>
                  <th className="p-4 text-[10px] uppercase font-black tracking-wider opacity-60">Type Média</th>
                  <th className="p-4 text-[10px] uppercase font-black tracking-wider opacity-60">Score</th>
                  <th className="p-4 text-[10px] uppercase font-black tracking-wider opacity-60">Tentatives</th>
                  <th className="p-4 text-[10px] uppercase font-black tracking-wider opacity-60">XP Estimés</th>
                </tr>
              </thead>
              <tbody>
                {offlineGames.map((game, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="p-4 text-xs font-bold capitalize">{game.game_mode}</td>
                    <td className="p-4 text-xs font-bold">{game.media_type}</td>
                    <td className="p-4 text-xs">
                      <span className={`font-black italic ${game.score === 100 ? 'text-green-500' : 'text-yellow-500'}`}>
                        {game.score} / 100
                      </span>
                    </td>
                    <td className="p-4 text-xs font-bold">{game.attempts}</td>
                    <td className="p-4 text-xs font-black text-cyan-400">
                      {game.score === 100 ? '+10 XP' : '0 XP'}
                    </td>
                  </tr>
                ))}
                {offlineGames.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-16 text-center opacity-30 text-xs uppercase font-bold tracking-widest">
                      Aucune partie en attente. Utilisez le bouton "Simuler Partie Locale" pour en ajouter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </AnimatedPage>
  );
};

export default OfflineSyncPage;
