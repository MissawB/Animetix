import React from 'react';
import { ToggleLeft, ToggleRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';

interface PassiveMiningCardProps {
  isEnabled: boolean;
  setEnabled: (val: boolean) => void;
  timeLeft: number;
  passiveStatus: string;
  totalMined: number;
}

export const PassiveMiningCard: React.FC<PassiveMiningCardProps> = ({
  isEnabled,
  setEnabled,
  timeLeft,
  passiveStatus,
  totalMined,
}) => {
  const { t } = useTranslation();

  return (
    <Card className="bg-gradient-to-br from-purple-950/20 to-black border-white/10 p-8 flex flex-col justify-between h-96 relative overflow-hidden">
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h4 className="text-xl font-black italic uppercase manga-font">Passive Mining</h4>
          <button
            onClick={() => setEnabled(!isEnabled)}
            aria-label={isEnabled ? 'Désactiver le minage passif' : 'Activer le minage passif'}
            className="focus:outline-none"
          >
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
  );
};
