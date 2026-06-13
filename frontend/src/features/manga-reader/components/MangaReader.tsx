import React from 'react';
import { useReaderStore } from '../stores/useReaderStore';

export const MangaReader: React.FC = () => {
  const { mode, setMode } = useReaderStore();
  
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
      {/* Component mode switch here will be added in Task 3 */}
    </div>
  );
};
