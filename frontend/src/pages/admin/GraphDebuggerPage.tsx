import React, { useState } from 'react';
import { 
  Zap, 
  ShieldAlert, 
  RefreshCw, 
  Trash2, 
  Activity, 
  Database, 
  Layers, 
  ShieldCheck, 
  Search,
  Loader2,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Network
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

const GraphDebuggerPage: React.FC = () => {
  const [healingId, setHealingId] = useState('');

  const { data: audit, isLoading, refetch } = useQuery<any>({
    queryKey: ['graph-audit'],
    queryFn: () => apiClient('/api/v1/graph/debugger/'),
  });

  const cleanupMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/graph/debugger/', {
        method: 'POST',
        body: JSON.stringify({ action: 'cleanup' })
    }),
    onSuccess: () => refetch()
  });

  const healMutation = useMutation({
    mutationFn: (mediaId: string) => apiClient('/api/v1/graph/debugger/', {
        method: 'POST',
        body: JSON.stringify({ action: 'heal', media_id: mediaId })
    }),
    onSuccess: () => {
        setHealingId('');
        refetch();
    }
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-32 flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_20px_rgba(168,85,247,0.5)]"></div>
        <p className="text-sm font-black uppercase tracking-[0.3em] animate-pulse opacity-40">Auditing Knowledge Graph...</p>
    </div>
  );

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-purple-400 mb-4">
                <Network className="w-3 h-3" /> Lore Consistency Protocol
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                GRAPH <span className="text-purple-500 text-glow">HEALER</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Diagnostic et résolution des conflits de lore dans la base Neo4j.
            </p>
        </header>

        {/* Top Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <Card padding="lg" className="bg-navy-950 border-white/10 relative overflow-hidden group">
                <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:scale-110 transition-transform">
                    <AlertTriangle className="w-32 h-32" />
                </div>
                <p className="text-[10px] font-black uppercase opacity-40 mb-4 tracking-widest">Isolated Nodes</p>
                <div className="flex items-baseline gap-2">
                    <span className="text-6xl font-black italic manga-font text-white">{audit.isolated_nodes}</span>
                    <span className="text-xs font-bold opacity-30 uppercase">Entities</span>
                </div>
                <p className="text-[10px] font-bold opacity-30 mt-4 leading-relaxed uppercase">Nœuds sans aucune relation sémantique ou temporelle.</p>
            </Card>

            <Card padding="lg" className="bg-navy-950 border-white/10 relative overflow-hidden group">
                <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:scale-110 transition-transform text-red-500">
                    <Zap className="w-32 h-32" />
                </div>
                <p className="text-[10px] font-black uppercase opacity-40 mb-4 tracking-widest text-red-500">Lore Conflicts</p>
                <div className="flex items-baseline gap-2">
                    <span className="text-6xl font-black italic manga-font text-red-500">{audit.temporal_conflicts}</span>
                    <span className="text-xs font-bold opacity-30 uppercase">Detected</span>
                </div>
                <p className="text-[10px] font-bold opacity-30 mt-4 leading-relaxed uppercase">Contradictions temporelles (ex: suites antérieures à l'original).</p>
            </Card>

            <Card padding="lg" className="bg-navy-950 border-white/10 relative overflow-hidden group">
                <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:scale-110 transition-transform text-cyan-500">
                    <Layers className="w-32 h-32" />
                </div>
                <p className="text-[10px] font-black uppercase opacity-40 mb-4 tracking-widest text-cyan-500">Orphan Entities</p>
                <div className="flex items-baseline gap-2">
                    <span className="text-6xl font-black italic manga-font text-cyan-500">{audit.orphan_entities}</span>
                    <span className="text-xs font-bold opacity-30 uppercase">Entities</span>
                </div>
                <p className="text-[10px] font-bold opacity-30 mt-4 leading-relaxed uppercase">Entités extraites non rattachées à un média parent.</p>
            </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {/* Actions & Healing */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-purple-600 text-white border-none shadow-2xl">
                    <h3 className="text-2xl font-black italic manga-font uppercase mb-6 flex items-center gap-3">
                        <ShieldCheck className="w-8 h-8" /> Auto-Heal
                    </h3>
                    <p className="text-sm font-bold opacity-90 leading-relaxed uppercase mb-8">
                        Lancer un cycle de nettoyage global pour supprimer les bruits d'extraction et les contradictions logiques triviales.
                    </p>
                    <Button 
                        onClick={() => cleanupMutation.mutate()}
                        disabled={cleanupMutation.isPending}
                        fullWidth
                        className="bg-black text-white hover:bg-navy-900 py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                    >
                        {cleanupMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "EXECUTE CLEANUP"}
                    </Button>
                </Card>

                <Card padding="lg" className="bg-navy-900 border-white/5">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Search className="w-4 h-4 text-purple-500" /> Manual Healing
                    </h3>
                    <div className="space-y-6">
                        <div className="relative">
                            <input 
                                type="text"
                                value={healingId}
                                onChange={(e) => setHealingId(e.target.value)}
                                placeholder="Media ID (ex: anime-123)"
                                className="w-full bg-black/40 border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold focus:border-purple-500 outline-none transition-all"
                            />
                        </div>
                        <Button 
                            onClick={() => healMutation.mutate(healingId)}
                            disabled={!healingId || healMutation.isPending}
                            fullWidth
                            className="bg-white text-black hover:bg-gray-200 py-4 rounded-xl font-black italic uppercase tracking-wider"
                        >
                            {healMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : "RECONSTRUCT NODE"}
                        </Button>
                    </div>
                </Card>
            </div>

            {/* Conflicts List */}
            <div className="lg:col-span-8">
                <Card padding="none" className="bg-navy-900/40 border-white/10 rounded-[3rem] overflow-hidden shadow-2xl">
                    <header className="px-12 py-8 border-b border-white/5 flex justify-between items-center">
                        <h3 className="text-2xl font-black italic manga-font uppercase flex items-center gap-3">
                            <Zap className="w-6 h-6 text-red-500" /> Critical Conflicts
                        </h3>
                        <Badge variant="neutral" className="bg-red-500/10 text-red-500 border-none uppercase font-black italic">TOP 5</Badge>
                    </header>
                    
                    <div className="p-8">
                        {audit.details && audit.details.length > 0 ? (
                            <div className="space-y-4">
                                {audit.details.map((conflict: any, i: number) => (
                                    <div key={i} className="group p-6 bg-black/40 rounded-[2rem] border border-white/5 hover:border-red-500/30 transition-all">
                                        <div className="flex items-center justify-between gap-6">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className="text-sm font-black italic uppercase text-red-400">{conflict.t1}</span>
                                                    <Badge variant="neutral" className="bg-white/5 border-none text-[8px]">{conflict.y1}</Badge>
                                                </div>
                                                <div className="flex items-center gap-4 py-1">
                                                    <div className="h-px flex-grow bg-white/5" />
                                                    <span className="text-[8px] font-black opacity-20 uppercase tracking-[0.3em]">CONTRA-SEQUEL</span>
                                                    <div className="h-px flex-grow bg-white/5" />
                                                </div>
                                                <div className="flex items-center gap-3 mt-2">
                                                    <span className="text-sm font-black italic uppercase text-white">{conflict.t2}</span>
                                                    <Badge variant="neutral" className="bg-white/5 border-none text-[8px]">{conflict.y2}</Badge>
                                                </div>
                                            </div>
                                            <div className="w-12 h-12 rounded-2xl bg-red-500/10 flex items-center justify-center text-red-500 group-hover:scale-110 transition-transform">
                                                <RefreshCw className="w-6 h-6" />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-24 text-center">
                                <CheckCircle2 className="w-20 h-20 text-emerald-500 mx-auto mb-6 opacity-20" />
                                <h4 className="text-2xl font-black italic manga-font uppercase opacity-20">No critical conflicts</h4>
                            </div>
                        )}
                    </div>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default GraphDebuggerPage;

