import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { CreditCard } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useAuthStore } from '../../store/authStore';
import { apiClient } from '../../utils/apiClient';
import { billingService } from '../../features/billing/services/billingService';
import {
  getRewardedAdProvider,
  type RewardedAdResult,
} from '../../features/billing/rewarded/rewardedAdProvider';
import { useToastStore } from '../../store/toastStore';
import { usePassiveMiningStore } from '../../store/passiveMiningStore';
import { PassiveAdMiner } from '../../features/billing/components/PassiveAdMiner';
import type { WalletTransaction } from '../../features/billing/types/walletTypes';

import { HolographicWalletCard } from './components/HolographicWalletCard';
import { ActiveMiningCard } from './components/ActiveMiningCard';
import { PassiveMiningCard } from './components/PassiveMiningCard';
import { TransactionLedgerTable } from './components/TransactionLedgerTable';

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
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isMounted = true;
    if (!user) return;

    const queryParams = new URLSearchParams({
      page: String(currentPage),
      page_size: '10',
      type: filterType,
      direction: filterDirection,
    });

    apiClient(`/api/v1/billing/wallet/balance/?${queryParams}`)
      .then((data) => {
        if (isMounted) {
          setWalletHistory(data.history || []);
          if (data.pagination) {
            setTotalPages(data.pagination.total_pages);
            setCurrentPage(data.pagination.page);
          }
        }
      })
      .catch((err) => {
        console.error('Failed to fetch transaction ledger:', err);
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingLedger(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [user, currentPage, filterType, filterDirection, reloadToken]);

  // La récompense est déclenchée par un fournisseur de pub REWARDED (agnostique
  // au réseau), jamais par une pub AdSense. En dev/sans réseau, un stub joue un
  // minuteur d'engagement. Cf. features/billing/rewarded/rewardedAdProvider.ts.
  const handleRecharge = () => {
    setIsWatching(true);
    setWatchProgress(0);
    getRewardedAdProvider()
      .showRewarded((pct) => setWatchProgress(pct))
      .then((result) => {
        if (result.rewarded) {
          void completeRecharge(result);
        } else {
          setIsWatching(false);
          setWatchProgress(0);
        }
      })
      .catch(() => {
        addToast(t('billing.power_station.recharge_error', 'Erreur lors de la recharge.'), 'error');
        setIsWatching(false);
        setWatchProgress(0);
      });
  };

  const completeRecharge = async (result: RewardedAdResult) => {
    setIsCrediting(true);
    try {
      // Le jeton signé du réseau (SSV) est transmis au backend, qui le vérifie
      // avant de créditer. En stub il est null → accepté uniquement en mode stub.
      const res = await billingService.activeRecharge(result.rewardToken ?? undefined);
      addToast(
        t('billing.power_station.energy_injected', {
          defaultValue: 'Énergie injectée : +{{earned}} Bx !',
          earned: res.earned,
        }),
        'success',
      );
      await refetchUser();
      setReloadToken((r) => r + 1);
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
                  'Gérez vos jetons Berrix (Bx) et suivez vos gains.',
                )}
              </p>
            </div>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Left Column: Berrix Wallet Card */}
            <HolographicWalletCard user={user} />

            {/* Right Column: Mining Node & Active Recharge */}
            <div className="lg:col-span-2 space-y-8">
              <h3 className="text-sm font-black uppercase tracking-[0.3em] text-gray-400 border-l-4 border-cyan-400 pl-4">
                Énergie & Récompenses
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Active Recharge */}
                <ActiveMiningCard
                  isWatching={isWatching}
                  watchProgress={watchProgress}
                  isCrediting={isCrediting}
                  isMuted={isMuted}
                  setIsMuted={setIsMuted}
                  onStartRecharge={handleRecharge}
                />

                {/* Passive Mining Node */}
                <PassiveMiningCard
                  isEnabled={isEnabled}
                  setEnabled={setEnabled}
                  timeLeft={timeLeft}
                  passiveStatus={passiveStatus}
                  totalMined={totalMined}
                />
              </div>
            </div>
          </div>

          {/* History Section (Complete Ledger with Pagination) */}
          <TransactionLedgerTable
            walletHistory={walletHistory}
            isLoadingLedger={isLoadingLedger}
            filterType={filterType}
            setFilterType={setFilterType}
            filterDirection={filterDirection}
            setFilterDirection={setFilterDirection}
            currentPage={currentPage}
            totalPages={totalPages}
            setCurrentPage={setCurrentPage}
          />
        </div>
      </div>
    </AnimatedPage>
  );
};

export default PowerStationPage;
