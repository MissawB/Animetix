import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../store/authStore';
import { forgeService } from '../features/labs/services/forgeService';
import type { FusionResponse, FusionStatus } from '../features/labs/services/forgeService';
import { SearchItem } from '../types';

export const FUSION_COST = 78;

export function useForge() {
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const walletBalance = useAuthStore((s) => s.user?.wallet_balance ?? 0);

  const [itemA, setItemA] = useState<SearchItem | null>(null);
  const [itemB, setItemB] = useState<SearchItem | null>(null);
  const [chaosLevel, setChaosLevel] = useState<number>(50);
  const [balance, setBalance] = useState<number>(50);
  const [artStyle, setArtStyle] = useState<string>('Cyberpunk');
  const [styleDir, setStyleDir] = useState<number>(0);

  const [isGenerating, setIsLoading] = useState<boolean>(false);
  const [fusionData, setFusionData] = useState<FusionResponse | null>(null);
  const [status, setStatus] = useState<FusionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);

  const errLoginRequired = t(
    'games.forge.errors.login_required',
    'Connexion requise pour forger une réalité.',
  );
  const errInsufficientBx = t('games.forge.errors.insufficient_bx', {
    defaultValue: 'Berrix insuffisants — la fusion coûte {{cost}} Bx.',
    cost: FUSION_COST,
  });

  const handleStartFusion = async () => {
    if (!isAuthenticated) {
      setError(errLoginRequired);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await forgeService.startFusion({
        title_A: itemA?.title || itemA?.name,
        title_B: itemB?.title || itemB?.name,
        chaos_level: chaosLevel,
        universe_balance: balance,
        art_style: artStyle,
      });
      setFusionData(res);
    } catch (err) {
      const httpStatus = (err as { status?: number }).status;
      if (httpStatus === 401 || httpStatus === 403) {
        setError(errLoginRequired);
      } else if (httpStatus === 402) {
        setError(errInsufficientBx);
      } else {
        setError(
          t(
            'games.forge.errors.reactor_overheat',
            'Le réacteur de fusion a surchauffé. Réessayez plus tard.',
          ),
        );
      }
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (fusionData && !status?.completed) {
      interval = setInterval(async () => {
        try {
          const res = await forgeService.getFusionStatus(fusionData.task_id, fusionData.fusion_id);
          setStatus(res);
          if (res.completed) {
            setIsLoading(false);
            setShowConfetti(true);
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fusionData, status, t]);

  const resetForge = () => {
    setItemA(null);
    setItemB(null);
    setChaosLevel(50);
    setBalance(50);
    setArtStyle('Cyberpunk');
    setIsLoading(false);
    setFusionData(null);
    setStatus(null);
    setError(null);
    setShowConfetti(false);
  };

  return {
    itemA,
    setItemA,
    itemB,
    setItemB,
    chaosLevel,
    setChaosLevel,
    balance,
    setBalance,
    artStyle,
    setArtStyle,
    styleDir,
    setStyleDir,
    isGenerating,
    fusionData,
    status,
    error,
    showConfetti,
    walletBalance,
    isAuthenticated,
    handleStartFusion,
    resetForge,
  };
}
