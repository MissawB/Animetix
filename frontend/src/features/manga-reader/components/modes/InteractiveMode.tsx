import React from 'react';
import { useReaderStore } from '../../stores/useReaderStore';
import { Sparkles, Languages, Volume2 } from 'lucide-react';

export const InteractiveMode = () => {
  const { pages, currentPageIndex } = useReaderStore();
  const currentPage = pages[currentPageIndex];

  if (!currentPage) return <div className="flex items-center justify-center h-64 text-gray-500 italic">Aucune page chargée</div>;

  return (
    <div className="flex flex-col items-center">
      <div className="relative max-w-2xl w-full">
        <img 
          src={currentPage.url} 
          alt={`Interactive Page ${currentPage.index + 1}`} 
          className="w-full h-auto rounded-lg shadow-2xl border-4 border-anime-accent/30"
        />
        
        {/* Interactive Overlays (Mock) */}
        <div className="absolute top-10 left-10 p-2 bg-anime-accent text-white rounded-full shadow-lg animate-pulse">
           <Sparkles className="w-5 h-5" />
        </div>

        <div className="absolute bottom-20 right-10 flex flex-col gap-3">
            <button className="p-3 bg-black/80 text-white rounded-xl border border-white/20 hover:bg-anime-accent transition-colors">
                <Languages className="w-5 h-5" />
            </button>
            <button className="p-3 bg-black/80 text-white rounded-xl border border-white/20 hover:bg-anime-accent transition-colors">
                <Volume2 className="w-5 h-5" />
            </button>
        </div>
      </div>
      
      <div className="mt-8 p-6 bg-navy-900/50 rounded-2xl border border-white/5 max-w-2xl w-full text-center">
        <p className="text-sm text-gray-400 italic">
          Le mode interactif utilise l'IA pour segmenter les cases et extraire les dialogues en temps réel. 
          Cliquez sur les zones en surbrillance pour interagir.
        </p>
      </div>
    </div>
  );
};
