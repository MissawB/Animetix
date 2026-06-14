import React, { useState, useCallback, useRef } from 'react';
import { 
  Globe,
  Loader2,
  ChevronRight,
  ShieldCheck,
  Zap,
  Target,
  Layers,
  Users,
  Film,
  Sparkles,
  Network,
  Maximize2,
  X,
  Plus,
  Compass,
  Database
} from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import _ForceGraph2D from 'react-force-graph-2d';
const ForceGraph2D = (_ForceGraph2D as any).default || _ForceGraph2D;

import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

// --- Types ---

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

const MultiverseStudioPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeView, setActiveView] = useState<'nexus' | 'forge'>('nexus');
  const [universeName, setUniverseName] = useState('ShinSekai');
  const [genre, setGenre] = useState('Cyberpunk');
  const [synthesizedResult, setSynthesizedResult] = useState<any | null>(null);
  const [selectedNode, setSelectedNode] = useState<MultiverseNode | null>(null);
  const fgRef = useRef<any>(null);

  // --- Queries & Mutations ---

  const { data: graphData, isLoading: isGraphLoading } = useQuery<MultiverseData>({
    queryKey: ['multiverse-gallery'],
    queryFn: () => apiClient('/api/v1/multiverse/gallery/'),
  });

  const synthesizeMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
    }),
    onSuccess: (data) => {
        setSynthesizedResult(data);
        // Refresh graph data after a successful generation
        queryClient.invalidateQueries({ queryKey: ['multiverse-gallery'] });
    }
  });

  // --- Graph Helpers ---

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
    
    ctx.shadowColor = color;
    ctx.shadowBlur = (selectedNode?.id === node.id ? 25 : 10) / globalScale;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
    ctx.fill();

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
    <div className="h-[calc(100vh-64px)] w-full flex overflow-hidden bg-[#05050a] text-white">
      <AnimatedPage>
        <div className="h-full w-full flex relative">
            
            {/* --- LEFT SIDEBAR: Genesis Forge --- */}
            <aside className={`w-[450px] h-full bg-[#080810] border-r border-white/5 flex flex-col z-30 transition-transform duration-500 ${activeView === 'forge' ? 'translate-x-0' : 'translate-x-0'}`}>
                
                {/* Forge Header */}
                <div className="p-8 border-b border-white/5 bg-gradient-to-br from-red-950/20 to-transparent relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                        <Sparkles className="w-24 h-24 rotate-12 text-red-500" />
                    </div>
                    <div className="flex items-center justify-between mb-6">
                        <Badge className="bg-red-600/10 text-red-500 border-red-500/20 uppercase tracking-[0.2em] text-[8px] font-black italic px-4 py-1.5 rounded-xl">
                            ADMS FORGE v2.4
                        </Badge>
                        <button 
                            onClick={() => setActiveView(activeView === 'nexus' ? 'forge' : 'nexus')}
                            className="p-2 bg-white/5 rounded-lg hover:bg-white/10 transition-all lg:hidden"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    <h2 className="text-4xl font-black italic manga-font tracking-tighter uppercase mb-2">
                        GENESIS <span className="text-red-500 text-glow">STUDIO</span>
                    </h2>
                    <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.2em]">Synthétiseur de Lore Autonome</p>
                </div>

                {/* Forge Content */}
                <div className="flex-grow overflow-y-auto custom-scrollbar p-8 space-y-10">
                    
                    {/* Input Section */}
                    <section className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Identifiant de Réalité</label>
                            <input 
                                type="text" 
                                value={universeName} 
                                onChange={(e) => setUniverseName(e.target.value)} 
                                className="w-full bg-black border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold focus:border-red-500 outline-none transition-all text-white placeholder:opacity-20"
                                placeholder="Nom de l'univers..."
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Paradigme Narratif</label>
                            <select 
                                value={genre} 
                                onChange={(e) => setGenre(e.target.value)} 
                                className="w-full bg-black border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-red-500 transition-all appearance-none"
                            >
                                <option value="Cyberpunk">Cyberpunk</option>
                                <option value="Sci-Fi">Sci-Fi</option>
                                <option value="Fantasy">Fantasy</option>
                                <option value="Steampunk">Steampunk</option>
                                <option value="Isekai">Isekai</option>
                            </select>
                        </div>
                        <Button 
                            onClick={() => synthesizeMutation.mutate({ action: 'synthesize', universe_name: universeName, genre: genre })} 
                            disabled={synthesizeMutation.isPending} 
                            className="w-full bg-red-600 hover:bg-red-500 text-white py-5 rounded-2xl font-black italic text-md uppercase shadow-xl hover:scale-[1.02] active:scale-95 transition-all border-none"
                        >
                            {synthesizeMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Plus className="w-5 h-5 mr-2" /> Initier la Synthèse</>}
                        </Button>
                    </section>

                    {/* Result Visualization */}
                    <AnimatePresence mode="wait">
                        {synthesizedResult && (
                            <motion.div 
                                initial={{ opacity: 0, y: 20 }} 
                                animate={{ opacity: 1, y: 0 }} 
                                className="space-y-8 pt-6 border-t border-white/5"
                            >
                                <header className="flex justify-between items-center">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest text-red-400 flex items-center gap-2">
                                        <Database className="w-3 h-3" /> Projection Réussie
                                    </h4>
                                    <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-400 border-none text-[8px] italic">
                                        PERSISTED_IN_NEO4J
                                    </Badge>
                                </header>

                                <div className="p-6 bg-white/[0.02] rounded-3xl border border-white/5 relative group">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-red-500 opacity-20" />
                                    <h5 className="text-xl font-black italic uppercase text-white mb-2">{synthesizedResult.universe?.name}</h5>
                                    <p className="text-xs font-medium text-gray-400 italic leading-relaxed line-clamp-4">
                                        "{synthesizedResult.universe?.description}"
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <Card padding="md" className="bg-navy-950/40 border-white/5 flex flex-col justify-between h-24">
                                        <span className="text-[8px] font-black uppercase opacity-30">Cohérence</span>
                                        <span className="text-3xl font-black italic manga-font text-red-500">
                                            {Math.round((synthesizedResult.evaluation?.ai_score || 0) * 100)}%
                                        </span>
                                    </Card>
                                    <Card padding="md" className="bg-navy-950/40 border-white/5 flex flex-col justify-between h-24">
                                        <span className="text-[8px] font-black uppercase opacity-30">Immersion</span>
                                        <span className="text-3xl font-black italic manga-font text-blue-400">
                                            {Math.round((synthesizedResult.evaluation?.community_score || 0) * 100)}%
                                        </span>
                                    </Card>
                                </div>

                                <Button 
                                    variant="outline"
                                    onClick={() => {
                                        const node = graphData?.nodes.find(n => n.label === synthesizedResult.universe?.name);
                                        if (node) handleNodeClick(node);
                                    }}
                                    className="w-full border-white/10 text-gray-400 hover:text-white text-[10px] font-black uppercase tracking-widest py-4"
                                >
                                    Localiser dans le Nexus <Compass className="ml-2 w-3 h-3" />
                                </Button>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {!synthesizedResult && !synthesizeMutation.isPending && (
                        <div className="py-20 text-center opacity-10 flex flex-col items-center">
                            <Globe className="w-16 h-16 mb-4" />
                            <p className="text-[10px] font-black uppercase tracking-[0.3em]">En attente de paramètres...</p>
                        </div>
                    )}
                </div>

                {/* Forge Footer */}
                <div className="p-6 border-t border-white/5 bg-black/20 text-center">
                    <p className="text-[8px] font-black uppercase tracking-[0.4em] opacity-20">
                        SYNERGY ENGINE v2.0 • SOTA_PROJECTION_READY
                    </p>
                </div>
            </aside>

            {/* --- MAIN AREA: Nexus Explorer --- */}
            <main className="flex-1 relative flex flex-col">
                
                {/* Graph Overlay: Controls */}
                <div className="absolute top-8 right-8 z-20 flex gap-4 pointer-events-none">
                    <div className="flex bg-black/60 backdrop-blur-xl border border-white/10 p-1.5 rounded-2xl pointer-events-auto shadow-2xl">
                        <button 
                            onClick={() => setActiveView('nexus')}
                            className={`px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeView === 'nexus' ? 'bg-cyan-600 text-white shadow-lg' : 'text-white/40 hover:text-white'}`}
                        >
                            Nexus Map
                        </button>
                        <button 
                            onClick={() => setActiveView('forge')}
                            className={`px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeView === 'forge' ? 'bg-red-600 text-white shadow-lg' : 'text-white/40 hover:text-white'}`}
                        >
                            Lore Forge
                        </button>
                    </div>
                </div>

                {/* Graph View */}
                <div className="flex-1 relative bg-black">
                    {isGraphLoading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#05050a] z-10">
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
                            linkColor={() => 'rgba(255, 255, 255, 0.05)'}
                            linkWidth={1}
                            cooldownTicks={100}
                            d3AlphaDecay={0.02}
                            d3VelocityDecay={0.3}
                        />
                    ) : (
                        <div className="absolute inset-0 flex flex-col items-center justify-center opacity-20">
                            <Network className="w-32 h-32 text-white mb-4" />
                            <p className="text-xl font-black uppercase tracking-tighter">Nexus Offline</p>
                        </div>
                    )}

                    {/* Quick Stats Overlay */}
                    <div className="absolute bottom-8 left-8 z-20 pointer-events-none hidden md:block">
                        <div className="flex gap-4">
                            <Card padding="sm" className="bg-black/40 backdrop-blur-xl border-white/5 pointer-events-auto min-w-[150px]">
                                <span className="text-[8px] font-black uppercase opacity-30 block mb-1">Entités Graphe</span>
                                <span className="text-xl font-black italic manga-font text-cyan-500">{graphData?.nodes.length || 0}</span>
                            </Card>
                            <Card padding="sm" className="bg-black/40 backdrop-blur-xl border-white/5 pointer-events-auto min-w-[150px]">
                                <span className="text-[8px] font-black uppercase opacity-30 block mb-1">Liaisons Sémantiques</span>
                                <span className="text-xl font-black italic manga-font text-emerald-500">{graphData?.links.length || 0}</span>
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
                                    {selectedNode.label}
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
                                    {selectedNode.full_text || "Aucune description cosmologique disponible pour cet univers."}
                                    </p>
                                </div>
                            </section>

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
