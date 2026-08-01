import React from 'react';
import { Play, Volume2, VolumeX, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

interface ActiveMiningCardProps {
  isWatching: boolean;
  watchProgress: number;
  isCrediting: boolean;
  isMuted: boolean;
  setIsMuted: (val: boolean) => void;
  onStartRecharge: () => void;
}

export const ActiveMiningCard: React.FC<ActiveMiningCardProps> = ({
  isWatching,
  watchProgress,
  isCrediting,
  isMuted,
  setIsMuted,
  onStartRecharge,
}) => {
  const { t } = useTranslation();

  return (
    <Card className="bg-gradient-to-br from-cyan-950/20 to-black border-white/10 p-8 flex flex-col justify-between h-96 relative overflow-hidden">
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h4 className="text-xl font-black italic uppercase manga-font">Active Mining</h4>
          <span className="text-[9px] font-black uppercase text-cyan-400 tracking-wider px-2 py-0.5 bg-cyan-500/10 rounded-full border border-cyan-500/20">
            +250 Bx
          </span>
        </div>
        <p className="text-xs text-gray-400 font-bold uppercase tracking-wide">
          {t(
            'billing.power_station.active_desc',
            "Lancez une recharge d'énergie pour créditer votre portefeuille.",
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
                aria-label={isMuted ? 'Activer le son' : 'Couper le son'}
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
            </div>
            <div className="w-full max-w-xs h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(6,182,212,1)]"
                style={{ width: `${watchProgress}%` }}
              />
            </div>
            <p className="text-[8px] text-gray-500 uppercase tracking-widest">
              {t('billing.power_station.dont_close_console', 'Ne fermez pas la console')}
            </p>
          </div>
        ) : (
          <>
            <Button
              aria-label="Lancer la recharge"
              className="rounded-full w-16 h-16 bg-cyan-500 hover:bg-cyan-400 text-black flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.3)] transition-all hover:scale-105"
              onClick={onStartRecharge}
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
  );
};
