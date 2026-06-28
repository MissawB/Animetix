import React from 'react';
import { HeroSection } from './features/home/components/HeroSection';
import { SoloChallenges } from './features/home/components/SoloChallenges';
import { WorldBossBanner } from './features/home/components/WorldBossBanner';
import { MultiplayerModes } from './features/home/components/MultiplayerModes';
import { CreativeForge } from './features/home/components/CreativeForge';
import { SingularityLab } from './features/home/components/SingularityLab';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="w-full bg-transparent transition-colors duration-500 bg-manga-overlay home-bg pb-24">
        <div className="hero-bg w-full transition-all duration-500 shadow-sm border-b border-gray-100/10 dark:border-navy-950/10">
          <HeroSection />
        </div>
        <div className="max-w-[1840px] mx-auto px-6 md:px-14 pb-24 mt-12 bg-[#fffcf0] dark:bg-[#1a1a2e] rounded-[3rem] shadow-2xl border border-gray-100 dark:border-white/5 transition-colors duration-500">
          <SoloChallenges />
          <WorldBossBanner />
          <MultiplayerModes />
          <CreativeForge />
          <SingularityLab />
        </div>
    </div>
  );
}

export default App;