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
    <div className="w-full bg-[#0B0C10] bg-manga-overlay home-bg pb-24 text-[#F4F1E8]">
      <div className="w-full">
        <HeroSection />
      </div>
      <div className="max-w-[1840px] mx-auto px-6 md:px-14 pb-24 mt-12 bg-[#0B0C10] rounded-[3rem] shadow-2xl border border-[#F4F1E8]/5">
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
