import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { GraphExplorer } from './GraphExplorer';
import { SearchBar } from '../../components/SearchBar';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const GraphPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const id = searchParams.get('id');
  const type = searchParams.get('type');

  const handleSelect = (item: any) => {
    if (item.id && item.type) {
      setSearchParams({ id: item.id.toString(), type: item.type });
    }
  };

  return (
    <AnimatedPage>
      <div className="flex flex-col w-full h-[calc(100vh-80px)] bg-black text-white">
        {!id || !type ? (
          <div className="flex flex-col items-center justify-center flex-grow p-8">
            <h1 className="text-5xl font-black italic tracking-tighter mb-4 text-center">
              EXPLORE CONNECTIONS
            </h1>
            <p className="text-gray-400 mb-12 text-center max-w-lg uppercase tracking-widest text-xs">
              Search for an Anime, Character, Game, or Movie to start exploring the localized graph universe.
            </p>
            <div className="w-full max-w-2xl relative z-20">
              <SearchBar 
                onSelect={handleSelect} 
                placeholder="Search media..." 
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-full">
            <div className="p-4 bg-navy-950 flex items-center justify-between z-10 border-b border-white/10">
              <button 
                onClick={() => setSearchParams({})}
                className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-full text-white font-bold uppercase tracking-widest text-xs transition-colors"
              >
                Back to Search
              </button>
            </div>
            <div className="flex-grow relative z-0">
              <GraphExplorer initialId={id} initialType={type} />
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default GraphPage;
