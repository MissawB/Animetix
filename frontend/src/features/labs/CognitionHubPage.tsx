import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Link } from 'react-router-dom';
import { 
  Brain, 
  Fingerprint, 
  GitBranch, 
  ArrowRight, 
  Terminal,
  Activity,
  Zap
} from 'lucide-react';

const cognitiveModules = [
  {
    id: 'archetype',
    title: 'Archetype Nexus',
    sub: 'SYNAPTIC CONVERGENCE',
    desc: 'Visualisez votre position dans l\'espace latent des fans et la convergence de vos traits psychographiques.',
    icon: Brain,
    url: '/social/archetype-nexus/',
    color: 'text-purple-500',
    bg: 'from-purple-500/20 to-transparent',
    badge: 'Latent Space'
  },
  {
    id: 'memory',
    title: 'Neuro-Memory',
    sub: 'SEMANTIC IMPRINT',
    desc: 'Gérez l\'empreinte sémantique que vous laissez sur l\'IA et auditez vos vecteurs de préférence en temps réel.',
    icon: Fingerprint,
    url: '/social/neuro-memory/',
    color: 'text-emerald-500',
    bg: 'from-emerald-500/20 to-transparent',
    badge: 'Cognitive Audit'
  },
  {
    id: 'simulator',
    title: 'Counterfactual Simulator',
    sub: 'TIMELINE OPTIMIZATION',
    desc: 'Explorez les mondes possibles de vos interactions et calculez le regret contrefactuel minimum.',
    icon: GitBranch,
    url: '/search/counterfactual/',
    color: 'text-blue-500',
    bg: 'from-blue-500/20 to-transparent',
    badge: 'Game Theory'
  }
];

const CognitionHubPage: React.FC = () => {
  const { t } = useTranslation();

  const particleConfig = useMemo(() => [...Array(20)].map(() => ({
    left: Math.random() * 100,
    top: Math.random() * 100,
    duration: 10 + Math.random() * 10,
    delay: Math.random() * 10
  })), []);

  return (
    <AnimatedPage>
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden bg-[#020202]">
        {/* Particles */}
        <div className="fixed inset-0 pointer-events-none z-0">
          {particleConfig.map((p, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-white rounded-full opacity-20"
              style={{
                left: `${p.left}%`,
                top: `${p.top}%`,
                animation: `float ${p.duration}s infinite linear`,
                animationDelay: `${p.delay}s`,
              }}
            />
          ))}
        </div>

        {/* Ambient Glows */}
        <div className="fixed inset-0 pointer-events-none z-0 opacity-10">
          <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-purple-600/20 blur-[150px] rounded-full" />
          <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-emerald-600/20 blur-[150px] rounded-full" />
        </div>

        <header className="text-center mb-24 z-10 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-[0.3em] text-purple-500 mb-8">
            <Terminal className="w-3 h-3" /> Neural Interface Protocol v7.0
          </div>
          <h1 className="text-8xl font-black italic manga-font uppercase tracking-tighter text-white mb-6">
            COGNITION <span className="text-purple-600 text-glow">CORE</span>
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed max-w-2xl mx-auto">
            Fusion de l'identité numérique, de la mémoire artificielle et de la simulation de futurs possibles.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 z-10 max-w-7xl w-full">
          {cognitiveModules.map((module) => (
            <Link key={module.id} to={module.url} className="no-underline group">
              <Card padding="none" className="h-full bg-navy-950/40 border-white/5 hover:border-purple-500/30 transition-all duration-500 overflow-hidden relative shadow-2xl">
                <div className={`absolute inset-0 bg-gradient-to-br ${module.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                
                <div className="p-10 relative z-10 flex flex-col h-full justify-between">
                    <div>
                        <div className="flex justify-between items-start mb-10">
                            <div className={`p-4 rounded-2xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${module.color}`}>
                                <module.icon className="w-8 h-8" />
                            </div>
                            <Badge variant="neutral" className="bg-white/5 border-none text-[8px] font-black italic uppercase tracking-widest">{module.badge}</Badge>
                        </div>
                        <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${module.color} mb-2`}>{module.sub}</p>
                        <h3 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter group-hover:text-white transition-colors">{module.title}</h3>
                        <p className="text-xs font-bold opacity-40 uppercase leading-relaxed tracking-wider mb-10 group-hover:opacity-60 transition-opacity">
                            {module.desc}
                        </p>
                    </div>
                    
                    <div className="flex items-center justify-between mt-auto pt-8 border-t border-white/5">
                        <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${module.color} opacity-0 group-hover:opacity-100 transition-all transform translate-x-[-10px] group-hover:translate-x-0 duration-500`}>
                            INITIALIZE <ArrowRight className="inline w-3 h-3 ml-2" />
                        </span>
                    </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Cognitive Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-24 z-10 w-full max-w-7xl">
            <Card padding="lg" className="bg-black/40 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-blue-400">
                    <Activity className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">CFR Resolution</p>
                    <p className="text-lg font-black italic uppercase manga-font">Regret Minimizer v2</p>
                </div>
            </Card>
            <Card padding="lg" className="bg-black/40 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-purple-400">
                    <Brain className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">Latent Mapping</p>
                    <p className="text-lg font-black italic uppercase manga-font">High-Dim Projection</p>
                </div>
            </Card>
            <Card padding="lg" className="bg-black/40 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-orange-400">
                    <Zap className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">Synaptic Sync</p>
                    <p className="text-lg font-black italic uppercase manga-font">Real-time Imprint</p>
                </div>
            </Card>
        </div>

        <footer className="mt-24 opacity-20 text-center z-10 max-w-4xl">
          <p className="text-[9px] font-bold uppercase tracking-[0.5em] italic leading-relaxed">
            Le Cognition Hub unifie les vecteurs d'identité et de décision. <br />
            Les données traitées ici servent à affiner les modèles de recommandation neuro-symboliques sans compromettre l'étanchéité de la vie privée numérique.
          </p>
        </footer>
      </div>

      <style>{`
        @keyframes float {
          0% { transform: translateY(0) rotate(0deg); opacity: 0; }
          50% { opacity: 0.5; }
          100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
        }
      `}</style>
    </AnimatedPage>
  );
};

export default CognitionHubPage;
