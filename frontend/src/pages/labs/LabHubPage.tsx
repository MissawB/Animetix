import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Cpu, 
  Activity, 
  Globe, 
  Atom,
  Users,
  Zap,
  ArrowRight,
  ShieldCheck,
  Terminal,
  Layers,
  Bot,
  Palette,
  Headphones,
  Video,
  Cuboid,
  Brain,
  Fingerprint,
  GitBranch,
  Mic,
  Waves,
  Music,
  MessageSquare,
  Eye,
  Film,
  Binary,
  Swords,
  Map,
  Target,
  Search
} from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const labs = [
    {
        id: 'quantum',
        title: 'Quantum Cognition',
        desc: 'Modélisation des préférences par superposition d\'états et effondrement SAT.',
        icon: Atom,
        url: '/lab/quantum/',
        color: 'text-purple-500',
        bg: 'from-purple-500/20 to-transparent',
        badge: 'Theoretical AI',
        status: 'Operational'
    },
    {
        id: 'swarm',
        title: 'Swarm Intelligence',
        desc: 'Validation décentralisée des faits de lore par consensus multi-agents IA.',
        icon: Users,
        url: '/lab/swarm/',
        color: 'text-emerald-500',
        bg: 'from-emerald-500/20 to-transparent',
        badge: 'Multi-Agent',
        status: 'Operational'
    },
    {
        id: 'plasticity',
        title: 'Synaptic Plasticity',
        desc: 'Évolution dynamique des liens sémantiques via simulation bio-inspirée.',
        icon: Activity,
        url: '/lab/synaptic/',
        color: 'text-red-500',
        bg: 'from-red-500/20 to-transparent',
        badge: 'Neural Sim',
        status: 'Operational'
    },
    {
        id: 'compiler',
        title: 'JIT Optimizer',
        desc: 'Génération et injection temps-réel de microcode C optimisé par l\'IA.',
        icon: Cpu,
        url: '/lab/compiler/',
        color: 'text-blue-500',
        bg: 'from-blue-500/20 to-transparent',
        badge: 'Performance',
        status: 'JIT SOTA'
    },
    {
        id: 'multiverse',
        title: 'Multiverse Genesis',
        desc: 'Génération autonome de segments de lore auto-cohérents (ADMS).',
        icon: Globe,
        url: '/lab/multiverse/',
        color: 'text-amber-500',
        bg: 'from-amber-500/20 to-transparent',
        badge: 'Generative',
        status: 'Neo4j Sync',
        catalogUrl: '/multiverse/catalog/'
    },
    {
        id: 'tot',
        title: 'Tree of Thoughts',
        desc: 'Visualisez le raisonnement multi-branches (MCTS) de l\'IA en temps réel.',
        icon: GitBranch,
        url: '/lab/tot/',
        color: 'text-emerald-500',
        bg: 'from-emerald-500/20 to-transparent',
        badge: 'Recursive AI',
        status: 'Operational'
    },
    {
        id: 'diagnostics',
        title: 'Neural Diagnostics',
        desc: 'Analyse d\'entropie et cartographie de confiance cognitive des réseaux.',
        icon: Brain,
        url: '/lab/diagnostics/',
        color: 'text-blue-500',
        bg: 'from-blue-500/20 to-transparent',
        badge: 'Diagnostics',
        status: 'Operational'
    },
    {
        id: 'liquid',
        title: 'Liquid Neural Networks',
        desc: 'Traitement adaptatif de flux continus via équations différentielles neuronales.',
        icon: Waves,
        url: '/lab/liquid-neural-networks/',
        color: 'text-cyan-400',
        bg: 'from-cyan-400/20 to-transparent',
        badge: 'Neural ODE',
        status: 'Operational'
    },
    {
        id: 'cove',
        title: 'CoVe Oracle',
        desc: 'Réduction des hallucinations via protocole Chain-of-Verification.',
        icon: ShieldCheck,
        url: '/lab/cove-oracle/',
        color: 'text-blue-400',
        bg: 'from-blue-400/20 to-transparent',
        badge: 'Reasoning',
        status: 'Operational'
    }
];

const creativeLabs = [
    {
        id: 'manga',
        title: 'Manga Lab',
        desc: 'Rendu Manga par IA et génération de planches dynamiques.',
        icon: Palette,
        url: '/lab/manga/',
        color: 'text-blue-500',
        bg: 'from-blue-500/20 to-transparent',
        badge: 'Visual AI'
    },
    {
        id: 'manga-voice',
        title: 'Manga Voice',
        desc: 'Doublage IA zero-shot et clonage vocal pour vos personnages.',
        icon: Mic,
        url: '/lab/manga-voice/',
        color: 'text-orange-500',
        bg: 'from-orange-500/20 to-transparent',
        badge: 'Neural Dubbing'
    },
    {
        id: 'audio',
        title: 'Audio Lab',
        desc: 'Clonage vocal haute fidélité et synthèse d\'ambiances sonores.',
        icon: Headphones,
        url: '/lab/audio/',
        color: 'text-emerald-500',
        bg: 'from-emerald-500/20 to-transparent',
        badge: 'Neural Audio'
    },
    {
        id: 'seiyuu',
        title: 'Seiyuu Discovery',
        desc: 'Identifiez les voix iconiques et accédez au catalogue des doubleurs japonais.',
        icon: Mic,
        url: '/lab/audio/seiyuu/',
        color: 'text-emerald-400',
        bg: 'from-emerald-400/20 to-transparent',
        badge: 'VA Catalog'
    },
    {
        id: 'video',
        title: 'Video Lab',
        desc: 'Analyse et indexation vidéo intelligente par vision artificielle.',
        icon: Video,
        url: '/lab/video/',
        color: 'text-orange-500',
        bg: 'from-orange-500/20 to-transparent',
        badge: 'Computer Vision'
    },
    {
        id: 'video-rag',
        title: 'Video RAG',
        desc: 'Recherche augmentée par récupération directement sur des flux vidéo.',
        icon: Search,
        url: '/lab/video-rag/',
        color: 'text-red-500',
        bg: 'from-red-500/20 to-transparent',
        badge: 'Video Retrieval'
    },
    {
        id: 'spatial',
        title: 'Spatial Lab',
        desc: 'Reconstruction 3D et Gaussian Splatting à partir de sources 2D.',
        icon: Cuboid,
        url: '/lab/spatial/',
        color: 'text-purple-500',
        bg: 'from-purple-500/20 to-transparent',
        badge: '3D/Spatial'
    },
    {
        id: 'soundscape',
        title: 'Soundscape Lab',
        desc: 'Génération procédurale d\'environnements sonores immersifs et spatialisés.',
        icon: Music,
        url: '/lab/soundscape/',
        color: 'text-emerald-400',
        bg: 'from-emerald-400/20 to-transparent',
        badge: 'Generative Audio'
    },
    {
        id: 'speech-to-speech',
        title: 'Speech-to-Speech',
        desc: 'Traduction vocale temps-réel préservant l\'émotion et le timbre original.',
        icon: MessageSquare,
        url: '/lab/speech-to-speech/',
        color: 'text-blue-400',
        bg: 'from-blue-400/20 to-transparent',
        badge: 'Voice Conversion'
    },
    {
        id: 'voice-lab',
        title: 'Voice Lab',
        desc: 'Synthèse vocale avancée et modulation de paramètres prosodiques fins.',
        icon: Mic,
        url: '/lab/voice/',
        color: 'text-orange-400',
        bg: 'from-orange-400/20 to-transparent',
        badge: 'TTS SOTA'
    },
    {
        id: 'visual-nexus',
        title: 'Visual Nexus',
        desc: 'Interconnexion de modèles de vision pour une compréhension holistique.',
        icon: Eye,
        url: '/lab/visual-nexus/',
        color: 'text-purple-400',
        bg: 'from-purple-400/20 to-transparent',
        badge: 'Vision-Language'
    },
    {
        id: 'cinematic',
        title: 'Cinematic Reconstruction',
        desc: 'Génération de séquences cinématographiques à partir de narrations.',
        icon: Film,
        url: '/lab/cinematic/',
        color: 'text-red-400',
        bg: 'from-red-400/20 to-transparent',
        badge: 'Generative Video'
    }
];

const cognitionLabs = [
    {
        id: 'archetype',
        title: 'Archetype Nexus',
        desc: 'Visualisez la convergence de vos traits et votre espace latent.',
        icon: Brain,
        url: '/social/archetype-nexus/',
        color: 'text-purple-500',
        bg: 'from-purple-500/20 to-transparent',
        badge: 'Social AI'
    },
    {
        id: 'memory',
        title: 'Neuro-Memory',
        desc: 'Gérez l\'empreinte sémantique et vos vecteurs de préférence.',
        icon: Fingerprint,
        url: '/social/neuro-memory/',
        color: 'text-emerald-500',
        bg: 'from-emerald-500/20 to-transparent',
        badge: 'Memory'
    },
    {
        id: 'simulator',
        title: 'Timeline Sim',
        desc: 'Explorez les futurs alternatifs et le regret conversationnel.',
        icon: GitBranch,
        url: '/search/counterfactual/',
        color: 'text-blue-500',
        bg: 'from-blue-500/20 to-transparent',
        badge: 'Game Theory'
    },
    {
        id: 'latent',
        title: 'Latent Space',
        desc: 'Exploration géométrique des représentations vectorielles de haute dimension.',
        icon: Binary,
        url: '/lab/latent-space/',
        color: 'text-indigo-400',
        bg: 'from-indigo-400/20 to-transparent',
        badge: 'Vector Geometry'
    },
    {
        id: 'debate',
        title: 'AI Debate Arena',
        desc: 'Confrontations sémantiques entre agents basées sur le Knowledge Graph.',
        icon: Swords,
        url: '/social/debate-arena/',
        color: 'text-red-400',
        bg: 'from-red-400/20 to-transparent',
        badge: 'Game Theory'
    },
    {
        id: 'graph-map',
        title: 'Lore World Map',
        desc: 'Visualisation des clusters de connaissances détectés par l\'algorithme de Leiden.',
        icon: Map,
        url: '/graph/map/',
        color: 'text-emerald-400',
        bg: 'from-emerald-400/20 to-transparent',
        badge: 'Graph RAG'
    },
    {
        id: 'strategy',
        title: 'Strategy Lab',
        desc: 'Interface de simulation CFR pour l\'optimisation des arbres de décision.',
        icon: Target,
        url: '/lab/strategy/',
        color: 'text-red-500',
        bg: 'from-red-500/20 to-transparent',
        badge: 'Nash Equil.'
    }
];

const LabHubPage: React.FC = () => {
  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white absolute left-0 top-0 pt-24 pb-20 z-0">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
          
          {/* Header Ultra-Moderne */}
        <header className="mb-24 relative">
            <div className="absolute -top-32 -left-32 w-[600px] h-[600px] bg-red-600/5 blur-[150px] rounded-full -z-10" />
            
            <div className="flex flex-col md:flex-row justify-between items-end gap-12">
                <div className="max-w-3xl">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-[0.3em] text-red-500 mb-6 shadow-[0_0_20px_rgba(220,38,38,0.1)]">
                        <Terminal className="w-3 h-3" /> Singularity Access Protocol v5.2
                    </div>
                    <h1 className="text-8xl font-black italic manga-font tracking-tighter uppercase mb-6 leading-[0.9]">
                        SINGULARITY <span className="text-red-600 text-glow">LABS</span>
                    </h1>
                    <p className="text-2xl font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed">
                        Explorez la frontière entre l'IA générative et la cognition pure.
                    </p>
                </div>
                
                <div className="flex gap-4">
                    <Card padding="lg" className="bg-black/40 border-white/5 text-center min-w-[160px]">
                        <p className="text-[10px] font-black uppercase opacity-30 mb-2">SOTA Status</p>
                        <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-none uppercase font-black italic">CONNECTED</Badge>
                    </Card>
                </div>
            </div>
        </header>

        {/* Labs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-24">
            {labs.map((lab) => (
                <Link key={lab.id} to={lab.url} className="no-underline group">
                    <Card padding="none" className="h-full bg-navy-950/40 border-white/5 hover:border-red-600/30 transition-all duration-500 overflow-hidden relative group shadow-2xl">
                        {/* Interactive BG hover effect */}
                        <div className={`absolute inset-0 bg-gradient-to-br ${lab.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                        
                        <div className="p-10 relative z-10 flex flex-col h-full justify-between">
                            <div>
                                <div className="flex justify-between items-start mb-10">
                                    <div className={`p-4 rounded-2xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${lab.color}`}>
                                        <lab.icon className="w-8 h-8" />
                                    </div>
                                    <Badge variant="neutral" className="bg-white/5 border-none text-[8px] font-black italic uppercase tracking-widest">{lab.badge}</Badge>
                                </div>
                                <h3 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter group-hover:text-white transition-colors">{lab.title}</h3>
                                <p className="text-xs font-bold opacity-40 uppercase leading-relaxed tracking-wider mb-10 group-hover:opacity-60 transition-opacity">
                                    {lab.desc}
                                </p>
                            </div>
                            
                            <div className="flex items-center justify-between mt-auto pt-8 border-t border-white/5">
                                <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${lab.color} opacity-0 group-hover:opacity-100 transition-all transform translate-x-[-10px] group-hover:translate-x-0 duration-500`}>
                                    INITIALIZE <ArrowRight className="inline w-3 h-3 ml-2" />
                                </span>
                                <div className="flex items-center gap-3">
                                    {(lab as { catalogUrl?: string }).catalogUrl && (
                                        <Link
                                            to={(lab as { catalogUrl?: string }).catalogUrl!}
                                            className="text-[9px] font-black uppercase text-amber-500 hover:text-white transition-colors tracking-widest z-20"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            Catalogue →
                                        </Link>
                                    )}
                                    <span className="text-[9px] font-bold opacity-20 uppercase">{lab.status}</span>
                                </div>
                            </div>
                        </div>
                    </Card>
                </Link>
            ))}


        </div>

        {/* Creative Forge Section */}
        <div className="mb-12 flex items-center justify-between gap-4">
            <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter">
                FORGE <span className="text-orange-500">CRÉATIVE</span>
            </h2>
            <div className="h-px flex-1 bg-gradient-to-r from-orange-500/50 to-transparent" />
            <Link to="/forge-hub/" className="text-[10px] font-black uppercase tracking-widest text-orange-500 hover:text-white transition-colors flex items-center gap-2 group whitespace-nowrap">
                ACCÉDER AU HUB COMPLET <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
            </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-24">
            {creativeLabs.map((lab) => (
                <Link key={lab.id} to={lab.url} className="no-underline group">
                    <Card padding="none" className="h-full bg-black/40 border-white/5 hover:border-orange-500/30 transition-all duration-500 overflow-hidden relative group">
                        <div className={`absolute inset-0 bg-gradient-to-br ${lab.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                        <div className="p-8 relative z-10">
                            <div className="flex justify-between items-start mb-6">
                                <div className={`p-3 rounded-xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${lab.color}`}>
                                    <lab.icon className="w-6 h-6" />
                                </div>
                                <Badge variant="neutral" className="bg-white/5 border-none text-[7px] font-black italic uppercase tracking-widest">{lab.badge}</Badge>
                            </div>
                            <h3 className="text-xl font-black italic manga-font uppercase mb-3 tracking-tighter group-hover:text-white transition-colors">{lab.title}</h3>
                            <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed tracking-wider group-hover:opacity-60 transition-opacity">
                                {lab.desc}
                            </p>
                        </div>
                    </Card>
                </Link>
            ))}
        </div>

        {/* Cognition Core Section */}
        <div className="mb-12 flex items-center justify-between gap-4">
            <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter">
                COGNITION <span className="text-purple-600">CORE</span>
            </h2>
            <div className="h-px flex-1 bg-gradient-to-r from-purple-600/50 to-transparent" />
            <Link to="/cognition-hub/" className="text-[10px] font-black uppercase tracking-widest text-purple-600 hover:text-white transition-colors flex items-center gap-2 group whitespace-nowrap">
                ACCÉDER AU HUB COMPLET <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
            </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-24">
            {cognitionLabs.map((lab) => (
                <Link key={lab.id} to={lab.url} className="no-underline group">
                    <Card padding="none" className="h-full bg-black/40 border-white/5 hover:border-purple-600/30 transition-all duration-500 overflow-hidden relative group">
                        <div className={`absolute inset-0 bg-gradient-to-br ${lab.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                        <div className="p-8 relative z-10">
                            <div className="flex justify-between items-start mb-6">
                                <div className={`p-3 rounded-xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${lab.color}`}>
                                    <lab.icon className="w-6 h-6" />
                                </div>
                                <Badge variant="neutral" className="bg-white/5 border-none text-[7px] font-black italic uppercase tracking-widest">{lab.badge}</Badge>
                            </div>
                            <h3 className="text-xl font-black italic manga-font uppercase mb-3 tracking-tighter group-hover:text-white transition-colors">{lab.title}</h3>
                            <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed tracking-wider group-hover:opacity-60 transition-opacity">
                                {lab.desc}
                            </p>
                        </div>
                    </Card>
                </Link>
            ))}
        </div>

        {/* Global Tech Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <Card padding="lg" className="bg-navy-900 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-blue-400">
                    <Layers className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">Architecture</p>
                    <p className="text-lg font-black italic uppercase manga-font">Neuro-Symbolic V5</p>
                </div>
            </Card>
            <Card padding="lg" className="bg-navy-900 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-purple-400">
                    <Bot className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">Compute Power</p>
                    <p className="text-lg font-black italic uppercase manga-font">H100 Distributed</p>
                </div>
            </Card>
            <Card padding="lg" className="bg-navy-900 border-white/5 flex items-center gap-8 shadow-xl">
                <div className="p-4 bg-white/5 rounded-2xl text-orange-400">
                    <Zap className="w-8 h-8" />
                </div>
                <div>
                    <p className="text-[10px] font-black uppercase opacity-30 mb-1">Latency</p>
                    <p className="text-lg font-black italic uppercase manga-font">Sub-Temporal 12ms</p>
                </div>
            </Card>
        </div>

        {/* Alpha Footer */}
        <footer className="mt-32 pt-16 border-t border-white/5 text-center">
            <p className="text-[9px] font-bold uppercase tracking-[0.5em] opacity-20 italic max-w-4xl mx-auto leading-relaxed">
                Le Singularity Lab est un environnement de recherche de niveau Omega. <br />
                Toutes les simulations de multivers et de plasticité sont exécutées sur des cœurs tensoriels isolés pour prévenir toute fuite de conscience artificielle.
            </p>
        </footer>
      </div>
    </AnimatedPage>
    </div>
  );
};

export default LabHubPage;


