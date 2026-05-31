import React from 'react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const WorldBossPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16 text-white">
        <h1 className="text-5xl font-black italic uppercase text-center text-red-500 mb-8">
          WORLD BOSS
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 bg-gray-900 min-h-[500px] rounded-xl border border-red-900/50">
                {/* Main Raid Area Placeholder */}
            </div>
            <div className="bg-gray-900 min-h-[500px] rounded-xl border border-gray-800">
                {/* Sidebar Placeholder */}
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default WorldBossPage;
