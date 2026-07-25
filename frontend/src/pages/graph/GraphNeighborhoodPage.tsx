import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { GraphExplorer } from '../../features/graph/GraphExplorer';
import { SearchBar } from '../../components/SearchBar';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import type { SearchItem } from '../../types';
import { ArrowLeft, Info, Share2, Download } from 'lucide-react';

const GraphNeighborhoodPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const id = searchParams.get('id');
  const type = searchParams.get('type');

  const handleSelect = (item: SearchItem) => {
    if (item.id && item.type) {
      setSearchParams({ id: String(item.id), type: String(item.type) });
    }
  };

  return (
    <AnimatedPage>
      <div className="flex h-[calc(100vh-80px)] w-full flex-col bg-[#0B0C10] text-[#F4F1E8]">
        {!id || !type ? (
          <div className="relative flex flex-grow flex-col items-center justify-center overflow-hidden p-8">
            {/* Trame de fond */}
            <div
              className="explore-halftone pointer-events-none absolute inset-x-0 top-16 h-56"
              aria-hidden
            />

            <div className="relative z-10 text-center">
              <div className="mb-4 flex items-center justify-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  隣
                </span>
                <span className="text-[10px] font-black uppercase italic tracking-[0.3em] text-[#E8442B]">
                  Visualiseur neuronal
                </span>
              </div>
              <h1 className="font-manga mb-6 text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-7xl">
                VOISINAGE <span className="text-[#E8442B]">PROFOND</span>
              </h1>
              <p className="mx-auto mb-12 max-w-xl text-sm font-medium leading-relaxed text-[#8F94A5]">
                Explorez librement les relations complexes, les influences cachées et les connexions
                sémantiques profondes au sein du Knowledge Graph.
              </p>
              <div className="relative z-20 mx-auto w-full max-w-2xl">
                <SearchBar
                  onSelect={handleSelect}
                  placeholder="Sélectionnez un point d'origine..."
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex h-full flex-col">
            {/* Panneau de contrôle */}
            <div className="z-10 flex items-center justify-between border-b border-[#F4F1E8]/10 bg-[#0F1016] p-4">
              <div className="flex items-center gap-6">
                <button
                  onClick={() => setSearchParams({})}
                  className="group rounded-full p-2 transition-colors hover:bg-[#F4F1E8]/5"
                >
                  <ArrowLeft className="h-5 w-5 text-[#8F94A5] group-hover:text-[#F4F1E8]" />
                </button>
                <div className="hidden h-8 w-px bg-[#F4F1E8]/10 md:block" />
                <div className="flex flex-col">
                  <span className="mb-1 text-[9px] font-black uppercase leading-none tracking-widest text-[#FDB913]">
                    Origine : {type}
                  </span>
                  <span className="max-w-[200px] truncate text-sm font-bold leading-none">
                    {id}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="hidden items-center gap-2 rounded-xl border border-[#F4F1E8]/10 px-4 py-2 lg:flex">
                  <Info className="h-4 w-4 text-[#FDB913]" />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#8F94A5]">
                    Exploration neuronale illimitée
                  </span>
                </div>
                <button className="rounded-xl p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]">
                  <Share2 className="h-4 w-4" />
                </button>
                <button className="rounded-xl p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]">
                  <Download className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Vue principale du graphe */}
            <div className="relative z-0 flex-grow">
              <GraphExplorer initialId={id} initialType={type} />
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default GraphNeighborhoodPage;
