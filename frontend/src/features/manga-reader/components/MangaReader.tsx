import React from 'react';
import { useReaderStore } from '../stores/useReaderStore';
import { WebtoonMode } from './modes/WebtoonMode';
import { TraditionalMode } from './modes/TraditionalMode';
import { InteractiveMode } from './modes/InteractiveMode';
import { Layout, Scroll, Sparkles } from 'lucide-react';

export const MangaReader: React.FC = () => {
  const { mode, setMode } = useReaderStore();
  
  const renderMode = () => {
    switch (mode) {
      case 'webtoon': return <WebtoonMode />;
      case 'traditional': return <TraditionalMode />;
      case 'interactive': return <InteractiveMode />;
      default: return null;
    }
  };

  const modeIcons = {
    webtoon: <Scroll className="w-4 h-4" />,
    traditional: <Layout className="w-4 h-4" />,
    interactive: <Sparkles className="w-4 h-4" />
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-center mb-12">
        <div className="bg-navy-900/80 backdrop-blur-md p-1.5 rounded-2xl flex gap-1 border border-white/10">
          {(['traditional', 'webtoon', 'interactive'] as const).map((m) => (
            <button 
              key={m} 
              onClick={() => setMode(m)}
              className={`px-6 py-2.5 rounded-xl flex items-center gap-2 text-xs font-black uppercase tracking-widest transition-all ${
                mode === m 
                ? 'bg-anime-accent text-white shadow-lg' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {modeIcons[m]}
              {m}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {renderMode()}
      </div>
    </div>
  );
};
