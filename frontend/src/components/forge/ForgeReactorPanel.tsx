import React from 'react';
import { useTranslation } from 'react-i18next';
import { Zap, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { CyberSlider } from './CyberSlider';
import { CyberButton } from './CyberButton';
import { SearchItem } from '../../types';

interface ForgeReactorPanelProps {
  itemA: SearchItem | null;
  itemB: SearchItem | null;
  chaosLevel: number;
  setChaosLevel: (val: number) => void;
  balance: number;
  setBalance: (val: number) => void;
  isGenerating: boolean;
  walletBalance: number;
  isAuthenticated: boolean;
  error: string | null;
  handleStartFusion: () => void;
  fusionCost: number;
}

export const ForgeReactorPanel: React.FC<ForgeReactorPanelProps> = ({
  itemA,
  itemB,
  chaosLevel,
  setChaosLevel,
  balance,
  setBalance,
  isGenerating,
  walletBalance,
  isAuthenticated,
  error,
  handleStartFusion,
  fusionCost,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const errLoginRequired = t(
    'games.forge.errors.login_required',
    'Connexion requise pour forger une réalité.',
  );
  const errInsufficientBx = t('games.forge.errors.insufficient_bx', {
    defaultValue: 'Berrix insuffisants — la fusion coûte {{cost}} Bx.',
    cost: fusionCost,
  });

  return (
    <div className="space-y-12">
      <div>
        <div className="flex justify-between items-end mb-4">
          <div className="space-y-1">
            <span className="text-xs font-black uppercase tracking-widest text-red-500">
              {t('games.forge.chaos_level', 'Niveau de Chaos')}
            </span>
            <p className="text-[10px] font-bold opacity-55 max-w-[180px]">
              {t('games.forge.chaos_desc', "Définit le degré d'imprévisibilité de la fusion.")}
            </p>
          </div>
          <span className="text-2xl font-black italic manga-font text-red-500">{chaosLevel}%</span>
        </div>
        <div className="relative group pt-4">
          <CyberSlider
            min={0}
            max={100}
            value={chaosLevel}
            onChange={setChaosLevel}
            color="magenta"
          />
          <div className="flex justify-between mt-3 text-[9px] font-black uppercase opacity-45">
            <span>{t('games.forge.chaos_scale_low', 'Cohérent')}</span>
            <span>{t('games.forge.chaos_scale_mid', 'Distordu')}</span>
            <span>{t('games.forge.chaos_scale_high', 'Entropie')}</span>
          </div>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-end mb-4">
          <div className="space-y-1">
            <span className="text-xs font-black uppercase tracking-widest text-blue-500">
              {t('games.forge.dna_balance', 'Équilibre des ADN')}
            </span>
            <p className="text-[10px] font-bold opacity-55 max-w-[180px]">
              {t(
                'games.forge.dna_balance_desc',
                'Quel univers doit dominer la structure globale ?',
              )}
            </p>
          </div>
          <span className="text-2xl font-black italic manga-font text-blue-500">{balance}%</span>
        </div>
        <div className="relative group pt-4">
          <CyberSlider min={0} max={100} value={balance} onChange={setBalance} color="cyan" />
          <div className="flex justify-between mt-3 text-[9px] font-black uppercase opacity-45">
            <span>{t('games.forge.balance_scale_a', 'Origine A')}</span>
            <span>{t('games.forge.balance_scale_mid', 'Hybride')}</span>
            <span>{t('games.forge.balance_scale_b', 'Origine B')}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between px-2">
          <span className="text-[11px] font-black uppercase tracking-widest opacity-50">
            {t('games.forge.fusion_cost', 'Coût de la fusion')}
          </span>
          <span className="flex items-center gap-1.5 text-sm font-black text-yellow-400">
            <Zap className="w-4 h-4" /> {fusionCost} Bx
          </span>
        </div>

        <CyberButton
          onClick={() => {
            if (!itemA || !itemB || isGenerating) return;
            handleStartFusion();
          }}
          className={`w-full py-8 rounded-[2.5rem] font-black italic text-3xl shadow-2xl transition-all duration-300 flex items-center justify-center gap-4 uppercase ${
            !itemA || !itemB || isGenerating ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <Sparkles className="w-8 h-8" />
          {t('games.forge.forge_button', 'Forger la Réalité')}
        </CyberButton>

        {isAuthenticated ? (
          <p className="text-center text-[10px] font-black uppercase tracking-widest opacity-40">
            {t('games.forge.balance_label', 'Solde :')}{' '}
            <span className={walletBalance < fusionCost ? 'text-red-500' : 'text-yellow-400'}>
              {walletBalance} Bx
            </span>
          </p>
        ) : (
          <p className="text-center text-[10px] font-black uppercase tracking-widest opacity-50">
            {t('games.forge.login_hint', 'Connexion requise — chaque fusion consomme des Berrix.')}
          </p>
        )}

        {error && (
          <div className="text-red-500 text-center text-xs font-black uppercase bg-red-500/10 p-4 rounded-2xl space-y-3">
            <p>{error}</p>
            {error === errLoginRequired && (
              <button
                onClick={() => navigate('/auth/login/')}
                className="underline hover:text-red-400"
              >
                {t('games.forge.login_button', 'Se connecter')}
              </button>
            )}
            {error === errInsufficientBx && (
              <button
                onClick={() => navigate('/power-station/')}
                className="underline hover:text-red-400"
              >
                {t('games.forge.recharge_button', 'Recharger des Berrix')}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
