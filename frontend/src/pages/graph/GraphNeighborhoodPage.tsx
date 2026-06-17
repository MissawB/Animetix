import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { GraphExplorer } from "../../features/graph/GraphExplorer";
import { SearchBar } from "../../components/SearchBar";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { ArrowLeft, Info, Share2, Download, Zap } from 'lucide-react';

const GraphNeighborhoodPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const id = searchParams.get('id');
  const type = searchParams.get('type');
  
  const handleSelect = (item: Record<string, unknown>) => {
    if (item.id && item.type) {
      setSearchParams({ id: item.id.toString(), type: item.type });
    }
  };

  return (
    <AnimatedPage>
      <div className="flex flex-col w-full h-[calc(100vh-80px)] bg-[#05050a] text-white">
        {!id || !type ? (
          <div className="flex flex-col items-center justify-center flex-grow p-8 relative overflow-hidden">
             {/* Background accents */}
             <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px] animate-pulse" />
             <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] animate-pulse delay-700" />

             <div className="relative z-10 text-center">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <Zap className="w-6 h-6 text-blue-500" />
                  <span className="text-blue-500 font-black italic tracking-widest text-[10px] uppercase">Neural Visualizer</span>
                </div>
                <h1 className="text-6xl md:text-7xl font-black italic tracking-tighter mb-6 text-white uppercase manga-font">
                  DEEP <span className="text-blue-500">NEIGHBORHOOD</span>
                </h1>
                <p className="text-gray-400 mb-12 max-w-xl mx-auto uppercase tracking-[0.2em] text-[10px] font-bold leading-relaxed">
                  Explorez librement les relations complexes, les influences cachées et les connexions sémantiques profondes au sein du Knowledge Graph.
                </p>
                <div className="w-full max-w-2xl mx-auto shadow-2xl shadow-blue-500/5 relative z-20">
                  <SearchBar 
                    onSelect={handleSelect} 
                    placeholder="Sélectionnez un point d'origine..." 
                  />
                </div>
             </div>
          </div>
        ) : (
          <div className="flex flex-col h-full">
            {/* Header Control Panel */}
            <div className="p-4 bg-black/40 backdrop-blur-md flex items-center justify-between z-10 border-b border-white/5">
              <div className="flex items-center gap-6">
                <button 
                  onClick={() => setSearchParams({})}
                  className="p-2 hover:bg-white/5 rounded-full transition-colors group"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-white" />
                </button>
                <div className="hidden md:block h-8 w-[1px] bg-white/10" />
                <div className="flex flex-col">
                  <span className="text-[9px] font-black text-blue-500 uppercase tracking-widest leading-none mb-1">Origine: {type}</span>
                  <span className="text-sm font-bold truncate max-w-[200px] leading-none">{id}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="hidden lg:flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl border border-white/10">
                  <Info className="w-4 h-4 text-blue-400" />
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Exploration neuronale illimitée</span>
                </div>
                <button className="p-2 hover:bg-white/5 rounded-xl transition-colors text-gray-400 hover:text-white">
                  <Share2 className="w-4 h-4" />
                </button>
                <button className="p-2 hover:bg-white/5 rounded-xl transition-colors text-gray-400 hover:text-white">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Main Graph View */}
            <div className="flex-grow relative z-0">
              <GraphExplorer initialId={id} initialType={type} hideHeader maxDepth={5} />
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default GraphNeighborhoodPage;
