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
    <div className="w-full bg-[#0B0C10] text-[#F4F1E8] transition-colors duration-500 pb-24">
      <div className="w-full border-b border-[#F4F1E8]/10">
        <HeroSection />
      </div>
      <div className="max-w-[1840px] mx-auto px-6 md:px-14 pb-24 mt-12">
        <SoloChallenges />
        <WorldBossBanner />
        <MultiplayerModes />
        <CreativeForge />
        <SingularityLab />
      </div>
    </div>
  );
};

export default App;
