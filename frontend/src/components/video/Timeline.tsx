import React from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';

export const Timeline: React.FC = () => {
  const { segments, selectSegment } = useVideoRagStore();
  
  return (
    <div className="h-24 bg-black/50 border border-white/5 rounded-xl flex items-center px-4 overflow-x-auto gap-2">
      {segments.map(seg => (
        <button 
          key={seg.id}
          className={`h-16 w-32 flex-shrink-0 border rounded-md p-2 text-xs flex flex-col justify-between ${seg.type === 'emotion' ? 'bg-purple-500/30 border-purple-500/50' : 'bg-yellow-500/30 border-yellow-500/50'}`}
          onClick={() => selectSegment(seg.id)}
        >
          <span className="font-bold">{seg.type}</span>
          <span className="truncate">{seg.description}</span>
        </button>
      ))}
    </div>
  );
};
