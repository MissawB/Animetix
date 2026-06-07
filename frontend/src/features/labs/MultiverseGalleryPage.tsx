import React, { useState, useCallback, useRef, useMemo } from 'react';
import { 
  Network, 
  Search, 
  Loader2, 
  X,
  Map,
  Users,
  Info,
  Maximize2
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import _ForceGraph2D from 'react-force-graph-2d';
const ForceGraph2D = (_ForceGraph2D as any).default || _ForceGraph2D;

import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

interface MultiverseNode {
  id: string;
  type: 'genre' | 'universe';
  label: string;
  full_text?: string;
  characters?: string[];
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

const MultiverseGalleryPage: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<MultiverseNode | null>(null);
  const fgRef = useRef<any>(null);

  const { data: graphData, isLoading, error } = useQuery<MultiverseData>({
    queryKey: ['multiverse-gallery'],
    queryFn: () => apiClient('/api/v1/multiverse/gallery/'),
  });

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    if (fgRef.current) {
        fgRef.current.centerAt(node.x, node.y, 800);
        fgRef.current.zoom(2.5, 800);
    }
  }, []);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'genre': return '#10b981'; // Emerald-500
      case 'universe': return '#06b6d4'; // Cyan-500
      default: return '#6b7280';
    }
  };

  const getNodeSize = (type: string) => {
    switch (type) {
      case 'genre': return 8;
      case 'universe': return 5;
      default: return 4;
    }
  };

  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = getNodeSize(node.type);
    const color = getNodeColor(node.type);
    
    // Node Glow
    ctx.shadowColor = color;
    ctx.shadowBlur = (selectedNode?.id === node.id ? 25 : 10) / globalScale;

    // Node Body
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
    ctx.fill();

    // Node Label on hover or persistent for genres
    if (globalScale > 2 || node.type === 'genre') {
        const fontSize = (node.type === 'genre' ? 4 : 3) / globalScale;
        ctx.font = `bold ${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillText(node.label, node.x, node.y + size + 1);
    }
  }, [selectedNode]);

  return (
    <AnimatedPage>
      <div className="h-[calc(100vh-64px)] w-full flex overflow-hidden bg-[#050505] relative">
        
        {/* Dashboard Header Overlay */}
        <div className="absolute top-8 left-8 z-20 pointer-events-none">
          <header>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-cyan-400 mb-4 pointer-events-auto">
              <Network className="w-3 h-3" /> NEXUS MULTIVERSE MAP
            </div>
            <h1 className="text-5xl font-black italic tracking-tighter uppercase mb-2 text-white pointer-events-auto">
              GALLERY <span className="text-cyan-500 text-glow">NEXUS</span>
            </h1>
            <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed text-white pointer-events-auto">
              Explorez les interconnexions entre les univers synthétiques.
            </p>
          </header>
        </div>

        {/* Legend Overlay */}
        <div className="absolute bottom-8 left-8 z-20 pointer-events-none">
           <Card padding="sm" className="bg-black/40 backdrop-blur-xl border-white/5 pointer-events-auto">
              <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-cyan-400 flex items-center gap-2">
                <Info className="w-3 h-3" /> Légende du Nexus
              </h4>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-[8px] font-black uppercase text-white">
                  <div className="w-2 h-2 rounded-full bg-emerald-500" /> Genres Narratifs
                </div>
                <div className="flex items-center gap-3 text-[8px] font-black uppercase text-white">
                  <div className="w-2 h-2 rounded-full bg-cyan-500" /> Univers Synthétiques
                </div>
              </div>
           </Card>
        </div>

        {/* Graph Canvas */}
        <div className="flex-1 relative">
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mb-4" />
              <p className="text-[10px] font-black uppercase tracking-widest text-cyan-500/50">Synchronisation du Nexus...</p>
            </div>
          ) : graphData ? (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              backgroundColor="rgba(0,0,0,0)"
              nodeCanvasObject={nodeCanvasObject}
              onNodeClick={handleNodeClick}
              linkColor={() => 'rgba(255, 255, 255, 0.03)'}
              linkWidth={1}
              cooldownTicks={100}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.3}
            />
          ) : (
             <div className="absolute inset-0 flex flex-col items-center justify-center opacity-20">
               <Map className="w-32 h-32 text-white mb-4" />
               <p className="text-xl font-black uppercase tracking-tighter">Erreur de chargement du Nexus</p>
             </div>
          )}
        </div>

        {/* Side Detail Panel (Drawer) */}
        <AnimatePresence>
          {selectedNode && selectedNode.type === 'universe' && (
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute top-0 right-0 h-full w-[450px] z-30 bg-[#080808] border-l border-white/10 shadow-[-20px_0_50px_rgba(0,0,0,0.5)] flex flex-col"
            >
              <div className="p-10 border-b border-white/5 flex justify-between items-start bg-gradient-to-br from-cyan-950/20 to-transparent">
                <div>
                  <Badge variant="primary" className="mb-4 bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                    UNIVERS SYNTHÉTIQUE
                  </Badge>
                  <h2 className="text-4xl font-black italic tracking-tighter uppercase text-white leading-none">
                    {selectedNode.label}
                  </h2>
                </div>
                <button 
                  onClick={() => setSelectedNode(null)}
                  className="p-3 bg-white/5 hover:bg-white/10 rounded-full transition-all group"
                >
                  <X className="w-6 h-6 text-white/40 group-hover:text-white transition-colors" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-10 space-y-12">
                {/* Full Text / Description */}
                <section className="space-y-4">
                  <header className="flex items-center gap-3">
                    <Maximize2 className="w-4 h-4 text-cyan-500" />
                    <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/50">Cosmologie & Narration</h3>
                  </header>
                  <div className="p-8 bg-white/[0.02] rounded-3xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500 opacity-20 group-hover:opacity-100 transition-opacity" />
                    <p className="text-sm font-bold leading-relaxed text-gray-300 italic whitespace-pre-wrap">
                      {selectedNode.full_text || "Aucune description cosmologique disponible pour cet univers."}
                    </p>
                  </div>
                </section>

                {/* Characters */}
                {selectedNode.characters && selectedNode.characters.length > 0 && (
                  <section className="space-y-6">
                    <header className="flex items-center gap-3">
                      <Users className="w-4 h-4 text-cyan-500" />
                      <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/50">Entités du Nexus</h3>
                    </header>
                    <div className="grid grid-cols-2 gap-4">
                      {selectedNode.characters.map((char, idx) => (
                        <div key={idx} className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3 hover:bg-white/10 transition-colors cursor-default">
                          <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center text-[10px] font-black text-cyan-400">
                            {char.charAt(0)}
                          </div>
                          <span className="text-xs font-black uppercase text-white/70">{char}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                <div className="pt-8 border-t border-white/5">
                   <Button className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-6 rounded-2xl font-black italic uppercase text-lg">
                      ENTRER DANS L'UNIVERS
                   </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  );
};

export default MultiverseGalleryPage;
