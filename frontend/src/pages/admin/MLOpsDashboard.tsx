import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Settings, 
  ShieldAlert, 
  Activity, 
  BarChart2, 
  Database, 
  ShieldCheck,
  ArrowRight,
  Brain,
  Zap,
  Terminal,
  LayoutGrid
} from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const MLOpsDashboard: React.FC = () => {
  const adminModules = [
    {
      title: "Curation DPO",
      desc: "Corrigez et validez les paires de préférences IA pour l'alignement du modèle.",
      icon: ShieldAlert,
      path: "/admin/dpo-curation/",
      color: "text-red-500",
      count: 12,
      status: "Attention"
    },
    {
      title: "Santé Système",
      desc: "Monitoring en temps réel de Brain API, Redis, Celery et PostgreSQL.",
      icon: Activity,
      path: "/admin/health/",
      color: "text-cyan-500",
      status: "Stable"
    },
    {
      title: "Évaluation IA",
      desc: "Benchmarks de régression et tests de qualité sémantique automatisés.",
      icon: BarChart2,
      path: "/admin/ai_eval/",
      color: "text-purple-500",
      status: "Active"
    },
    {
      title: "Gold Dataset",
      desc: "Édition et validation des données d'entraînement haute fidélité (SOTA).",
      icon: Database,
      path: "/admin/gold-dataset/",
      color: "text-amber-500",
      status: "Actif"
    },
    {
      title: "Curation IA",
      desc: "Validez les corrections structurelles suggérées par les agents de guérison (Graph Healers).",
      icon: LayoutGrid,
      path: "/admin/curation/",
      color: "text-cyan-500",
      status: "IA-Guérison"
    },
    {
      title: "Knowledge Graph",
      desc: "Gestion de Neo4j, résolution de conflits et audit de relations.",
      icon: Zap,
      path: "/graph/",
      color: "text-purple-500",
      status: "Maintenance"
    },
    {
      title: "Open Ledger",
      desc: "Dashboard de transparence publique, éthique et coûts IA.",
      icon: ShieldCheck,
      path: "/transparency/",
      color: "text-emerald-500",
      status: "Public"
    },
    {
      title: "Benchmarks SOTA",
      desc: "Suivi des performances mondiales des modèles (ELO score, MMLU accuracy).",
      icon: Trophy,
      path: "/admin/sota-benchmarks/",
      color: "text-cyan-500",
      status: "Global"
    },
    {
      title: "Graph Healer",
      desc: "Analyse et résolution des conflits de lore dans Neo4j.",
      icon: Network,
      path: "/admin/graph-debugger/",
      color: "text-purple-500",
      status: "Beta"
    },
    {
      title: "Dynamic Budget TTC",
      desc: "Monitoring de la consommation et de l'efficacité cognitive (Test-Time Compute).",
      icon: Brain,
      path: "/admin/ttc-monitoring/",
      color: "text-yellow-500",
      status: "Actif"
    }
  ];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-6">
            <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-black uppercase tracking-widest text-cyan-500 mb-4">
                    <Terminal className="w-3 h-3" /> Command Center v4.0
                </div>
                <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
                    MLOPS <span className="text-cyan-500 text-glow">DASHBOARD</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] leading-relaxed">
                    Pilotage de l'infrastructure neuronale et alignement éthique.
                </p>
            </div>
            
            <div className="flex gap-4">
                <div className="text-right">
                    <p className="text-[10px] font-black uppercase opacity-40 mb-1">Inference Cluster</p>
                    <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">H100 x 8 ONLINE</Badge>
                </div>
            </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {adminModules.map((m) => (
                <Link key={m.title} to={m.path} className="no-underline group">
                    <Card padding="lg" className="h-full bg-gray-900/40 border-white/5 hover:border-cyan-500/30 transition-all duration-300">
                        <div className="flex justify-between items-start mb-6">
                            <div className={`p-3 rounded-xl bg-white/5 group-hover:scale-110 transition-transform ${m.color}`}>
                                <m.icon className="w-6 h-6" />
                            </div>
                            <Badge variant="neutral" className="text-[9px] uppercase font-black">{m.status}</Badge>
                        </div>
                        <h3 className="text-lg font-black italic manga-font uppercase mb-2 group-hover:text-cyan-400 transition-colors">{m.title}</h3>
                        <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider mb-6">
                            {m.desc}
                        </p>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1 text-cyan-500 text-[10px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
                                Accéder <ArrowRight className="w-3 h-3" />
                            </div>
                            {m.count && <span className="text-xs font-black text-red-500">{m.count}</span>}
                        </div>
                    </Card>
                </Link>
            ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Quick Metrics */}
            <Card padding="lg" className="lg:col-span-2 bg-black border-white/10 shadow-2xl">
                <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" /> Métriques d'Inférence (Global)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="space-y-2">
                        <p className="text-[10px] font-black uppercase opacity-30">Latence Moyenne</p>
                        <div className="flex items-end gap-2">
                            <span className="text-4xl font-black italic manga-font text-white">420</span>
                            <span className="text-xs font-black opacity-30 mb-1">ms</span>
                        </div>
                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                            <div className="w-[40%] h-full bg-cyan-500" />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <p className="text-[10px] font-black uppercase opacity-30">Taux de Hallucination</p>
                        <div className="flex items-end gap-2">
                            <span className="text-4xl font-black italic manga-font text-emerald-400">0.8</span>
                            <span className="text-xs font-black opacity-30 mb-1">%</span>
                        </div>
                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                            <div className="w-[15%] h-full bg-emerald-500" />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <p className="text-[10px] font-black uppercase opacity-30">Appels / min</p>
                        <div className="flex items-end gap-2">
                            <span className="text-4xl font-black italic manga-font text-amber-400">12.5k</span>
                        </div>
                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                            <div className="w-[70%] h-full bg-amber-500" />
                        </div>
                    </div>
                </div>
            </Card>

            {/* Neural Summary */}
            <Card padding="lg" className="bg-cyan-600 text-white border-none flex flex-col justify-between">
                <div>
                    <Brain className="w-12 h-12 mb-6" />
                    <h3 className="text-2xl font-black italic manga-font uppercase mb-4 leading-tight">État de la Singularité</h3>
                    <p className="text-sm font-bold italic opacity-90 leading-relaxed uppercase">
                        Les poids synaptiques globaux sont stables. Le cluster DPO a ingéré 4.2k corrections cette semaine, augmentant la précision sémantique de 12%.
                    </p>
                </div>
                <div className="mt-8 pt-8 border-t border-white/20 flex justify-between items-center">
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-60">IA Trust Score</span>
                    <span className="text-4xl font-black italic manga-font font-glow">98.4%</span>
                </div>
            </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default MLOpsDashboard;


