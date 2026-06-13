import React from 'react';
import { useReaderStore } from '../../stores/useReaderStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const TraditionalMode = () => {
  const { pages, currentPageIndex, setCurrentPageIndex } = useReaderStore();
  const currentPage = pages[currentPageIndex];

  if (!currentPage) return <div className="flex items-center justify-center h-64 text-gray-500 italic">Aucune page chargée</div>;

  return (
    <div className="flex flex-col items-center">
      <div className="relative group max-w-2xl w-full">
        <img 
          src={currentPage.url} 
          alt={`Page ${currentPage.index + 1}`} 
          className="w-full h-auto rounded-lg shadow-2xl border border-white/10"
        />
        
        {/* Navigation Overlays */}
        <button 
          onClick={() => setCurrentPageIndex(Math.max(0, currentPageIndex - 1))}
          className="absolute left-0 top-0 bottom-0 w-1/4 flex items-center justify-start pl-4 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-r from-black/40 to-transparent cursor-pointer"
        >
          <ChevronLeft className="w-12 h-12 text-white" />
        </button>
        
        <button 
          onClick={() => setCurrentPageIndex(Math.min(pages.length - 1, currentPageIndex + 1))}
          className="absolute right-0 top-0 bottom-0 w-1/4 flex items-center justify-end pr-4 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-l from-black/40 to-transparent cursor-pointer"
        >
          <ChevronRight className="w-12 h-12 text-white" />
        </button>
      </div>
      
      <div className="mt-6 flex items-center gap-4 text-xs font-bold text-gray-400">
        <span className="uppercase tracking-widest">Page {currentPageIndex + 1} / {pages.length}</span>
      </div>
    </div>
  );
};
