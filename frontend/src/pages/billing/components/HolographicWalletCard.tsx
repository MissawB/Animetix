import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { User } from '../../../types';

interface HolographicWalletCardProps {
  user: User | null;
}

export const HolographicWalletCard: React.FC<HolographicWalletCardProps> = ({ user }) => {
  const { t } = useTranslation();

  return (
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
            {user?.wallet_balance?.toLocaleString() || 0} <span className="text-cyan-400">Bx</span>
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
  );
};
