import React from 'react';
import { 
  Brain, 
  Network, 
  Cpu, 
  Zap, 
  Layers, 
  Fingerprint, 
  Scale, 
  Activity, 
  Search, 
  Database,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
  Gamepad2,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const ArchetypeGuidePage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white overflow-hidden">
        {/* Animated Background Gradients */}
        <div className="absolute top-0 left-0 w-full h-[1000px] pointer-events-none">
            <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 blur-[150px] rounded-full animate-pulse" />
            <div className="absolute bottom-0 right-[-5%] w-[40%] h-[40%] bg-anime-accent/5 blur-[120px] rounded-full" />
        </div>

        {/* Hero Section */}
        <section className="relative pt-32 pb-24 px-6 text-center border-b border-white/5">
            <div className="max-w-4xl mx-auto relative z-10">
                <Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-12 no-underline group">
                    <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Nexus
                </Link>
                
                <div className="inline-flex items-center gap-3 px-6 py-2.5 rounded-full bg-navy-900/50 border border-white/10 text-anime-accent text-[10px] font-black uppercase tracking-[0.3em] mb-10 shadow-2xl backdrop-blur-xl">
                    <Brain className="w-4 h-4 animate-pulse" /> Guide Scientifique du Nexus
                </div>
                
                <h1 className="text-8xl font-black italic manga-font tracking-tighter uppercase mb-8 leading-none">
                    L'INTELLIGENCE <br />
                    <span className="text-blue-500 text-glow">NEURO-SYMBOLIQUE</span>
                </h1>
                
                <p className="text-xl text-gray-400 font-bold uppercase tracking-widest leading-relaxed max-w-3xl mx-auto italic">
                    Découvrez la technologie révolutionnaire qui permet à Animetix de comprendre vos goûts, de résoudre des paradoxes et de fusionner des univers.
                </p>
            </div>
        </section>

        <main className="max-w-6xl mx-auto px-6 py-24 space-y-40">
            {/* The Core Concept */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                <div className="space-y-8">
                    <h2 className="text-4xl font-black italic uppercase manga-font tracking-tight flex items-center gap-4">
                        <Layers className="w-10 h-10 text-blue-500" /> Le Cycle Cognitif
                    </h2>
                    <p className="text-lg text-gray-400 leading-relaxed font-medium italic">
                        Contrairement aux IA classiques qui se contentent de prédire le mot suivant, Animetix utilise un 
                        <span className="text-white"> cycle cognitif en 6 phases</span>. 
                        C'est l'alliance entre la force brute du Deep Learning et la rigueur de la logique mathématique.
                    </p>
                    <div className="space-y-4">
                        <StepItem index="01" title="Ingestion Multimodale" desc="Scraping temps réel des métadonnées (MAL, IGDB, TV Tropes)." />
                        <StepItem index="02" title="Stockage Hybride" desc="Combinaison SQL, Graphes Neo4j et Bases Vectorielles." />
                        <StepItem index="03" title="RAG Augmenté" desc="Recherche sémantique via Jina-v3 et Matryoshka Embeddings." />
                    </div>
                </div>
                <div className="relative group">
                    <div className="absolute -inset-4 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-[4rem] blur-2xl opacity-50 group-hover:opacity-100 transition-opacity duration-700" />
                    <Card className="relative bg-black/40 border-white/10 rounded-[3rem] p-12 backdrop-blur-2xl">
                        <div className="grid grid-cols-2 gap-8">
                            <div className="p-6 rounded-3xl bg-white/5 border border-white/5 text-center">
                                <Cpu className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                                <h4 className="text-xs font-black uppercase tracking-widest">Neural</h4>
                                <p className="text-[10px] opacity-40 mt-2">Intuition & Créativité</p>
                            </div>
                            <div className="p-6 rounded-3xl bg-white/5 border border-white/5 text-center">
                                <Scale className="w-12 h-12 text-anime-accent mx-auto mb-4" />
                                <h4 className="text-xs font-black uppercase tracking-widest">Symbolic</h4>
                                <p className="text-[10px] opacity-40 mt-2">Logique & Preuve</p>
                            </div>
                            <div className="col-span-2 p-8 rounded-3xl bg-gradient-to-r from-blue-600/20 to-anime-accent/20 border border-white/10 text-center">
                                <h4 className="text-xl font-black italic uppercase tracking-widest mb-2">NEURO-SYMBOLIQUE</h4>
                                <p className="text-xs font-bold opacity-60 uppercase">La fusion parfaite pour l'Analyse Otaku</p>
                            </div>
                        </div>
                    </Card>
                </div>
            </section>

            {/* Logical Profiling */}
            <section className="text-center space-y-16">
                <div className="max-w-3xl mx-auto space-y-6">
                    <h2 className="text-6xl font-black italic uppercase manga-font tracking-tighter">
                        PROFILAGE <span className="text-anime-accent">LOGIQUE</span>
                    </h2>
                    <p className="text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                        Animetix ne se contente pas de vous recommander des titres similaires. 
                        Il déconstruit vos interactions pour extraire des "engrammes" cognitifs.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
                    <Card className="bg-navy-900/20 border-white/5 p-10 hover:border-blue-500/30 transition-all group">
                        <Fingerprint className="w-12 h-12 text-blue-500 mb-8 group-hover:scale-110 transition-transform" />
                        <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight">Archétype Nexus</h3>
                        <p className="text-sm text-gray-500 leading-relaxed font-medium italic">
                            Analyse de votre comportement de jeu (Akinetix, Paradox) pour définir votre "empreinte" de fan (ex: Analytique Shonen, Explorateur Seinen).
                        </p>
                    </Card>
                    <Card className="bg-navy-900/20 border-white/5 p-10 hover:border-anime-accent/30 transition-all group">
                        <Activity className="w-12 h-12 text-anime-accent mb-8 group-hover:scale-110 transition-transform" />
                        <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight">Drift Sémantique</h3>
                        <p className="text-sm text-gray-500 leading-relaxed font-medium italic">
                            Notre système détecte en temps réel si vos goûts évoluent ou si vous explorez de nouvelles frontières narratives (KS-Test).
                        </p>
                    </Card>
                    <Card className="bg-navy-900/20 border-white/5 p-10 hover:border-emerald-500/30 transition-all group">
                        <Network className="w-12 h-12 text-emerald-500 mb-8 group-hover:scale-110 transition-transform" />
                        <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight">Graphe de Soi</h3>
                        <p className="text-sm text-gray-500 leading-relaxed font-medium italic">
                            Chaque préférence crée un nœud dans votre graphe personnel, relié aux studios, auteurs et thèmes que vous chérissez.
                        </p>
                    </Card>
                </div>
            </section>

            {/* Interactive Engines */}
            <section className="bg-white/5 border border-white/10 rounded-[4rem] p-16 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-12 opacity-5 grayscale group-hover:grayscale-0 transition-all">
                    <Zap className="w-64 h-64 text-yellow-400 rotate-12" />
                </div>
                
                <h2 className="text-4xl font-black italic uppercase manga-font tracking-tight mb-16 flex items-center gap-4">
                    <Gamepad2 className="w-10 h-10 text-yellow-500" /> Les Moteurs d'Expérience
                </h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 relative z-10">
                    <div className="space-y-8">
                        <div className="flex gap-6">
                            <div className="w-16 h-16 rounded-2xl bg-blue-600/10 flex items-center justify-center text-blue-500 flex-shrink-0">
                                <Search className="w-8 h-8" />
                            </div>
                            <div>
                                <h4 className="text-xl font-black italic uppercase tracking-widest mb-2">Akinetix (RL PPO)</h4>
                                <p className="text-sm text-gray-400 leading-relaxed italic">
                                    Utilise l'apprentissage par renforcement pour minimiser l'entropie et deviner vos personnages en un minimum de coups.
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-6">
                            <div className="w-16 h-16 rounded-2xl bg-purple-600/10 flex items-center justify-center text-purple-500 flex-shrink-0">
                                <CheckCircle2 className="w-8 h-8" />
                            </div>
                            <div>
                                <h4 className="text-xl font-black italic uppercase tracking-widest mb-2">Paradox Quest (Z3 Solver)</h4>
                                <p className="text-sm text-gray-400 leading-relaxed italic">
                                    Prouve mathématiquement l'existence d'un "intrus" thématique en compilant des prédicats logiques résolus par le solveur Z3 de Microsoft Research.
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-6">
                            <div className="w-16 h-16 rounded-2xl bg-anime-accent/10 flex items-center justify-center text-anime-accent flex-shrink-0">
                                <Sparkles className="w-8 h-8" />
                            </div>
                            <div>
                                <h4 className="text-xl font-black italic uppercase tracking-widest mb-2">La Forge (Stable Diffusion XL)</h4>
                                <p className="text-sm text-gray-400 leading-relaxed italic">
                                    Génération d'images et clonage de voix (XTTS-v2) pour matérialiser vos fusions créatives les plus folles.
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-black/60 rounded-[3rem] p-10 border border-white/10 flex flex-col justify-center text-center space-y-6">
                        <h3 className="text-2xl font-black italic uppercase tracking-tighter text-blue-400">Prêt pour l'immersion ?</h3>
                        <p className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-8 leading-loose">
                            Votre voyage dans le Nexus ne fait que commencer. 
                            Chaque action alimente la boucle de feedback DPO pour rendre l'IA plus experte.
                        </p>
                        <div className="flex flex-col gap-4">
                            <Button as={Link} to="/explore/" variant="primary" className="py-6 rounded-2xl bg-blue-600 border-none font-black italic uppercase">COMMENCER L'EXPLORATION</Button>
                            <Button as={Link} to="/social/transparency/" variant="outline" className="py-4 rounded-2xl border-white/20 text-white/60 hover:text-white uppercase text-[10px] font-black">CONSULTER L'AUDIT ÉTHIQUE</Button>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        {/* Technical Footer */}
        <footer className="py-24 border-t border-white/5 bg-black/40">
             <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-12 opacity-20 grayscale">
                 <div className="flex items-center gap-4">
                    <Database className="w-6 h-6" />
                    <span className="text-[10px] font-black uppercase tracking-widest">Neural-Symbolic Architecture v2.4</span>
                 </div>
                 <div className="flex items-center gap-4">
                    <Badge variant="neutral" className="bg-white/5 px-4 py-2 border-white/10">CORE: DEEPSEEK-R1 + Z3 SOLVER</Badge>
                 </div>
             </div>
        </footer>
      </div>
    </AnimatedPage>
  );
};

const StepItem = ({ index, title, desc }: { index: string, title: string, desc: string }) => (
    <div className="flex items-start gap-6 group">
        <span className="text-4xl font-black italic manga-font text-white/10 group-hover:text-blue-500/20 transition-colors">{index}</span>
        <div>
            <h4 className="text-sm font-black italic uppercase tracking-widest mb-1 group-hover:text-white transition-colors">{title}</h4>
            <p className="text-xs text-gray-500 font-bold uppercase tracking-tight leading-relaxed">{desc}</p>
        </div>
    </div>
);

export default ArchetypeGuidePage;
