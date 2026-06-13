import React from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { Play, MessageSquare, Heart, Sparkles } from 'lucide-react';

export const Timeline: React.FC = () => {
  const { segments, selectedSegmentId, selectSegment } = useVideoRagStore();
  
  if (!segments || segments.length === 0) {
    return (
      <div className="h-32 bg-black/30 border border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center p-6 text-center animate-pulse">
        <Sparkles className="w-6 h-6 text-white/20 mb-2" />
        <p className="text-xs font-bold text-white/50 uppercase tracking-widest">Aucun segment chargé</p>
        <p className="text-[10px] text-white/30 mt-1 max-w-md">
          Saisissez des mots-clés dans l'explorateur sémantique ou utilisez les suggestions pour localiser les scènes.
        </p>
      </div>
    );
  }

  // Helper function to return icon based on type
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'emotion':
        return <Heart className="w-3.5 h-3.5 text-purple-400" />;
      case 'dialogue':
        return <MessageSquare className="w-3.5 h-3.5 text-blue-400" />;
      default:
        return <Play className="w-3.5 h-3.5 text-yellow-400" />;
    }
  };

  // Helper to return border & bg colors for segments
  const getTypeColors = (type: string, isSelected: boolean) => {
    if (isSelected) {
      return 'border-red-500 bg-red-950/40 shadow-[0_0_15px_rgba(239,68,68,0.25)] ring-2 ring-red-500/20';
    }
    switch (type) {
      case 'emotion':
        return 'bg-purple-950/20 border-purple-500/30 text-purple-300 hover:border-purple-500/60 hover:bg-purple-950/30';
      case 'dialogue':
        return 'bg-blue-950/20 border-blue-500/30 text-blue-300 hover:border-blue-500/60 hover:bg-blue-950/30';
      default:
        return 'bg-yellow-950/20 border-yellow-500/30 text-yellow-300 hover:border-yellow-500/60 hover:bg-yellow-950/30';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center text-[10px] font-black text-white/40 uppercase tracking-widest px-1">
        <span>Séquence Chronologique</span>
        <span>{segments.length} segment{segments.length > 1 ? 's' : ''} trouvé{segments.length > 1 ? 's' : ''}</span>
      </div>
      <div className="h-32 bg-black/60 border border-white/5 rounded-2xl flex items-center px-4 overflow-x-auto gap-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent py-2">
        {segments.map((seg, index) => {
          const isSelected = seg.id === selectedSegmentId;
          return (
            <button 
              key={seg.id}
              className={`h-24 w-44 flex-shrink-0 border rounded-xl p-3 text-xs flex flex-col justify-between text-left transition-all duration-300 hover:scale-102 cursor-pointer ${getTypeColors(seg.type, isSelected)}`}
              onClick={() => selectSegment(seg.id)}
            >
              <div className="flex justify-between items-center w-full">
                <span className="text-[10px] font-bold text-white/50 tracking-wider">#{index + 1}</span>
                <span className="text-[10px] font-black tracking-widest bg-black/40 px-2 py-0.5 rounded border border-white/5">
                  {seg.start}s - {seg.end === -1 ? 'Fin' : `${seg.end}s`}
                </span>
              </div>
              
              <p className="text-[11px] font-semibold text-white/80 line-clamp-2 leading-relaxed my-1.5 flex-grow">
                {seg.description}
              </p>

              <div className="flex items-center gap-1.5 mt-1">
                {getTypeIcon(seg.type)}
                <span className="text-[9px] font-black uppercase tracking-wider opacity-60">
                  {seg.type}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
