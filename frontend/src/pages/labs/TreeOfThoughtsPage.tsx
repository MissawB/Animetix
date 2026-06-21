import React, { useState, useCallback, useRef } from 'react';
import { 
  GitBranch, 
  Search, 
  Loader2, 
  ChevronRight, 
  Info,
  X,
  Network,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import _ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
const ForceGraph2D = (_ForceGraph2D as unknown as { default: React.ElementType }).default || _ForceGraph2D;
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

interface ToTNode {
  id: string;
  type: 'root' | 'selected' | 'pruned' | 'final';
  score: number;
  full_text: string;
  label?: string;
  x?: number;
  y?: number;
}

interface ToTLink {
  source: string | ToTNode;
  target: string | ToTNode;
}

interface ToTGraphData {
  nodes: ToTNode[];
  links: ToTLink[];
}

interface ToTResponse {
    full_tree: ToTGraphData;
    final_answer: string;
}

const TreeOfThoughtsPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<ToTNode | null>(null);
  const [graphData, setGraphData] = useState<ToTGraphData | null>(null);
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined); // react-force-graph-2d imperative handle

  const totMutation = useMutation<ToTResponse, Error, { query: string }>({
    mutationFn: (body: { query: string }) => apiClient('/api/v1/labs/tot/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
    }),
    onSuccess: (data) => {
        if (data.full_tree) {
            setGraphData(data.full_tree);
            // Auto-zoom after data loads
            setTimeout(() => {
                if (fgRef.current) {
                    fgRef.current.zoomToFit(400);
                }
            }, 500);
        }
    }
  });

  const handleNodeClick = useCallback((node: ToTNode) => {
    setSelectedNode(node);
    // Center camera on node
    if (fgRef.current && node.x !== undefined && node.y !== undefined) {
        fgRef.current.centerAt(node.x, node.y, 1000);
        fgRef.current.zoom(2, 1000);
    }
  }, []);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'root': return '#ffffff';
      case 'selected': return '#10b981'; // Emerald-500
      case 'pruned': return '#991b1b'; // Red-800
      case 'final': return '#fbbf24'; // Yellow-400
      default: return '#6b7280';
    }
  };

  const getNodeSize = (type: string) => {
    switch (type) {
      case 'root': return 8;
      case 'selected': return 6;
      case 'final': return 7;
      case 'pruned': return 4;
      default: return 5;
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="h-[calc(100vh-84px)] w-full flex overflow-hidden relative z-10">
          
          {/* Input & Controls Sidebar */}
          <div className="w-96 flex-shrink-0 border-r border-white/5 bg-black/40 backdrop-blur-xl p-8 flex flex-col z-20 overflow-y-auto custom-scrollbar">
            <header className="mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-4">
                <GitBranch className="w-3 h-3" /> Recursive Reasoning Lab
              </div>
              <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase mb-4">
                TREE OF <span className="text-emerald-500 text-glow">THOUGHTS</span>
              </h1>
              <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
                Visualisez le raisonnement multi-branches (MCTS) de l'IA en temps réel.
              </p>
            </header>

            <div className="space-y-6">
              <div className="space-y-3">
                <label htmlFor="cognitive-query" className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2 flex items-center gap-2">
                  <Search className="w-3 h-3" /> Requête Cognitive
                </label>
                <textarea
                  id="cognitive-query"
                  aria-label="Requête cognitive"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Entrez un problème complexe..."
                  className="w-full h-32 bg-white/5 border-2 border-white/5 rounded-2xl p-4 text-sm font-bold text-white outline-none focus:border-emerald-500/50 transition-all resize-none placeholder:opacity-20"
                />
              </div>

              <Button 
                onClick={() => totMutation.mutate({ query })}
                disabled={totMutation.isPending || !query.trim()}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all border-none"
              >
                {totMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "GÉNÉRER L'ARBRE"}
              </Button>
            </div>

            <div className="mt-12 space-y-8">
              <Card padding="md" className="bg-white/5 border-white/5 opacity-60">
                <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-emerald-400 flex items-center gap-2">
                  <Info className="w-3 h-3" /> Légende des Nœuds
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-[8px] font-black uppercase">
                    <div className="w-2 h-2 rounded-full bg-white" /> Point d'Origine
                  </div>
                  <div className="flex items-center gap-3 text-[8px] font-black uppercase">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" /> Chemin Sélectionné
                  </div>
                  <div className="flex items-center gap-3 text-[8px] font-black uppercase">
                    <div className="w-2 h-2 rounded-full bg-red-800" /> Branche Élaguée
                  </div>
                  <div className="flex items-center gap-3 text-[8px] font-black uppercase">
                    <div className="w-2 h-2 rounded-full bg-yellow-400" /> Conclusion Finale
                  </div>
                </div>
              </Card>

              <Card padding="md" className="bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-6 -bottom-6 opacity-5 group-hover:opacity-10 transition-opacity">
                      <GitBranch className="w-32 h-32 text-emerald-500" />
                  </div>
                  <h4 className="text-[11px] font-black italic manga-font uppercase mb-3 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" /> Guide de l'Arbre
                  </h4>
                  <div className="space-y-3 relative z-10">
                      <p className="text-[9px] font-bold uppercase tracking-wider text-white/50 leading-relaxed">
                          <span className="text-emerald-400">Multi-Pensée :</span> L'IA n'écrit pas d'un seul trait. Elle explore plusieurs "branches" de réflexion en parallèle pour trouver la meilleure solution.
                      </p>
                      <p className="text-[9px] font-bold uppercase tracking-wider text-white/50 leading-relaxed">
                          <span className="text-emerald-400">L'Élagage :</span> Si une branche mène à une impasse logique, l'IA l'abandonne (en rouge) pour se concentrer sur les chemins prometteurs (en vert).
                      </p>
                  </div>
              </Card>
            </div>
          </div>

        {/* Main Visualization Area */}
        <div className="flex-1 relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-950/10 via-black to-black">
          {graphData ? (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              backgroundColor="rgba(0,0,0,0)"
              nodeLabel={(node: ToTNode) => `${node.type.toUpperCase()} | Score: ${node.score}`}
              nodeColor={(node: ToTNode) => getNodeColor(node.type)}
              nodeRelSize={1}
              nodeCanvasObject={(node: ToTNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
                const size = getNodeSize(node.type);
                const color = getNodeColor(node.type);
                
                // Draw glow for selected/final nodes
                if (node.type === 'selected' || node.type === 'final') {
                    ctx.shadowColor = color;
                    ctx.shadowBlur = 15 / globalScale;
                } else {
                    ctx.shadowBlur = 0;
                }

                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI, false);
                ctx.fill();

                // Draw label for large nodes or when zoomed in
                if (globalScale > 3 || node.type === 'final' || node.type === 'root') {
                    const label = node.type === 'root' ? 'START' : node.type === 'final' ? 'END' : '';
                    if (label) {
                        ctx.font = `${4 / globalScale}px font-black`;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = '#000';
                        ctx.fillText(label, node.x || 0, node.y || 0);
                    }
                }
              }}
              linkColor={() => 'rgba(255, 255, 255, 0.05)'}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.005}
              linkDirectionalParticleWidth={2}
              linkDirectionalParticleColor={(link: ToTLink) => {
                  const targetId = typeof link.target === 'object' ? (link.target as ToTNode).id : link.target;
                  const target = graphData.nodes.find(n => n.id === targetId);
                  return target?.type === 'selected' || target?.type === 'final' ? '#10b981' : 'rgba(255,255,255,0.1)';
              }}
              onNodeClick={handleNodeClick}
              cooldownTicks={100}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center opacity-10">
              <Network className="w-64 h-64 mb-12 animate-pulse" />
              <h2 className="text-6xl font-black italic uppercase manga-font tracking-tighter">WAITING FOR REASONING</h2>
            </div>
          )}

          {/* Node Details Overlay Panel */}
          <AnimatePresence>
            {selectedNode && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="absolute top-8 right-8 w-96 max-h-[calc(100vh-128px)] overflow-y-auto z-30"
              >
                <Card padding="none" className="bg-black/80 backdrop-blur-2xl border-white/10 rounded-[2.5rem] shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden">
                  <div className="p-8 border-b border-white/5 flex justify-between items-start">
                    <div>
                      <Badge variant="neutral" className={`bg-white/5 border-none text-[8px] font-black italic uppercase tracking-widest mb-2 ${
                        selectedNode.type === 'selected' ? 'text-emerald-500' : 
                        selectedNode.type === 'pruned' ? 'text-red-500' : 
                        selectedNode.type === 'final' ? 'text-yellow-500' : ''
                      }`}>
                        {selectedNode.type} NODE
                      </Badge>
                      <h3 className="text-xl font-black italic manga-font uppercase tracking-tighter">
                        Inspection <span className="text-emerald-500">Nœud</span>
                      </h3>
                    </div>
                    <button 
                      onClick={() => setSelectedNode(null)}
                      className="p-2 hover:bg-white/5 rounded-full transition-colors"
                    >
                      <X className="w-5 h-5 text-white/40" />
                    </button>
                  </div>

                  <div className="p-8 space-y-8">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">Score de Confiance</span>
                        <span className="text-2xl font-black italic manga-font text-emerald-400">{(selectedNode.score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${selectedNode.score * 100}%` }}
                          className={`h-full ${selectedNode.type === 'pruned' ? 'bg-red-800' : 'bg-emerald-500'}`}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <span className="text-[10px] font-black opacity-30 uppercase tracking-widest flex items-center gap-2">
                        <ChevronRight className="w-3 h-3 text-emerald-500" /> Trace de Pensée
                      </span>
                      <div className="p-6 bg-white/5 rounded-3xl border border-white/5 text-sm font-bold leading-relaxed text-gray-300 italic">
                        "{selectedNode.full_text}"
                      </div>
                    </div>

                    <div className="pt-4 flex gap-4">
                       <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                          <p className="text-[8px] font-black opacity-20 uppercase mb-1">ID</p>
                          <p className="text-[10px] font-mono opacity-40 truncate">{selectedNode.id}</p>
                       </div>
                       <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                          <p className="text-[8px] font-black opacity-20 uppercase mb-1">Status</p>
                          <p className="text-[10px] font-black italic uppercase text-emerald-500">{selectedNode.type === 'pruned' ? 'TERMINATED' : 'ACTIVE'}</p>
                       </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </AnimatedPage>
  </div>
);
};

export default TreeOfThoughtsPage;


