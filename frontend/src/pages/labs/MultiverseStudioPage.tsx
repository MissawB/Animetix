import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Loader2,
  Users,
  Network,
  Maximize2,
  X,
  LayoutGrid
} from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

import { NexusMap } from '../../features/labs/components/Multiverse/NexusMap';
import { GenesisToolbox } from '../../features/labs/components/Multiverse/GenesisToolbox';
import type { GraphData, GraphNode } from '../../types';

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
  const queryClient = useQueryClient();
  const [activeSynthesis, setActiveSynthesis] = useState<MultiverseNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<MultiverseNode | null>(null);

  // --- Queries & Mutations ---

  const { data: graphData, isLoading: isGraphLoading, isFetching: isGraphFetching } = useQuery<MultiverseData>({
    queryKey: ['multiverse-gallery'],
    queryFn: () => apiClient('/api/v1/multiverse/gallery/'),
  });

  const synthesizeMutation = useMutation<void, Error, { action: string; universe_name: string; genre: string }>({
    mutationFn: (body: { action: string; universe_name: string; genre: string }) => 
        apiClient('/api/v1/singularity-lab/', { 
            method: 'POST', 
            body: JSON.stringify(body) 
        }),
    onSuccess: () => {
        // Refresh graph data after a successful generation
        queryClient.invalidateQueries({ queryKey: ['multiverse-gallery'] });
    }
  });

  const mutationsInProgress = useRef(new Set<string>());

  const handleDropSeed = (seed: string, x: number, y: number) => {
    const id = `latent_${Date.now()}`;
    const latentNode: MultiverseNode = { id, name: `Synthesizing ${seed}...`, type: 'universe', x, y };
    
    setActiveSynthesis(prev => [...prev, latentNode]);
    mutationsInProgress.current.add(id);
    
    synthesizeMutation.mutate({ 
        action: 'synthesize', 
        universe_name: `${seed}_${id.slice(-4)}`, 
        genre: seed 
    }, {
        onSettled: () => {
            mutationsInProgress.current.delete(id);
        }
    });
  };

  // Robust removal of latent nodes once sync is complete
  useEffect(() => {
    if (!isGraphFetching && activeSynthesis.length > 0) {
      const stillRunning = activeSynthesis.filter(n => mutationsInProgress.current.has(n.id));
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
      links: graphData.links
    };
  }, [graphData, activeSynthesis]);

  return (
    <div className="h-[calc(100vh-64px)] w-full flex overflow-hidden bg-[#05050a] text-white">
      <AnimatedPage>
        <div className="h-full w-full flex relative">
            
            {/* --- MAIN AREA: Nexus Explorer --- */}
            <main className="flex-1 relative flex flex-col">
                
                {/* Genesis Toolbox (Floating Draggable) */}
                <GenesisToolbox />

                {/* Graph Overlay: Controls */}
                <div className="absolute top-8 right-8 z-20 flex gap-4 pointer-events-none">
                    <div className="flex bg-black/60 backdrop-blur-xl border border-white/10 p-1.5 rounded-2xl pointer-events-auto shadow-2xl gap-1">
                        <div className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest bg-cyan-600 text-white shadow-lg cursor-default">
                            Nexus Map
                        </div>
                        <Link 
                            to="/multiverse/catalog/" 
                            className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest text-white/60 hover:text-white hover:bg-white/5 transition-all flex items-center gap-2"
                        >
                            <LayoutGrid className="w-3.5 h-3.5" />
                            Catalogue
                        </Link>
                    </div>
                </div>

                {/* Graph View */}
                <div className="flex-1 relative bg-black">
                    {isGraphLoading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#05050a] z-10">
                            <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mb-4" />
                            <p className="text-[10px] font-black uppercase tracking-widest text-cyan-500/50">Synchronisation du Nexus...</p>
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
                    <div className="absolute bottom-8 left-8 z-20 pointer-events-none hidden md:block">
                        <div className="flex gap-4">
                            <Card padding="sm" className="bg-black/40 backdrop-blur-xl border-white/5 pointer-events-auto min-w-[150px]">
                                <span className="text-[8px] font-black uppercase opacity-30 block mb-1">Entités Graphe</span>
                                <span className="text-xl font-black italic manga-font text-cyan-500">{mergedData.nodes.length || 0}</span>
                            </Card>
                            <Card padding="sm" className="bg-black/40 backdrop-blur-xl border-white/5 pointer-events-auto min-w-[150px]">
                                <span className="text-[8px] font-black uppercase opacity-30 block mb-1">Liaisons Sémantiques</span>
                                <span className="text-xl font-black italic manga-font text-emerald-500">{mergedData.links.length || 0}</span>
                            </Card>
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
                        className="absolute top-0 right-0 h-full w-[450px] z-40 bg-[#08080c] border-l border-white/10 shadow-[-20px_0_50px_rgba(0,0,0,0.8)] flex flex-col"
                    >
                        <div className="p-10 border-b border-white/5 flex justify-between items-start bg-gradient-to-br from-cyan-950/20 to-transparent relative">
                            <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                                <Network className="w-32 h-32 text-cyan-500" />
                            </div>
                            <div>
                                <Badge variant="primary" className="mb-4 bg-cyan-500/10 text-cyan-400 border-cyan-500/20 px-4 py-1">
                                    UNIVERS SYNTHÉTIQUE
                                </Badge>
                                <h2 className="text-4xl font-black italic tracking-tighter uppercase text-white leading-none">
                                    {selectedNode.name}
                                </h2>
                            </div>
                            <button 
                                onClick={() => setSelectedNode(null)}
                                className="p-3 bg-white/5 hover:bg-white/10 rounded-full transition-all group relative z-10"
                            >
                                <X className="w-6 h-6 text-white/40 group-hover:text-white transition-colors" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-10 space-y-12 custom-scrollbar">
                            <section className="space-y-4">
                                <header className="flex items-center gap-3">
                                    <Maximize2 className="w-4 h-4 text-cyan-500" />
                                    <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/50">Cosmologie & Narration</h3>
                                </header>
                                <div className="p-8 bg-white/[0.02] rounded-3xl border border-white/5 relative overflow-hidden group">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500 opacity-20 group-hover:opacity-100 transition-opacity" />
                                    <p className="text-sm font-bold leading-relaxed text-gray-300 italic whitespace-pre-wrap">
                                    {selectedNode.metadata?.description || selectedNode.metadata?.cosmology || "Aucune description cosmologique disponible pour cet univers."}
                                    </p>
                                </div>
                            </section>

                            {selectedNode.metadata?.characters && selectedNode.metadata.characters.length > 0 && (
                                <section className="space-y-6">
                                    <header className="flex items-center gap-3">
                                        <Users className="w-4 h-4 text-cyan-500" />
                                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/50">Entités du Nexus</h3>
                                    </header>
                                    <div className="grid grid-cols-2 gap-4">
                                    {selectedNode.metadata.characters.map((char, idx) => (
                                        <div key={idx} className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3 hover:bg-white/10 transition-colors cursor-default">
                                            <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center text-[10px] font-black text-cyan-400">
                                                {char.charAt(0)}
                                            </div>
                                            <span className="text-xs font-black uppercase text-white/70 truncate">{char}</span>
                                        </div>
                                    ))}
                                    </div>
                                </section>
                            )}

                            <div className="pt-8 border-t border-white/5">
                                <Button className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-6 rounded-2xl font-black italic uppercase text-lg shadow-xl shadow-cyan-900/20">
                                    ENTRER DANS L'UNIVERS
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                )}
                </AnimatePresence>
            </main>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default MultiverseStudioPage;
