import React from 'react';
import _Plot from 'react-plotly.js';
import { Data } from 'plotly.js';
import { 
  Layers, 
  Activity, 
  Clock, 
  ChevronRight, 
  Target,
  BarChart3,
  Cpu,
  Fingerprint,
  TrendingUp
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion } from 'framer-motion';

// Fix for react-plotly.js type/import compatibility
const Plot = (_Plot as unknown as { default: React.ComponentType<Record<string, unknown>> }).default || (_Plot as React.ComponentType<Record<string, unknown>>);

interface StatBarProps {
  label: string;
  value: number;
  color: string;
}

const StatBar: React.FC<StatBarProps> = ({ label, value, color }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-end">
      <span className="text-[9px] font-black uppercase tracking-widest opacity-40">{label}</span>
      <span className="text-xs font-black italic">{Math.round(value * 100)}%</span>
    </div>
    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${value * 100}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
        className={`h-full ${color}`} 
      />
    </div>
  </div>
);

interface ArchetypeData {
  id: string;
  aura_type: string;
  intensity: number;
  accent: string;
}

interface CognitiveStats {
  shonen_affinity: number;
  seinen_affinity: number;
  logic_consistency: number;
  memory_depth: number;
}

interface RecentSignal {
  context: string;
  is_positive: boolean;
}

interface DriftHistoryEntry {
  date: string;
  shonen: number;
  seinen: number;
}

interface ArchetypeNexusResponse {
  archetype: ArchetypeData;
  logical_rules: string[];
  recent_signals: RecentSignal[];
  cognitive_stats: CognitiveStats;
  drift_history: DriftHistoryEntry[];
}

const ArchetypeNexusPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery<ArchetypeNexusResponse>({
    queryKey: ['archetype-nexus'],
    queryFn: () => apiClient('/api/v1/cognition/archetype-nexus/'),
  });

  if (isLoading) return (
    <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center">
      <CardSkeleton />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 w-full max-w-7xl px-6">
          <CardSkeleton /><CardSkeleton /><CardSkeleton />
      </div>
    </div>
  );

  if (isError || !data) return (
    <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center text-center">
        <h2 className="text-3xl font-black text-red-500 italic uppercase">Défaillance Cognitive</h2>
        <p className="text-white/40 mt-4 uppercase font-bold tracking-widest">Impossible de synchroniser le profil neuronal.</p>
    </div>
  );

  const { archetype, logical_rules, recent_signals, cognitive_stats, drift_history } = data;

  const driftPlotData = drift_history && drift_history.length > 0 ? [
    {
      x: drift_history.map((h) => h.date),
      y: drift_history.map((h) => h.shonen),
      name: 'Shonen',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#f97316', width: 3, shape: 'spline' },
      marker: { size: 8, color: '#f97316' }
    },
    {
      x: drift_history.map((h) => h.date),
      y: drift_history.map((h) => h.seinen),
      name: 'Seinen',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#a855f7', width: 3, shape: 'spline' },
      marker: { size: 8, color: '#a855f7' }
    }
  ] : [];

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          
          {/* Header Profil Neuronal */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-gray-500 mb-4">
                <Fingerprint className="w-3 h-3" /> Digital Consciousness
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                ARCHETYPE <span className="text-blue-500 text-glow">NEXUS</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Visualisation de votre empreinte sémantique et de vos biais narratifs déduits par l'IA.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
            
            {/* Colonne Gauche: Archétype Dominant & Aura */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="none" className="bg-black border-white/10 overflow-hidden rounded-[3rem] relative group shadow-2xl">
                    {/* Dynamic Aura Background */}
                    <div 
                        className="absolute inset-0 opacity-20 transition-opacity group-hover:opacity-40"
                        style={{ 
                            background: `radial-gradient(circle at center, ${archetype.accent} 0%, transparent 70%)`,
                            filter: 'blur(40px)'
                        }} 
                    />
                    
                    <div className="relative z-10 p-10 text-center">
                        <div className="w-48 h-48 mx-auto mb-8 relative">
                            <div 
                                className="absolute inset-0 rounded-full animate-pulse opacity-50"
                                style={{ boxShadow: `0 0 50px ${archetype.accent}` }}
                            />
                            <div className="w-full h-full bg-navy-900 border-4 border-white/10 rounded-full flex items-center justify-center relative overflow-hidden">
                                <Activity className="w-20 h-20 text-white opacity-20" />
                                <div 
                                    className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-blue-500/20 to-transparent h-1/2 animate-scan"
                                />
                            </div>
                        </div>

                        <Badge 
                            variant="primary" 
                            style={{ backgroundColor: archetype.accent }}
                            className="mb-4 text-[10px] font-black italic uppercase tracking-widest py-2 px-6"
                        >
                            {archetype.id.replace('_', ' ')}
                        </Badge>
                        
                        <h2 className="text-4xl font-black italic manga-font uppercase mb-2 tracking-tighter">Archétype Maître</h2>
                        <p className="text-[10px] font-bold opacity-40 uppercase tracking-widest leading-relaxed">
                            Aura: {archetype.aura_type} ({Math.round(archetype.intensity * 100)}% d'intensité)
                        </p>
                    </div>

                    <div className="border-t border-white/5 bg-white/5 p-8 grid grid-cols-2 gap-4">
                        <div className="text-center">
                            <p className="text-[8px] font-black opacity-30 uppercase mb-1">Stabilité</p>
                            <p className="text-xl font-black italic text-blue-500">92%</p>
                        </div>
                        <div className="text-center border-l border-white/5">
                            <p className="text-[8px] font-black opacity-30 uppercase mb-1">Convergence</p>
                            <p className="text-xl font-black italic text-emerald-500">HAUTE</p>
                        </div>
                    </div>
                </Card>

                <Card padding="lg" className="bg-navy-900/40 border-white/5">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-blue-500" /> Profil Neuronal
                    </h3>
                    <div className="space-y-6">
                        <StatBar label="Affinité Shonen" value={cognitive_stats.shonen_affinity} color="bg-orange-500" />
                        <StatBar label="Complexité Seinen" value={cognitive_stats.seinen_affinity} color="bg-purple-500" />
                        <StatBar label="Cohérence Logique" value={cognitive_stats.logic_consistency} color="bg-emerald-500" />
                        <StatBar label="Profondeur Mémoire" value={Math.min(cognitive_stats.memory_depth / 50, 1)} color="bg-blue-500" />
                    </div>
                </Card>
            </div>

            {/* Colonne Droite: Graphique de Drift & Z3 Rules */}
            <div className="lg:col-span-8 space-y-8 flex flex-col">
                
                {/* Archetype Drift Evolution (Le Graphique) */}
                <Card padding="lg" className="bg-black border-white/5 overflow-hidden flex-grow flex flex-col">
                    <header className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-black italic manga-font uppercase flex items-center gap-3">
                            <TrendingUp className="w-5 h-5 text-emerald-500" /> Archetype Drift Evolution
                        </h3>
                        <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px]">TIME-SERIES ALPHA</Badge>
                    </header>
                    
                    <div className="flex-grow min-h-[300px] relative">
                        {drift_history && drift_history.length > 0 ? (
                            <Plot
                                data={driftPlotData as unknown as Data[]}
                                layout={{
                                    autosize: true,
                                    height: 300,
                                    paper_bgcolor: 'rgba(0,0,0,0)',
                                    plot_bgcolor: 'rgba(0,0,0,0)',
                                    margin: { l: 40, r: 20, b: 40, t: 10 },
                                    showlegend: true,
                                    legend: { font: { color: '#64748b', size: 10 }, orientation: 'h', y: -0.2 },
                                    xaxis: {
                                        gridcolor: 'rgba(255,255,255,0.05)',
                                        tickfont: { color: '#475569', size: 8 },
                                        showgrid: true,
                                    },
                                    yaxis: {
                                        gridcolor: 'rgba(255,255,255,0.05)',
                                        tickfont: { color: '#475569', size: 8 },
                                        range: [0, 1.1],
                                        showgrid: true,
                                    }
                                }}
                                config={{ responsive: true, displayModeBar: false }}
                                style={{ width: '100%' }}
                            />
                        ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-center opacity-20 border-2 border-dashed border-white/5 rounded-3xl">
                                <TrendingUp className="w-12 h-12 mb-4" />
                                <p className="text-[10px] font-black uppercase tracking-widest">Historique insuffisant pour projection</p>
                            </div>
                        )}
                    </div>
                </Card>

                {/* Z3 Deduced Rules */}
                <Card padding="lg" className="bg-black border-blue-500/20 shadow-[0_0_40px_rgba(59,130,246,0.1)]">
                    <header className="flex justify-between items-start mb-6">
                        <div>
                            <h3 className="text-2xl font-black italic manga-font uppercase mb-1 flex items-center gap-3">
                                <Cpu className="w-6 h-6 text-blue-500" /> Modèle Logique SAT (Z3)
                            </h3>
                            <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest">Contraintes formelles déduites de vos interactions.</p>
                        </div>
                        <div className="flex gap-2">
                            <Button 
                                as={Link}
                                to="/social/neuro-memory/"
                                variant="outline"
                                className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10 py-1 px-4 rounded-xl text-[8px] font-black uppercase tracking-widest h-auto"
                            >
                                Gérer <ChevronRight className="ml-1 w-3 h-3" />
                            </Button>
                            <Badge variant="neutral" className="bg-blue-500/10 text-blue-500 border-blue-500/20">RESOLVED</Badge>
                        </div>
                    </header>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {logical_rules.map((rule: string, i: number) => (
                            <motion.div 
                                key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4 group hover:border-blue-500/40 transition-colors"
                            >
                                <div className="w-8 h-8 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500 font-mono text-[10px] font-black group-hover:scale-110 transition-transform">
                                    {i + 1}
                                </div>
                                <code className="text-xs font-bold text-blue-100 opacity-80 uppercase tracking-wider">{rule}</code>
                            </motion.div>
                        ))}
                    </div>
                </Card>
            </div>
        </div>

        {/* Bottom Section: Signals */}
        <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
             {/* Recent Signals (Memory Timeline) */}
             <Card padding="lg" className="bg-navy-900/40 border-white/5">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-10 tracking-widest flex items-center gap-2">
                        <Clock className="w-4 h-4 text-emerald-500" /> Signaux de Mémoire Épisodique
                    </h3>
                    <div className="space-y-6 relative">
                        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-white/5" />
                        
                        {recent_signals.map((sig, i) => (
                            <div key={i} className="flex gap-6 relative group">
                                <div className={`w-10 h-10 rounded-2xl shrink-0 flex items-center justify-center relative z-10 transition-transform group-hover:scale-110 ${
                                    sig.is_positive ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'
                                }`}>
                                    {sig.is_positive ? <Target className="w-5 h-5" /> : <Layers className="w-5 h-5" />}
                                </div>
                                <div className="flex-grow pt-2">
                                    <div className="flex justify-between items-center mb-1">
                                        <p className={`text-[10px] font-black uppercase tracking-widest ${sig.is_positive ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {sig.is_positive ? 'SIGNAL POSITIF' : 'SIGNAL NÉGATIF'}
                                        </p>
                                        <span className="text-[8px] opacity-20 font-mono">STEP_0{recent_signals.length - i}</span>
                                    </div>
                                    <p className="text-sm font-bold opacity-80 line-clamp-1 italic group-hover:line-clamp-none transition-all">"{sig.context}"</p>
                                </div>
                            </div>
                        ))}

                        {recent_signals.length === 0 && (
                            <div className="text-center py-12 opacity-10 italic uppercase font-black tracking-widest">
                                Aucun signal indexé
                            </div>
                        )}
                    </div>
                </Card>
        </div>

        {/* Global Warning / Alpha Status */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic">
                Avertissement : Les déductions neuro-symboliques sont basées sur des modèles stochastiques résolus en temps réel. <br />
                Le drift d'archétype est recalculé après chaque session de forge ou de débat.
            </p>
        </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default ArchetypeNexusPage;


