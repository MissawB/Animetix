import React from 'react';
import { Globe, Layers, Zap, Database, Search, Maximize2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { motion } from 'framer-motion';

interface LoreCommunity {
  id: string | number;
  name: string;
  summary: string;
  entities?: string[];
}

// The endpoint answers with EITHER the community list OR, while the map is being
// (re)built behind its anti-stampede lock, a 202 `{status: "generating"}`. Both are
// 2xx, so apiClient hands them through as data — the page must discriminate. It used
// to assume an array and crashed the error boundary with "e?.map is not a function".
type WorldMapResponse = LoreCommunity[] | { status?: string };

const isGenerating = (data: WorldMapResponse | undefined): boolean =>
  !!data && !Array.isArray(data) && (data as { status?: string }).status === 'generating';

const LoreWorldMapPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery<WorldMapResponse>({
    queryKey: ['graph-world-map'],
    queryFn: () => apiClient('/api/v1/graph/world-map/'),
    // While the backend reports "generating", poll until the map lands.
    refetchInterval: (query) => (isGenerating(query.state.data) ? 5000 : false),
  });

  // Anything that is not a list of communities renders as "no communities yet"
  // rather than throwing (a malformed payload must not take the page down).
  const communities: LoreCommunity[] = Array.isArray(data) ? data : [];
  const generating = isGenerating(data);

  if (isLoading)
    return (
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError)
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <h2 className="text-3xl font-black text-red-500 italic uppercase">
          Erreur de Cartographie
        </h2>
        <p className="text-white/40 mt-4 uppercase font-bold tracking-widest">
          Impossible de charger les données macro-conceptuelles.
        </p>
      </div>
    );

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header Atlas */}
        <header className="mb-16 relative">
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 blur-[120px] rounded-full -z-10" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-gray-500 mb-4">
            <Globe className="w-3 h-3" /> Macro-Sémantique Division
          </div>
          <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
            LORE <span className="text-emerald-500 text-glow">WORLD MAP</span>
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
            Visualisation macroscopique des clusters de lore détectés par l'algorithme de Leiden.
          </p>
        </header>

        {/* Navigation / Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Sidebar : Community Stats */}
          <div className="lg:col-span-4 space-y-8">
            <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl">
              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-500" /> État du Graphe
              </h3>
              <div className="space-y-6">
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-[10px] font-black uppercase opacity-30">Communautés</span>
                  <span className="text-2xl font-black italic text-emerald-500">
                    {communities.length}
                  </span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-[10px] font-black uppercase opacity-30">Algorithme</span>
                  <span className="text-xs font-black italic">LEIDEN / LOUVAIN</span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-[10px] font-black uppercase opacity-30">Profondeur</span>
                  <span className="text-xs font-black italic">MACRO-THEMATIC</span>
                </div>
              </div>

              <div className="mt-10 p-6 bg-emerald-500/5 rounded-3xl border border-emerald-500/10">
                <p className="text-[9px] font-bold leading-relaxed opacity-40 uppercase italic">
                  Le partitionnement regroupe les œuvres non pas par titre, mais par densité de
                  relations (thèmes communs, auteurs, studios, inspirations).
                </p>
              </div>
            </Card>

            <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
              <h4 className="text-[10px] font-black uppercase tracking-widest mb-4">
                Légende Dynamique
              </h4>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                  <span className="text-[10px] font-bold uppercase opacity-60">
                    Forte Cohérence
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                  <span className="text-[10px] font-bold uppercase opacity-60">
                    Inter-connectivité
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                  <span className="text-[10px] font-bold uppercase opacity-60">
                    Zone Expérimentale
                  </span>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content : Cluster Cards */}
          <div className="lg:col-span-8 space-y-12">
            {generating && (
              <Card
                padding="lg"
                className="bg-white/5 border-emerald-500/20 rounded-[3rem] text-center"
              >
                <h4 className="text-2xl font-black italic manga-font uppercase mb-2 text-emerald-500">
                  Cartographie en cours
                </h4>
                <p className="text-xs font-bold opacity-50 uppercase tracking-wide leading-relaxed">
                  Le partitionnement du graphe est en cours de génération. Cette page se rafraîchira
                  automatiquement dès que les clusters seront disponibles.
                </p>
              </Card>
            )}
            {!generating && communities.length === 0 && (
              <Card padding="lg" className="bg-white/5 border-white/10 rounded-[3rem] text-center">
                <h4 className="text-2xl font-black italic manga-font uppercase mb-2 opacity-60">
                  Aucune communauté
                </h4>
                <p className="text-xs font-bold opacity-40 uppercase tracking-wide">
                  Le graphe n'a pas encore produit de clusters macro-conceptuels.
                </p>
              </Card>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {communities.map((community, idx) => (
                <motion.div
                  key={community.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <Card
                    padding="none"
                    className="group overflow-hidden bg-black border-white/10 hover:border-emerald-500/40 transition-all duration-500 rounded-[2.5rem] h-full flex flex-col relative"
                  >
                    {/* Visual Accent */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[50px] -mr-16 -mt-16 group-hover:bg-emerald-500/20 transition-all" />

                    <div className="p-8 space-y-6 flex-grow">
                      <div className="flex justify-between items-start">
                        <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-emerald-500 group-hover:scale-110 transition-transform">
                          <Layers className="w-6 h-6" />
                        </div>
                        <Badge
                          variant="primary"
                          className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px] font-black uppercase"
                        >
                          CLUSTER_{idx + 1}
                        </Badge>
                      </div>

                      <div>
                        <h3 className="text-2xl font-black italic manga-font uppercase mb-3 tracking-tighter group-hover:text-emerald-400 transition-colors">
                          {community.name}
                        </h3>
                        <p className="text-xs font-bold leading-relaxed opacity-60 uppercase italic line-clamp-4">
                          {community.summary}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {community.entities?.slice(0, 3).map((entity: string) => (
                          <span
                            key={entity}
                            className="text-[8px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 border border-white/5 rounded-full opacity-40"
                          >
                            {entity}
                          </span>
                        ))}
                        {community.entities && community.entities.length > 3 && (
                          <span className="text-[8px] font-black uppercase opacity-20 py-1">
                            +{community.entities.length - 3} PLUS
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="p-6 bg-white/5 border-t border-white/5 flex justify-between items-center">
                      <button className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-emerald-500 hover:text-emerald-400 transition-colors">
                        Explorer la zone <Maximize2 className="w-3 h-3" />
                      </button>
                      <div className="flex items-center gap-1 opacity-20">
                        <Zap className="w-3 h-3 fill-current" />
                        <span className="text-[8px] font-black">STABLE</span>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>

            {/* Macro RAG Search Info */}
            <Card
              padding="lg"
              className="bg-emerald-500/5 border-emerald-500/20 flex flex-col md:flex-row items-center gap-8 rounded-[3rem]"
            >
              <div className="p-6 bg-emerald-500 rounded-3xl">
                <Search className="w-12 h-12 text-white" />
              </div>
              <div className="text-center md:text-left">
                <h4 className="text-2xl font-black italic manga-font uppercase mb-2">
                  Macro-RAG Enabled
                </h4>
                <p className="text-sm font-bold opacity-50 uppercase leading-relaxed tracking-wide">
                  Ces communautés ne sont pas seulement visuelles. Elles sont utilisées par l'Expert
                  Nexus pour obtenir un contexte macro-conceptuel sur les sagas complètes avant
                  d'affiner sa recherche.
                </p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LoreWorldMapPage;
