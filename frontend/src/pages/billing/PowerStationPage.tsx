import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  Zap,
  Play,
  History,
  AlertCircle,
  Cpu,
  ShieldCheck,
  CreditCard,
  ToggleLeft,
  ToggleRight,
  ArrowUpRight,
  ArrowDownLeft,
  ChevronLeft,
  ChevronRight,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useAuthStore } from '../../store/authStore';
import { apiClient } from '../../utils/apiClient';
import { useToastStore } from '../../store/toastStore';
import { usePassiveMiningStore } from '../../store/passiveMiningStore';
import { PassiveAdMiner } from '../../features/billing/components/PassiveAdMiner';

interface WalletTransaction {
  amount: number;
  type: string;
  description: string;
  date: string;
}

const PowerStationPage: React.FC = () => {
  const { t } = useTranslation();
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();

  // Passive Mining Global State
  const {
    isEnabled,
    setEnabled,
    timeLeft,
    totalMined,
    status: passiveStatus,
  } = usePassiveMiningStore();

  // Active Mining State
  const [isWatching, setIsWatching] = useState(false);
  const [watchProgress, setWatchProgress] = useState(0);
  const [isCrediting, setIsCrediting] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  // Ledger state
  const [walletHistory, setWalletHistory] = useState<WalletTransaction[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterType, setFilterType] = useState('all');
  const [filterDirection, setFilterDirection] = useState('all');
  const [isLoadingLedger, setIsLoadingLedger] = useState(false);

  const fetchLedger = useCallback(
    async (page: number, type: string, direction: string) => {
      if (!user) return;
      setIsLoadingLedger(true);
      try {
        const queryParams = new URLSearchParams({
          page: String(page),
          page_size: '10',
          type,
          direction,
        });
        const data = await apiClient(`/api/v1/billing/wallet/balance/?${queryParams}`);
        setWalletHistory(data.history || []);
        if (data.pagination) {
          setTotalPages(data.pagination.total_pages);
          setCurrentPage(data.pagination.page);
        }
      } catch (err) {
        console.error('Failed to fetch transaction ledger:', err);
      } finally {
        setIsLoadingLedger(false);
      }
    },
    [user],
  );

  useEffect(() => {
    // Deferred so the synchronous setIsLoadingLedger(true) at the top of
    // fetchLedger doesn't run in the effect body (react-hooks/set-state-in-effect).
    queueMicrotask(() => {
      void fetchLedger(currentPage, filterType, filterDirection);
    });
  }, [fetchLedger, currentPage, filterType, filterDirection]);

  const handleWatchAd = () => {
    setIsWatching(true);
    setWatchProgress(0);

    const duration = 15000;
    const interval = 100;
    const steps = duration / interval;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      setWatchProgress((currentStep / steps) * 100);

      if (currentStep >= steps) {
        clearInterval(timer);
        completeAd();
      }
    }, interval);
  };

  const completeAd = async () => {
    setIsCrediting(true);
    try {
      const res = await apiClient('/api/v1/billing/wallet/watch-ad/', { method: 'POST' });
      addToast(
        t('billing.power_station.energy_injected', {
          defaultValue: 'Énergie injectée : +{{earned}} Bx !',
          earned: res.earned,
        }),
        'success',
      );
      await refetchUser();
      fetchLedger(1, filterType, filterDirection);
    } catch (_err) {
      addToast(t('billing.power_station.recharge_error', 'Erreur lors de la recharge.'), 'error');
    } finally {
      setIsWatching(false);
      setIsCrediting(false);
      setWatchProgress(0);
    }
  };

  return (
    <AnimatedPage>
      <PassiveAdMiner />
      <div className="min-h-screen bg-[#050505] text-white pt-24 pb-32 px-6 bg-manga-overlay">
        <div className="max-w-7xl mx-auto space-y-12">
          <header className="flex flex-col md:flex-row justify-between items-end gap-6 mb-16 border-b border-white/5 pb-8">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-cyan-500/20 rounded-2xl border border-cyan-500/30">
                  <CreditCard className="w-8 h-8 text-cyan-400" />
                </div>
                <h1 className="text-4xl md:text-6xl font-black italic uppercase tracking-tighter manga-font">
                  BERRIX <span className="text-cyan-400 text-glow">WALLET</span>
                </h1>
              </div>
              <p className="text-gray-400 font-bold uppercase tracking-[0.2em] text-xs">
                {t(
                  'billing.power_station.subtitle',
                  'Gérez vos jetons Berrix (Bx) et optimisez votre attention mining.',
                )}
              </p>
            </div>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Left Column: Berrix Wallet Card */}
            <div className="space-y-8">
              <h3 className="text-sm font-black uppercase tracking-[0.3em] text-gray-400 border-l-4 border-cyan-400 pl-4">
                Holographic Wallet
              </h3>

              {/* 3D-Tilt Card */}
              <motion.div
                whileHover={{ rotateY: 10, rotateX: -5, scale: 1.02 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="relative h-60 w-full rounded-[2rem] bg-gradient-to-br from-cyan-900/60 via-purple-950/40 to-black border border-cyan-500/30 p-8 flex flex-col justify-between shadow-[0_0_50px_rgba(6,182,212,0.15)] overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                  <Cpu className="w-32 h-32 text-cyan-400" />
                </div>

                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-[0.25em] text-cyan-400/80 block">
                      {t('billing.power_station.berrix_system', 'Système Berrix')}
                    </span>
                    <span className="text-xs text-gray-500 font-bold">
                      Node ID: {user?.id || 'GUEST-00'}
                    </span>
                  </div>
                  <Zap className="w-8 h-8 text-cyan-400 animate-pulse fill-current" />
                </div>

                <div>
                  <span className="text-[9px] font-black uppercase text-gray-500 tracking-widest block mb-1">
                    Total Balance
                  </span>
                  <span className="text-4xl font-black italic manga-font text-white">
                    {user?.wallet_balance?.toLocaleString() || 0}{' '}
                    <span className="text-cyan-400">Bx</span>
                  </span>
                </div>

                <div className="flex justify-between items-center text-[10px] text-gray-400 uppercase font-black tracking-widest">
                  <span>{user?.username || 'ANONYMOUS'}</span>
                  <span className="px-3 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400">
                    {user?.is_staff ? 'ADMIN NODE' : 'USER NODE'}
                  </span>
                </div>
              </motion.div>
            </div>

            {/* Right Column: Attention Mining Node & Active Mining */}
            <div className="lg:col-span-2 space-y-8">
              <h3 className="text-sm font-black uppercase tracking-[0.3em] text-gray-400 border-l-4 border-cyan-400 pl-4">
                Attention Mining & Reward Center
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Active Mining (Rewarded Ads) */}
                <Card className="bg-gradient-to-br from-cyan-950/20 to-black border-white/10 p-8 flex flex-col justify-between h-96 relative overflow-hidden">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="text-xl font-black italic uppercase manga-font">
                        Active Mining
                      </h4>
                      <span className="text-[9px] font-black uppercase text-cyan-400 tracking-wider px-2 py-0.5 bg-cyan-500/10 rounded-full border border-cyan-500/20">
                        +250 Bx
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 font-bold uppercase tracking-wide">
                      {t(
                        'billing.power_station.active_desc',
                        'Regardez un spot de transmission sponsorisé pour recharger.',
                      )}
                    </p>
                  </div>

                  <div className="h-44 bg-black/60 rounded-xl border border-white/5 flex flex-col items-center justify-center relative overflow-hidden group">
                    {isWatching ? (
                      <div className="w-full h-full flex flex-col items-center justify-center p-6 space-y-4">
                        <div className="flex items-center gap-3">
                          <span className="text-cyan-400 font-black italic text-xs animate-pulse tracking-widest">
                            {t('billing.power_station.transmission_active', 'TRANSMISSION ACTIVE')}
                          </span>
                          <button
                            onClick={() => setIsMuted(!isMuted)}
                            className="text-gray-400 hover:text-cyan-400 transition-colors"
                          >
                            {isMuted ? (
                              <VolumeX className="w-4 h-4" />
                            ) : (
                              <Volume2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <div className="w-full max-w-xs h-2 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(6,182,212,1)]"
                            style={{ width: `${watchProgress}%` }}
                          />
                        </div>
                        <p className="text-[8px] text-gray-500 uppercase tracking-widest">
                          {t(
                            'billing.power_station.dont_close_console',
                            'Ne fermez pas la console',
                          )}
                        </p>
                      </div>
                    ) : (
                      <>
                        <Button
                          className="rounded-full w-16 h-16 bg-cyan-500 hover:bg-cyan-400 text-black flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.3)] transition-all hover:scale-105"
                          onClick={handleWatchAd}
                          disabled={isCrediting}
                        >
                          <Play className="w-6 h-6 fill-current ml-0.5" />
                        </Button>
                        <span className="mt-4 text-[9px] font-black uppercase tracking-widest text-cyan-400">
                          {t('billing.power_station.start_recharge', 'Lancer la recharge')}
                        </span>
                      </>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[9px] text-gray-500 font-black uppercase tracking-widest">
                    <ShieldCheck className="w-4 h-4 text-green-500" /> NeuralGuard Sec-V2
                  </div>
                </Card>

                {/* Passive Mining Node */}
                <Card className="bg-gradient-to-br from-purple-950/20 to-black border-white/10 p-8 flex flex-col justify-between h-96 relative overflow-hidden">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="text-xl font-black italic uppercase manga-font">
                        Passive Mining
                      </h4>
                      <button onClick={() => setEnabled(!isEnabled)} className="focus:outline-none">
                        {isEnabled ? (
                          <ToggleRight className="w-10 h-10 text-cyan-400" />
                        ) : (
                          <ToggleLeft className="w-10 h-10 text-gray-600" />
                        )}
                      </button>
                    </div>
                    <p className="text-xs text-gray-400 font-bold uppercase tracking-wide">
                      {t(
                        'billing.power_station.passive_desc',
                        'Mine des Berrix en arrière-plan pendant que vous naviguez ou jouez.',
                      )}
                    </p>
                  </div>

                  {/* Circular Progress & Timer */}
                  <div className="flex flex-col items-center justify-center space-y-2 py-4">
                    <div className="relative w-28 h-28 flex items-center justify-center">
                      <svg className="absolute w-full h-full transform -rotate-90">
                        <circle
                          cx="56"
                          cy="56"
                          r="46"
                          stroke="rgba(255,255,255,0.05)"
                          strokeWidth="6"
                          fill="transparent"
                        />
                        <circle
                          cx="56"
                          cy="56"
                          r="46"
                          stroke={isEnabled ? '#06b6d4' : '#4b5563'}
                          strokeWidth="6"
                          fill="transparent"
                          strokeDasharray={289}
                          strokeDashoffset={289 - 289 * (isEnabled ? (180 - timeLeft) / 180 : 0)}
                          className="transition-all duration-1000"
                        />
                      </svg>
                      <div className="text-center z-10">
                        <span className="text-2xl font-black italic manga-font">
                          {isEnabled
                            ? `${Math.floor(timeLeft / 60)}:${String(timeLeft % 60).padStart(2, '0')}`
                            : '--:--'}
                        </span>
                        <span className="text-[8px] font-black uppercase tracking-widest text-gray-500 block mt-0.5">
                          Cycle Timer
                        </span>
                      </div>
                    </div>
                    <span
                      className={`text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded-full border ${
                        passiveStatus === 'ONLINE'
                          ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400 animate-pulse'
                          : passiveStatus === 'COOLDOWN'
                            ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                            : 'bg-white/5 border-white/10 text-gray-500'
                      }`}
                    >
                      STATUS: {passiveStatus}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-[9px] text-gray-500 font-black uppercase tracking-widest">
                    <span>
                      Total passive: <span className="text-cyan-400">{totalMined} Bx</span>
                    </span>
                    <span>Rate: +20 Bx / 3 min</span>
                  </div>
                </Card>
              </div>
            </div>
          </div>

          {/* History Section (Complete Ledger with Pagination) */}
          <div className="mt-20 space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <h3 className="text-2xl font-black italic uppercase manga-font flex items-center gap-3">
                <History className="w-6 h-6 text-cyan-400" /> Transaction Ledger
              </h3>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-4">
                <select
                  value={filterType}
                  onChange={(e) => {
                    setFilterType(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-black uppercase tracking-wider text-gray-400 focus:outline-none focus:border-cyan-400"
                >
                  <option value="all">All Categories</option>
                  <option value="ad_passive">Passive Mining</option>
                  <option value="ad_active">Active Recharge</option>
                  <option value="purchase">Direct Purchase</option>
                  <option value="ai_usage">AI Consumption</option>
                  <option value="daily_grant">Daily Grant</option>
                </select>

                <select
                  value={filterDirection}
                  onChange={(e) => {
                    setFilterDirection(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-black uppercase tracking-wider text-gray-400 focus:outline-none focus:border-cyan-400"
                >
                  <option value="all">All Directions</option>
                  <option value="credit">Credits Only (+)</option>
                  <option value="debit">Debits Only (-)</option>
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden">
              {isLoadingLedger ? (
                <div className="p-20 text-center text-gray-500 font-black animate-pulse uppercase tracking-[0.2em] text-xs">
                  Querying database ledger...
                </div>
              ) : walletHistory.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse min-w-[600px]">
                    <thead>
                      <tr className="border-b border-white/5 bg-white/5">
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                          Transaction Description
                        </th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                          Source type
                        </th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                          Timestamp
                        </th>
                        <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 text-right">
                          Amount
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {walletHistory.map((t, i) => (
                        <tr
                          key={i}
                          className="border-b border-white/5 hover:bg-white/5 transition-colors"
                        >
                          <td className="p-6 font-bold text-sm text-white">{t.description}</td>
                          <td className="p-6">
                            <span
                              className={`text-[8px] font-black uppercase px-3 py-1 rounded-full border ${
                                t.amount > 0
                                  ? 'border-cyan-500/30 text-cyan-400'
                                  : 'border-purple-500/30 text-purple-400'
                              }`}
                            >
                              {t.type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="p-6 text-xs text-gray-500 font-bold">
                            {new Date(t.date).toLocaleString()}
                          </td>
                          <td
                            className={`p-6 text-right font-black italic manga-font flex items-center justify-end gap-1.5 ${t.amount > 0 ? 'text-green-400' : 'text-purple-400'}`}
                          >
                            {t.amount > 0 ? (
                              <>
                                <ArrowDownLeft className="w-3.5 h-3.5" /> +{t.amount}
                              </>
                            ) : (
                              <>
                                <ArrowUpRight className="w-3.5 h-3.5" /> {t.amount}
                              </>
                            )}{' '}
                            Bx
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-20 text-center space-y-4">
                  <AlertCircle className="w-12 h-12 text-gray-700 mx-auto" />
                  <p className="text-gray-500 font-bold uppercase tracking-widest text-sm">
                    No transaction ledger entries matched your query.
                  </p>
                </div>
              )}

              {/* Pagination Footer */}
              {totalPages > 1 && (
                <div className="p-6 border-t border-white/5 bg-white/5 flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                    Page {currentPage} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                      className="flex items-center gap-1"
                    >
                      <ChevronLeft className="w-4 h-4" /> Previous
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage >= totalPages}
                      onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                      className="flex items-center gap-1"
                    >
                      Next <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default PowerStationPage;
