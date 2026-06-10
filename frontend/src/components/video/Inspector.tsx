import React from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { Heart, Download } from 'lucide-react';

export const Inspector: React.FC = () => {
  const { selectedSegmentId, segments, toggleFavorite, favorites } = useVideoRagStore();
  const segment = segments.find(s => s.id === selectedSegmentId);

  if (!segment) return <div className="p-4 opacity-50 text-sm">Sélectionnez un segment</div>;

  return (
    <div className="p-6 bg-black/40 border border-white/10 rounded-xl mt-4">
      <h3 className="font-bold text-lg mb-2">Inspecteur de Segment</h3>
      <p className="text-gray-300">{segment.description}</p>
      <div className="flex gap-4 mt-6">
        <button 
          onClick={() => toggleFavorite(segment.id)}
          className={`p-2 rounded-full ${favorites.includes(segment.id) ? 'text-red-500' : 'text-white'}`}
        >
          <Heart fill={favorites.includes(segment.id) ? 'currentColor' : 'none'} />
        </button>
        <button 
          onClick={() => console.log('Export', segment.id)}
          className="p-2 text-white hover:text-blue-400"
        >
          <Download />
        </button>
      </div>
    </div>
  );
};
