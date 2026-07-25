import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GraphExplorer } from '../../features/graph/GraphExplorer';
import { SearchBar } from '../../components/SearchBar';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import type { SearchItem } from '../../types';

import { Zap } from 'lucide-react';

const GraphPage: React.FC = () => {
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
          <div className="relative flex flex-grow flex-col items-center justify-center p-8">
            <div
              className="explore-halftone pointer-events-none absolute inset-x-0 top-10 h-48"
              aria-hidden
            />
            <div className="relative mb-6 flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                網
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                Cartographie du graphe · Neo4j
              </span>
            </div>
            <h1 className="font-manga mb-4 text-center text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
              EXPLORER LES <span className="text-[#E8442B]">CONNEXIONS</span>
            </h1>
            <p className="mb-12 max-w-lg text-center text-sm leading-relaxed text-[#8F94A5]">
              Cherchez un anime, un personnage, un jeu ou un film pour commencer à explorer son
              univers de relations dans le graphe.
            </p>
            <div className="relative z-20 w-full max-w-2xl">
              <SearchBar onSelect={handleSelect} placeholder="Rechercher une œuvre..." />
            </div>

            <Link
              to="/graph/neighborhood/"
              className="group mt-8 flex items-center gap-2 rounded-xl border border-[#F4F1E8]/15 px-6 py-3 no-underline transition-colors hover:border-[#FDB913]"
            >
              <Zap className="h-4 w-4 text-[#FDB913] transition-transform group-hover:scale-110" />
              <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors group-hover:text-[#F4F1E8]">
                Activer l'Explorateur de Voisinage Profond
              </span>
            </Link>
          </div>
        ) : (
          <div className="flex h-full flex-col">
            <div className="z-10 flex items-center justify-between border-b border-[#F4F1E8]/10 bg-[#0F1016] p-4">
              <button
                onClick={() => setSearchParams({})}
                className="rounded-full border border-[#F4F1E8]/15 px-6 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
              >
                Retour à la recherche
              </button>
            </div>
            <div className="relative z-0 flex-grow">
              <GraphExplorer initialId={id} initialType={type} />
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default GraphPage;
