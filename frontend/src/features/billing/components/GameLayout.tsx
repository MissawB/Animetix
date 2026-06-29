import React, { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { PassiveAdMiner } from '../components/PassiveAdMiner';
import { AdSlot } from '../components/AdSlot';

const GAME_AD_SLOT = import.meta.env.VITE_ADSENSE_SLOT_GAME as string | undefined;

const GameLayout: React.FC = () => {
  return (
    <>
      <PassiveAdMiner />
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-[#fffcf0] dark:bg-[#0f0f1a]"><div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" /></div>}>
        <Outlet />
      </Suspense>
      {/* Bannière publicitaire des jeux, épinglée en bas — finance le minage
          passif de Bx tant qu'elle reste visible. */}
      <div className="sticky bottom-0 z-30 pointer-events-none">
        <div className="mx-auto w-full max-w-3xl px-4 pb-3 pointer-events-auto">
          <div className="rounded-2xl border border-white/10 bg-black/70 shadow-2xl backdrop-blur-md">
            <AdSlot slot={GAME_AD_SLOT} className="w-full" label="Publicité — finance ton minage" />
          </div>
        </div>
      </div>
    </>
  );
};

export default GameLayout;
