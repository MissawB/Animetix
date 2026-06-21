import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { 
    Activity, 
    Zap, 
    Shield,
    Cpu, 
    Radio, 
    Terminal,
    ChevronRight,
    AlertTriangle,
    Database,
    Binary
} from 'lucide-react';
import { motion } from 'framer-motion';

interface AIServiceStatus {
    id: string;
    name: string;
    status: 'online' | 'offline' | 'warning';
    load: number;
    metrics: Record<string, unknown>;
}

interface SingularityHealth {
    status: string;
    services: AIServiceStatus[];
    events: { time: string; type: string; msg: string }[];
    system_load: number;
}

const SingularityCommandCenterPage: React.FC = () => {
    const { data, isLoading } = useQuery<SingularityHealth>({
        queryKey: ['singularity-command-center'],
        queryFn: () => apiClient('/api/v1/singularity-lab/command-center/'),
        refetchInterval: 5000 // Real-time feel
    });

    if (isLoading) return (
        <div className="min-h-screen bg-black flex items-center justify-center">
            <div className="flex flex-col items-center gap-6">
                <div className="w-20 h-20 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin shadow-[0_0_50px_rgba(6,182,212,0.3)]"></div>
                <span className="text-cyan-500 font-black italic uppercase tracking-[0.5em] animate-pulse">Establishing Neural Link...</span>
            </div>
        </div>
    );

    return (
        <AnimatedPage>
            <div className="min-h-screen bg-[#050505] text-white p-8 lg:p-12 overflow-hidden selection:bg-cyan-500 selection:text-black">
                
                {/* Header : HUD Style */}
                <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 gap-8 border-b border-white/5 pb-12">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-cyan-500 animate-ping" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500/60">System Operator Console v4.0</span>
                        </div>
                        <h1 className="text-6xl md:text-8xl font-black italic manga-font tracking-tighter uppercase leading-none">
                            SINGULARITY <span className="text-cyan-500 text-glow-cyan">HUB</span>
                        </h1>
                        <p className="text-sm font-bold opacity-30 uppercase tracking-[0.2em] max-w-xl leading-relaxed italic">
                            Interface de monitoring centralisée pour l'orchestration des modèles cognitifs avancés.
                        </p>
                    </div>

                    <div className="flex gap-6">
                        <div className="text-right">
                            <span className="block text-[8px] font-black uppercase opacity-30 mb-1 tracking-widest text-cyan-400">Global Efficiency</span>
                            <span className="text-4xl font-black italic manga-font text-white">{100 - (data?.system_load || 0)}%</span>
                        </div>
                        <div className="w-px h-12 bg-white/10" />
                        <div className="text-right">
                            <span className="block text-[8px] font-black uppercase opacity-30 mb-1 tracking-widest text-purple-400">Cognitive Nodes</span>
                            <span className="text-4xl font-black italic manga-font text-white">{data?.services?.length || 0}</span>
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                    
                    {/* Main Monitoring Grid */}
                    <div className="lg:col-span-8 space-y-12">
                        
                        {/* Service Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {data?.services?.map((svc, idx) => (
                                <motion.div 
                                    key={svc.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                >
                                    <Card padding="none" className="bg-black border-white/10 hover:border-cyan-500/40 transition-all duration-500 rounded-[2.5rem] overflow-hidden group">
                                        <div className="p-8 space-y-8">
                                            <div className="flex justify-between items-start">
                                                <div className="p-4 bg-white/5 rounded-2xl text-cyan-500 group-hover:bg-cyan-500 group-hover:text-black transition-all shadow-inner">
                                                    {svc.id === 'quantum' && <Zap className="w-6 h-6" />}
                                                    {svc.id === 'plasticity' && <Activity className="w-6 h-6" />}
                                                    {svc.id === 'swarm' && <Radio className="w-6 h-6" />}
                                                    {svc.id === 'lnn' && <Binary className="w-6 h-6" />}
                                                </div>
                                                <Badge className="bg-cyan-500/10 text-cyan-500 border-cyan-500/20 text-[8px] font-black uppercase">NODE_{svc.id.toUpperCase()}</Badge>
                                            </div>

                                            <div>
                                                <h3 className="text-2xl font-black italic manga-font uppercase mb-1 tracking-tighter">{svc.name}</h3>
                                                <div className="flex items-center gap-2">
                                                    <div className={`w-1.5 h-1.5 rounded-full ${svc.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'} animate-pulse`} />
                                                    <span className="text-[10px] font-black uppercase opacity-40 tracking-widest">{svc.status}</span>
                                                </div>
                                            </div>

                                            {/* Load Bar */}
                                            <div className="space-y-3">
                                                <div className="flex justify-between text-[8px] font-black uppercase tracking-widest opacity-30">
                                                    <span>Computational Load</span>
                                                    <span>{svc.load}%</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                    <motion.div 
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${svc.load}%` }}
                                                        className={`h-full ${svc.load > 70 ? 'bg-red-500' : 'bg-cyan-500'} shadow-[0_0_10px_rgba(6,182,212,0.5)]`}
                                                    />
                                                </div>
                                            </div>

                                            {/* Metrics Mini-Grid */}
                                            <div className="grid grid-cols-2 gap-4">
                                                {Object.entries(svc.metrics).map(([key, val]) => (
                                                    <div key={key} className="bg-white/5 p-3 rounded-xl border border-white/5">
                                                        <span className="block text-[7px] font-black uppercase opacity-20 mb-1">{key.replace('_', ' ')}</span>
                                                        <span className="text-xs font-black italic">{String(val)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        
                                        <button className="w-full py-4 bg-white/5 hover:bg-cyan-500 hover:text-black text-[9px] font-black uppercase tracking-[0.3em] transition-all border-t border-white/5">
                                            Manage Neural Node <ChevronRight className="inline w-3 h-3 ml-2" />
                                        </button>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>

                        {/* System Specs Overlay */}
                        <div className="p-10 bg-cyan-500/5 border border-cyan-500/20 rounded-[3rem] relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-8 opacity-10">
                                <Shield className="w-24 h-24 text-cyan-500" />
                            </div>
                            <h4 className="text-2xl font-black italic manga-font uppercase mb-6 tracking-tighter">Cluster Security : <span className="text-emerald-500">MAXIMUM</span></h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                                <div className="space-y-1">
                                    <span className="text-[8px] font-black uppercase opacity-30 tracking-widest block">Uptime</span>
                                    <span className="text-sm font-black italic">99.998%</span>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[8px] font-black uppercase opacity-30 tracking-widest block">Guardrails</span>
                                    <span className="text-sm font-black italic text-emerald-500 text-glow-emerald">ACTIVE</span>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[8px] font-black uppercase opacity-30 tracking-widest block">Encryption</span>
                                    <span className="text-sm font-black italic">AES-768-Q</span>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[8px] font-black uppercase opacity-30 tracking-widest block">Sync Rate</span>
                                    <span className="text-sm font-black italic">1.2ms</span>
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* Sidebar: Activity & Global Stats */}
                    <div className="lg:col-span-4 space-y-12">
                        
                        {/* System Logs */}
                        <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl h-full flex flex-col">
                            <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-cyan-500" /> Neural Event Log
                            </h3>
                            
                            <div className="space-y-6 flex-grow overflow-y-auto custom-scrollbar pr-4">
                                {data?.events?.map((event, i) => (
                                    <div key={i} className="flex gap-4 border-l-2 border-white/5 pl-4 py-1 hover:border-cyan-500/40 transition-colors group">
                                        <div className="shrink-0 pt-1">
                                            <div className={`w-2 h-2 rounded-full ${i === 0 ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]' : 'bg-white/20'}`} />
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2">
                                                <span className="text-[7px] font-black text-cyan-500/60 uppercase">{new Date(event.time).toLocaleTimeString()}</span>
                                                <Badge className="text-[6px] py-0 px-1.5 opacity-40">{event.type}</Badge>
                                            </div>
                                            <p className="text-[10px] font-bold leading-relaxed opacity-60 group-hover:opacity-100 transition-opacity">
                                                {event.msg}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-8 pt-8 border-t border-white/5">
                                <div className="p-4 bg-red-500/5 rounded-2xl border border-red-500/10 flex items-center gap-4">
                                    <AlertTriangle className="w-5 h-5 text-red-500 animate-pulse" />
                                    <span className="text-[9px] font-black uppercase text-red-500/60 tracking-widest">No critical anomalies detected in the last 24h.</span>
                                </div>
                            </div>
                        </Card>

                        {/* Hardware Visualization Placeholder */}
                        <Card padding="none" className="bg-black/40 border-white/5 rounded-[2.5rem] p-8 space-y-6">
                            <div className="flex justify-between items-center">
                                <h4 className="text-[10px] font-black uppercase tracking-widest opacity-30">Infrastructure Map</h4>
                                <Database className="w-3 h-3 opacity-20" />
                            </div>
                            <div className="aspect-square bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] rounded-2xl flex items-center justify-center border border-white/5 relative group">
                                <div className="absolute inset-0 bg-cyan-500/5 group-hover:bg-cyan-500/10 transition-colors" />
                                <Cpu className="w-20 h-20 text-cyan-500 opacity-20 group-hover:scale-110 transition-transform" />
                                {/* Scanning line effect */}
                                <div className="absolute top-0 left-0 w-full h-1 bg-cyan-500/20 animate-scan" />
                            </div>
                            <div className="flex justify-between items-center text-[8px] font-black uppercase tracking-widest opacity-20 italic">
                                <span>Edge Region: europe-west9</span>
                                <span>Multi-Tenant: True</span>
                            </div>
                        </Card>
                    </div>

                </div>

                {/* Background HUD elements */}
                <div className="fixed top-0 right-0 w-full h-full pointer-events-none -z-10 opacity-[0.03]">
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120vw] h-[120vh] border-[1px] border-white rounded-full" />
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vh] border-[1px] border-white rounded-full" />
                     <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:100px_100px]" />
                </div>

            </div>
            
            <style>{`
                .text-glow-cyan {
                    text-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
                }
                .text-glow-emerald {
                    text-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
                }
                @keyframes scan {
                    0% { top: 0; }
                    100% { top: 100%; }
                }
                .animate-scan {
                    animation: scan 4s linear infinite;
                }
            `}</style>
        </AnimatedPage>
    );
};

export default SingularityCommandCenterPage;
