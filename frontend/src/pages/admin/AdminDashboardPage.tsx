import React from 'react';
import { Shield, Users, Activity, Brain, Database, BarChart3, Clock, ArrowRight, Workflow, Target, Network, ListChecks, Coins, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from "../../components/ui/Card";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const AdminDashboardPage: React.FC = () => {
  const adminModules = [
    {
      title: 'User Management',
      desc: 'Gérer les comptes, les droits admin et les accès.',
      icon: <Users className="w-8 h-8 text-blue-500" />,
      path: '/admin/users/',
      color: 'blue'
    },
    {
      title: 'AI Quality Control',
      desc: 'Surveiller la précision et les hallucinations de l\'IA.',
      icon: <Brain className="w-8 h-8 text-purple-500" />,
      path: '/admin/eval/',
      color: 'purple'
    },
    {
      title: 'System Health',
      desc: 'État des services, latence et performances.',
      icon: <Activity className="w-8 h-8 text-emerald-500" />,
      path: '/admin/health/',
      color: 'emerald'
    },
    {
      title: 'Data Curation',
      desc: 'Valider et corriger les données du graphe.',
      icon: <Database className="w-8 h-8 text-cyan-500" />,
      path: '/admin/gold-dataset/',
      color: 'cyan'
    },
    {
      title: 'TTC Monitoring',
      desc: 'Budget de tokens et efficacité de l\'inférence.',
      icon: <Clock className="w-8 h-8 text-orange-500" />,
      path: '/admin/ttc-monitoring/',
      color: 'orange'
    },
    {
      title: 'SOTA Benchmarks',
      desc: 'Comparaison des performances modèles.',
      icon: <BarChart3 className="w-8 h-8 text-pink-500" />,
      path: '/admin/sota-benchmark/',
      color: 'pink'
    },
    {
      title: 'MLOps Dashboard',
      desc: 'Supervision des pipelines d\'entraînement et déploiement.',
      icon: <Workflow className="w-8 h-8 text-indigo-500" />,
      path: '/admin/mlops/',
      color: 'indigo'
    },
    {
      title: 'Observability Console',
      desc: 'Analyser le drift d\'archétype et ajuster les guardrails.',
      icon: <Activity className="w-8 h-8 text-purple-500" />,
      path: '/admin/observability/',
      color: 'purple'
    },
    {
      title: 'DSPy Optimizer',
      desc: 'Optimisation automatique des prompts via DSPy.',
      icon: <Target className="w-8 h-8 text-red-500" />,
      path: '/admin/dspy/',
      color: 'red'
    },
    {
      title: 'Graph Debugger',
      desc: 'Inspection visuelle et débogage du graphe Neo4j.',
      icon: <Network className="w-8 h-8 text-emerald-400" />,
      path: '/admin/graph-debugger/',
      color: 'emerald'
    },
    {
      title: 'Admin Curation',
      desc: 'Interface avancée de validation humaine (RLHF).',
      icon: <ListChecks className="w-8 h-8 text-amber-500" />,
      path: '/admin/curation/',
      color: 'amber'
    },
    {
      title: 'Financial Dashboard',
      desc: 'Calculer les coûts IA et égaliser avec les pubs/dons.',
      icon: <Coins className="w-8 h-8 text-yellow-500" />,
      path: '/admin/financials/',
      color: 'yellow'
    },
    {
      title: 'Economic Audit',
      desc: 'Analyse de la masse monétaire et de l\'inflation des Berrix.',
      icon: <TrendingUp className="w-8 h-8 text-emerald-500" />,
      path: '/admin/economics/',
      color: 'emerald'
    }
  ];

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-16">
          
          <div className="mb-16">
            <div className="flex items-center gap-3 text-blue-600 dark:text-blue-400 font-black uppercase tracking-widest text-xs mb-4">
              <Shield size={20} /> Accès Administrateur Sécurisé
            </div>
            <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
              COMMAND <span className="text-blue-600 dark:text-blue-400">CENTER</span>
            </h1>
            <p className="text-gray-600 dark:text-gray-400 font-bold uppercase tracking-widest mt-4">
              Supervision globale de l'écosystème Animetix
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {adminModules.map((module) => (
              <Link key={module.path} to={module.path} className="no-underline group">
                <Card padding="lg" className="h-full hover:scale-105 transition-all duration-300 border-none shadow-xl bg-white dark:bg-[#0f0f1a] relative overflow-hidden">
                  <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500">
                    {module.icon}
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-white/5 w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-inner border border-gray-100 dark:border-white/5 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    {module.icon}
                  </div>
                  
                  <h3 className="text-2xl font-black italic manga-font uppercase mb-3 text-black dark:text-white group-hover:text-blue-600 transition-colors">
                    {module.title}
                  </h3>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-medium leading-relaxed mb-6">
                    {module.desc}
                  </p>
                  
                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    Accéder au module <ArrowRight size={12} />
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <div className="mt-16 pt-12 border-t border-gray-100 dark:border-white/5 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] text-gray-500 dark:text-gray-400">
              Animetix Admin Engine v2.4.0 • Node Status: <span className="text-green-700 dark:text-green-400">Optimal</span>
            </p>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AdminDashboardPage;
