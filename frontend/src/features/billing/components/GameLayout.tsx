import React, { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { PassiveAdMiner } from '../components/PassiveAdMiner';

const GameLayout: React.FC = () => {
  return (
    <>
      <PassiveAdMiner />
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-[#fffcf0] dark:bg-[#0f0f1a]"><div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" /></div>}>
        <Outlet />
      </Suspense>
    </>
  );
};

export default GameLayout;
