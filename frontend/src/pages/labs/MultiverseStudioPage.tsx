import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Users, Maximize2, X, LayoutGrid } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '../../utils/apiClient';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

import { NexusMap } from '../../features/labs/components/Multiverse/NexusMap';
import { GenesisToolbox } from '../../features/labs/components/Multiverse/GenesisToolbox';
import type { GraphData, GraphNode } from '../../types';
import { LabGuide, LAB_CTA, LAB_LABEL } from './components/shared/LabKit';

// --- Types ---

interface MultiverseNode {
  id: string;
  type: 'genre' | 'universe';
  name: string;
  metadata?: {
    description?: string;
    cosmology?: string;
    characters?: string[];
  };
  x?: number;
  y?: number;
}

interface MultiverseLink {
  source: string;
  target: string;
}

interface MultiverseData {
  nodes: MultiverseNode[];
  links: MultiverseLink[];
}

const MultiverseStudioPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [activeSynthesis, setActiveSynthesis] = useState<MultiverseNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<MultiverseNode | null>(null);

  // --- Queries & Mutations ---

  const {
    data: graphData,
    isLoading: isGraphLoading,
    isFetching: isGraphFetching,
  } = useQuery<MultiverseData>({
    queryKey: ['multiverse-gallery'],
    queryFn: () => apiClient('/api/v1/multiverse/gallery/'),
  });

  const synthesizeMutation = useMutation<
    void,
    Error,
    { action: string; universe_name: string; genre: string }
  >({
    mutationFn: (body: { action: string; universe_name: string; genre: string }) =>
      apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      // Refresh graph data after a successful generation
      queryClient.invalidateQueries({ queryKey: ['multiverse-gallery'] });
    },
  });

  const mutationsInProgress = useRef(new Set<string>());

  const handleDropSeed = (seed: string, x: number, y: number) => {
    const id = `latent_${Date.now()}`;
    const latentNode: MultiverseNode = {
      id,
      name: t('labs.multiverse.synthesizing_seed', 'Synthesizing {{seed}}...', { seed }),
      type: 'universe',
      x,
      y,
    };

    setActiveSynthesis((prev) => [...prev, latentNode]);
    mutationsInProgress.current.add(id);

    synthesizeMutation.mutate(
      {
        action: 'synthesize',
        universe_name: `${seed}_${id.slice(-4)}`,
        genre: seed,
      },
      {
        onSettled: () => {
          mutationsInProgress.current.delete(id);
        },
      },
    );
  };

  // Robust removal of latent nodes once sync is complete
  useEffect(() => {
    if (!isGraphFetching && activeSynthesis.length > 0) {
      const stillRunning = activeSynthesis.filter((n) => mutationsInProgress.current.has(n.id));
      if (stillRunning.length !== activeSynthesis.length) {
        setActiveSynthesis(stillRunning);
      }
    }
  }, [isGraphFetching, activeSynthesis]);

  // --- Graph Helpers ---

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node as unknown as MultiverseNode);
  }, []);

  const mergedData = useMemo(() => {
    if (!graphData) return { nodes: activeSynthesis, links: [] };
    return {
      nodes: [...graphData.nodes, ...activeSynthesis],
      links: graphData.links,
    };
  }, [graphData, activeSynthesis]);

  return (
    <div className="w-full bg-[#0B0C10] text-[#F4F1E8]">
      <AnimatedPage>
        <div className="relative flex h-[calc(100vh-64px)] w-full overflow-hidden">
          {/* --- MAIN AREA: Nexus Explorer --- */}
          <main className="relative flex flex-1 flex-col">
            {/* Genesis Toolbox (Floating Draggable) */}
            <GenesisToolbox />

            {/* Graph Overlay: Controls */}
            <div className="pointer-events-none absolute right-8 top-8 z-20 flex gap-4">
              <div className="pointer-events-auto flex gap-1 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10]/80 p-1.5 backdrop-blur-xl">
                <div className="cursor-default rounded-xl bg-[#E8442B] px-6 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#F4F1E8]">
                  Nexus Map
                </div>
                <Link
                  to="/multiverse/catalog/"
                  className="flex items-center gap-2 rounded-xl px-6 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]"
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  {t('labs.multiverse.catalog_btn', 'Catalogue')}
                </Link>
              </div>
            </div>

            {/* Graph View */}
            <div className="relative flex-1 bg-[#0B0C10]">
              {isGraphLoading ? (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[#0B0C10]">
                  <Loader2 className="mb-4 h-12 w-12 animate-spin text-[#FDB913]" />
                  <p className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {t('labs.multiverse.sync_nexus', 'Synchronisation du Nexus...')}
                  </p>
                </div>
              ) : (
                <NexusMap
                  data={mergedData as unknown as GraphData}
                  loadingNodes={activeSynthesis}
                  onDropSeed={handleDropSeed}
                  onNodeClick={handleNodeClick}
                />
              )}

              {/* Quick Stats Overlay */}
              <div className="pointer-events-none absolute bottom-8 left-8 z-20 hidden md:block">
                <div className="flex gap-4">
                  <div className="pointer-events-auto min-w-[150px] rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]/80 px-5 py-4 backdrop-blur-xl">
                    <span className="mb-1 block text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                      {t('labs.multiverse.graph_entities', 'Entités Graphe')}
                    </span>
                    <span className="font-manga text-xl font-black italic text-[#FDB913]">
                      {mergedData.nodes.length || 0}
                    </span>
                  </div>
                  <div className="pointer-events-auto min-w-[150px] rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]/80 px-5 py-4 backdrop-blur-xl">
                    <span className="mb-1 block text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                      {t('labs.multiverse.semantic_links', 'Liaisons Sémantiques')}
                    </span>
                    <span className="font-manga text-xl font-black italic text-[#F4F1E8]">
                      {mergedData.links.length || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Side Detail Panel (Floating Drawer for selected node) */}
            <AnimatePresence>
              {selectedNode && selectedNode.type === 'universe' && (
                <motion.div
                  initial={{ x: '100%' }}
                  animate={{ x: 0 }}
                  exit={{ x: '100%' }}
                  transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                  className="absolute right-0 top-0 z-40 flex h-full w-[450px] flex-col border-l border-[#F4F1E8]/10 bg-[#0F1016] shadow-[-20px_0_50px_rgba(0,0,0,0.8)]"
                >
                  <div className="flex items-start justify-between border-b border-[#F4F1E8]/10 p-10">
                    <div>
                      <p className="mb-4 text-[10px] font-black uppercase tracking-[0.25em] text-[#FDB913]">
                        {t('labs.multiverse.synthetic_universe', 'UNIVERS SYNTHÉTIQUE')}
                      </p>
                      <h2 className="font-manga text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
                        {selectedNode.name}
                      </h2>
                    </div>
                    <button
                      onClick={() => setSelectedNode(null)}
                      className="group relative z-10 rounded-full border border-[#F4F1E8]/10 bg-transparent p-3 transition-colors hover:border-[#FDB913]"
                    >
                      <X className="h-6 w-6 text-[#8F94A5] transition-colors group-hover:text-[#F4F1E8]" />
                    </button>
                  </div>

                  <div className="custom-scrollbar flex-1 space-y-12 overflow-y-auto p-10">
                    <section className="space-y-4">
                      <header className="flex items-center gap-3">
                        <Maximize2 className="h-4 w-4 text-[#E8442B]" aria-hidden="true" />
                        <h3 className={LAB_LABEL}>Cosmologie &amp; Narration</h3>
                      </header>
                      <div className="relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-8">
                        <div
                          className="absolute left-0 top-0 h-full w-1 bg-[#E8442B]"
                          aria-hidden
                        />
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#F4F1E8]/80">
                          {selectedNode.metadata?.description ||
                            selectedNode.metadata?.cosmology ||
                            t(
                              'labs.multiverse.no_cosmology',
                              'Aucune description cosmologique disponible pour cet univers.',
                            )}
                        </p>
                      </div>
                    </section>

                    {selectedNode.metadata?.characters &&
                      selectedNode.metadata.characters.length > 0 && (
                        <section className="space-y-6">
                          <header className="flex items-center gap-3">
                            <Users className="h-4 w-4 text-[#E8442B]" aria-hidden="true" />
                            <h3 className={LAB_LABEL}>
                              {t('labs.multiverse.nexus_entities', 'Entités du Nexus')}
                            </h3>
                          </header>
                          <div className="grid grid-cols-2 gap-4">
                            {selectedNode.metadata.characters.map((char, idx) => (
                              <div
                                key={idx}
                                className="flex cursor-default items-center gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 transition-colors hover:border-[#FDB913]/40"
                              >
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FDB913]/15 text-[10px] font-black text-[#FDB913]">
                                  {char.charAt(0)}
                                </div>
                                <span className="truncate text-xs font-black uppercase text-[#F4F1E8]/80">
                                  {char}
                                </span>
                              </div>
                            ))}
                          </div>
                        </section>
                      )}

                    <div className="border-t border-[#F4F1E8]/10 pt-8">
                      <button type="button" className={LAB_CTA}>
                        {t('labs.multiverse.enter_universe', "ENTRER DANS L'UNIVERS")}
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>

        {/* Guide & Protocole */}
        <div className="mx-auto max-w-7xl px-4 pb-16 sm:px-6">
          <h2 className="sr-only">Guide du Multivers</h2>
          <LabGuide
            steps={[
              {
                title: 'Explore la carte',
                body: 'Chaque bulle de la Nexus Map est un genre ou un univers. Clique sur un univers pour lire sa cosmologie et découvrir ses personnages.',
              },
              {
                title: 'Sème un genre',
                body: 'Glisse une graine de genre depuis la boîte Genesis directement sur la carte : un nouvel univers est synthétisé en quelques secondes.',
              },
              {
                title: 'Parcours le catalogue',
                body: 'Tous les univers créés sont conservés. Bascule sur la vue Catalogue pour les parcourir sous forme de liste.',
              },
            ]}
            note="La synthèse d'univers génère un lore cohérent (cosmologie, personnages) via LLM et le persiste dans le graphe Neo4j. La Nexus Map affiche ce graphe — nœuds et liaisons sémantiques — et se resynchronise après chaque génération."
          />
        </div>
      </AnimatedPage>
    </div>
  );
};

export default MultiverseStudioPage;
