import React from 'react';
import { useReaderStore } from '../stores/useReaderStore';
import { WebtoonMode } from './modes/WebtoonMode';
import { TraditionalMode } from './modes/TraditionalMode';
import { InteractiveMode } from './modes/InteractiveMode';

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

  return (
    <div className="w-full h-full">
      <div className="flex gap-2 mb-4">
        {['webtoon', 'traditional', 'interactive'].map((m) => (
          <button 
            key={m} 
            onClick={() => setMode(m as any)}
            className={mode === m ? 'bg-anime-accent' : 'bg-gray-800'}
          >
            {m}
          </button>
        ))}
      </div>
      {renderMode()}
    </div>
  );
};
