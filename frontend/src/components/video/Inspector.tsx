import React, { useState } from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { Heart, Download, Video, Info, Calendar, Sparkles } from 'lucide-react';
import { Badge } from '../../components/ui/Badge';

export const Inspector: React.FC = () => {
  const { selectedSegmentId, segments, toggleFavorite, favorites } = useVideoRagStore();
  const segment = segments.find(s => s.id === selectedSegmentId);

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  if (!segment) {
    return (
      <div className="p-8 bg-black/20 border border-white/5 rounded-2xl flex flex-col items-center justify-center text-center text-white/30 h-44">
        <Info className="w-8 h-8 opacity-30 mb-3" />
        <p className="text-xs font-bold uppercase tracking-wider">Inspecteur de Segment</p>
        <p className="text-[10px] opacity-70 mt-1 max-w-sm">
          Sélectionnez n'importe quel segment sur la timeline ci-dessus pour inspecter son récit, gérer sa mise en favori et l'exporter.
        </p>
      </div>
    );
  }

  const handleExport = () => {
    if (isExporting) return;
    setIsExporting(true);
    setExportProgress(0);
    
    const interval = setInterval(() => {
      setExportProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setIsExporting(false);
          }, 1000);
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  const isFavorited = favorites.includes(segment.id);

  return (
    <div className="p-6 bg-[#0e0e1a] border border-white/10 rounded-2xl relative overflow-hidden transition-all duration-300 shadow-xl">
      {/* Dynamic light background effect */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 blur-3xl rounded-full" />
      
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 relative z-10">
        
        {/* Left Side Info */}
        <div className="space-y-4 flex-grow">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-black italic tracking-wider text-red-500 uppercase flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-red-400" /> Inspecteur
            </span>
            
            <div className="flex gap-2">
              <Badge variant="neutral" className="bg-white/5 border border-white/10 text-white/80 text-[9px] uppercase px-2">
                ID: {segment.id}
              </Badge>
              <Badge variant="neutral" className="bg-red-500/10 border border-red-500/20 text-red-400 text-[9px] uppercase px-2 font-black">
                {segment.type}
              </Badge>
              {segment.video_id && (
                <Badge variant="neutral" className="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[9px] uppercase px-2 flex items-center gap-1">
                  <Video className="w-2.5 h-2.5" /> {segment.video_id}
                </Badge>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xs font-black uppercase text-white/40 tracking-widest flex items-center gap-1.5">
              Description Sémantique du Segment
            </h3>
            <p className="text-white/80 text-sm leading-relaxed font-medium bg-black/40 border border-white/5 p-4 rounded-xl">
              {segment.description}
            </p>
          </div>

          <div className="flex items-center gap-6 text-xs text-white/40">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4 opacity-50" />
              <span>Horodatage : <strong className="text-white/70">{segment.start}s - {segment.end === -1 ? 'Fin' : `${segment.end}s`}</strong></span>
            </div>
            {segment.end !== -1 && (
              <div>
                Durée : <strong className="text-white/70">{segment.end - segment.start} secondes</strong>
              </div>
            )}
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex flex-row md:flex-col items-center gap-3 w-full md:w-auto flex-shrink-0">
          <button 
            onClick={() => toggleFavorite(segment.id)}
            className={`w-full md:w-40 px-4 py-3 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition-all cursor-pointer ${
              isFavorited 
                ? 'bg-red-600/10 border-red-500 text-red-400 hover:bg-red-600/20' 
                : 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white'
            }`}
          >
            <Heart className="w-4 h-4" fill={isFavorited ? 'currentColor' : 'none'} />
            {isFavorited ? 'Favorisé' : 'Mettre en Favori'}
          </button>
          
          <button 
            onClick={handleExport}
            disabled={isExporting}
            className={`w-full md:w-40 px-4 py-3 rounded-xl flex items-center justify-center gap-2 text-xs font-bold transition-all border-none text-white cursor-pointer ${
              isExporting 
                ? 'bg-white/5 text-white/40' 
                : 'bg-red-600 hover:bg-red-700 hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            <Download className="w-4 h-4" />
            {isExporting ? 'Exportation...' : 'Exporter Extrait'}
          </button>
        </div>
      </div>

      {/* Export progress overlay */}
      {isExporting && (
        <div className="absolute inset-0 bg-[#0e0e1a]/95 backdrop-blur-sm z-20 flex flex-col justify-center items-center px-12 animate-fade-in">
          <div className="w-full max-w-md space-y-3">
            <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-red-400">
              <span>Exportation du segment en cours...</span>
              <span>{exportProgress}%</span>
            </div>
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
              <div 
                className="h-full bg-red-600 rounded-full transition-all duration-150"
                style={{ width: `${exportProgress}%` }}
              />
            </div>
            <p className="text-[10px] text-white/30 text-center uppercase tracking-widest animate-pulse mt-2">
              Extraction du clip vidéo & génération des métadonnées temporelles
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
