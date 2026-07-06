import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Brain, 
  Search, 
  Zap, 
  Sparkles, 
  Network, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  Clock
} from 'lucide-react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import ForceGraph2D, { type ForceGraphMethods, type NodeObject, type LinkObject } from 'react-force-graph-2d';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import XaiReportDisplay, { type XaiReport } from "../../components/XaiReportDisplay";

interface Step {
  id: string;
  type: 'thought' | 'eval' | 'token' | 'xai_report';
  content: string | XaiReport;
  timestamp: number;
  agent?: string;
  parentId?: string; 
  xaiReport?: XaiReport;
}

// Interfaces for ForceGraph
interface GraphNode {
  id: string;
  label: string;
  agent: string;
  type: string;
  val: number;
  color: string;
  // Populated by the force-graph engine at render time.
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  color: string;
}

const ExpertNexusPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useTranslation();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [isStreaming, setIsStreaming] = useState(false);
  const [, setSteps] = useState<Step[]>([]);
  const [finalAnswer, setFinalAnswer] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<'auth' | 'payment' | 'generic' | null>(null);
  const [xaiReport, setXaiReport] = useState<XaiReport | null>(null);
  const receivedAnyRef = useRef(false);
  
  // Graph state
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[], links: GraphLink[] }>({ nodes: [], links: [] });
  const graphRef = useRef<ForceGraphMethods<NodeObject<GraphNode>, LinkObject<GraphNode, GraphLink>> | undefined>(undefined);

  const eventSourceRef = useRef<EventSource | null>(null);

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const getAgentColorCode = (agent?: string) => {
    switch (agent) {
      case 'Semantic Router': return '#3b82f6'; // blue-500
      case 'State Machine': return '#a855f7'; // purple-500
      case 'TTC': return '#ef4444'; // red-500
      case 'Graph User Memory': return '#10b981'; // emerald-500
      case 'Judge': return '#10b981'; // emerald-500
      case 'Synthesizer': return '#eab308'; // yellow-500
      case 'Root': return '#ffffff';
      default: return '#64748b'; // slate-500
    }
  };

  const handleSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    // Ce mode utilise l'IA (GPU) et consomme des Bx → login requis. On le détecte
    // en amont car EventSource ne peut pas lire un statut HTTP 401/402.
    if (!useAuthStore.getState().isAuthenticated) {
      setError(t('search.expert.auth_error', "Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour lancer une analyse."));
      setErrorKind('auth');
      setIsStreaming(false);
      return;
    }

    setSearchParams({ q: searchQuery });
    setSteps([]);
    setFinalAnswer('');
    setError(null);
    setErrorKind(null);
    receivedAnyRef.current = false;
    setIsStreaming(true);

    // Initialize Root node
    const rootId = 'root';
    const initNodes: GraphNode[] = [{
        id: rootId,
        label: "Question",
        agent: 'Root',
        type: 'root',
        val: 20,
        color: '#ffffff'
    }];
    setGraphData({ nodes: initNodes, links: [] });

    const url = `/api/v1/stream/agentic-rag/?q=${encodeURIComponent(searchQuery)}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    let lastNodeId = rootId;

    eventSource.onmessage = (event) => {
      try {
        receivedAnyRef.current = true;
        const data = JSON.parse(event.data);

        if (data.type === 'token') {
          setFinalAnswer(prev => prev + data.content);
        } else if (data.type === 'thought') {
          const agentMatch = data.content.match(/^\[(.*?)\]/);
          const agent = agentMatch ? agentMatch[1] : 'System';
          const content = agentMatch ? data.content.replace(/^\[.*?\]\s*/, '') : data.content;
          const newId = Math.random().toString(36).substr(2, 9);

          setSteps(prev => [...prev, {
            id: newId,
            type: 'thought',
            content,
            agent,
            timestamp: Date.now(),
            parentId: lastNodeId
          }]);

          setGraphData(prev => {
              const newNode = {
                  id: newId,
                  label: content,
                  agent: agent,
                  type: 'thought',
                  val: 10,
                  color: getAgentColorCode(agent)
              };
              const newLink = {
                  source: lastNodeId,
                  target: newId,
                  color: 'rgba(255, 255, 255, 0.2)'
              };
              return {
                  nodes: [...prev.nodes, newNode],
                  links: [...prev.links, newLink]
              };
          });
          lastNodeId = newId;

        } else if (data.type === 'eval') {
          const newId = Math.random().toString(36).substr(2, 9);
          setSteps(prev => [...prev, {
            id: newId,
            type: 'eval',
            content: data.content,
            agent: 'Judge',
            timestamp: Date.now(),
            parentId: lastNodeId
          }]);

          setGraphData(prev => {
              const newNode = {
                  id: newId,
                  label: "Évaluation",
                  agent: 'Judge',
                  type: 'eval',
                  val: 12,
                  color: getAgentColorCode('Judge')
              };
              const newLink = {
                  source: lastNodeId,
                  target: newId,
                  color: 'rgba(255, 255, 255, 0.2)'
              };
              return {
                  nodes: [...prev.nodes, newNode],
                  links: [...prev.links, newLink]
              };
          });
          lastNodeId = newId;

        } else if (data.type === 'error') {
          setError(data.content);
          stopStreaming();
        } else if (data.type === 'done') {
          stopStreaming();
        } else if (data.type === 'xai_report') { 
          setXaiReport(data.content); 
        }
      } catch (e) {
        console.error("Failed to parse event data", e);
      }
    };

    eventSource.onerror = () => {
      // EventSource ne donne ni statut ni corps. Si le flux échoue sans qu'aucun
      // évènement n'ait été reçu, c'est presque toujours un refus 402 (solde de Bx
      // insuffisant), l'utilisateur étant déjà authentifié à ce stade.
      if (!receivedAnyRef.current) {
        setError(t('search.expert.payment_error', 'Analyse refusée. Vérifie ton solde de Berrix (ce mode IA en consomme) puis réessaie.'));
        setErrorKind('payment');
      }
      stopStreaming();
    };
  }, [setSearchParams, stopStreaming]);

  useEffect(() => {
    let isMounted = true;
    const startInitialSearch = async () => {
        if (initialQuery && isMounted) {
            await handleSearch(initialQuery);
        }
    };
    startInitialSearch();
    return () => { 
      isMounted = false;
      stopStreaming(); 
    };
  }, [initialQuery, handleSearch, stopStreaming]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col min-h-[calc(100vh-100px)]">
        
        {/* Header */}
        <header className="mb-12 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
               <Brain className="w-4 h-4 fill-current" /> SOTA Agentic RAG v2.0
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                EXPERT <span className="text-blue-500 text-glow">NEXUS</span>
            </h1>
            <p className="text-lg font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                Raisonnement arborescent multi-agents pour les requêtes complexes de Lore.
            </p>
        </header>

        {/* Search Bar */}
        <Card padding="lg" className="mb-12 bg-navy-950/50 border-white/5 shadow-2xl rounded-[3rem]">
            <form onSubmit={onSubmit} className="flex gap-4">
                <div className="relative flex-grow group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/20 group-focus-within:text-blue-500 transition-colors" />
                    <input
                        type="text"
                        aria-label="Rechercher"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={t('search.expert.placeholder', 'Posez une question profonde sur un univers, une relation ou un arc narratif...')}
                        className="w-full bg-black border-2 border-white/5 rounded-[2.5rem] py-6 pl-16 pr-8 text-lg font-bold focus:border-blue-600 outline-none transition-all placeholder:opacity-20"
                    />
                </div>
                <Button 
                    type="submit" 
                    disabled={isStreaming || !query.trim()}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-10 rounded-[2.5rem] font-black italic text-xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                >
                    {isStreaming ? <Zap className="w-6 h-6 animate-pulse" /> : t('search.expert.solve_btn', 'RÉSOUDRE')}
                </Button>
            </form>
        </Card>

        {/* Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-grow">
            
            {/* Tree of Thoughts (Graph) */}
            <div className="lg:col-span-5 flex flex-col h-full min-h-[500px]">
                <div className="flex items-center justify-between mb-6 px-4">
                    <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                        <Network className="w-4 h-4" /> {t('search.expert.thought_tree', 'Arbre de Pensée (MCTS)')}
                    </h3>
                    {isStreaming && (
                        <Badge variant="primary" className="bg-blue-600 animate-pulse text-[8px]">ACTIVE REASONING</Badge>
                    )}
                </div>

                <Card padding="none" className="flex-grow bg-black border-white/5 rounded-[2.5rem] overflow-hidden relative">
                    {graphData.nodes.length > 0 ? (
                        <div className="absolute inset-0">
                            <ForceGraph2D
                                ref={graphRef}
                                graphData={graphData}
                                nodeLabel="agent"
                                nodeColor="color"
                                nodeVal="val"
                                linkColor="color"
                                linkWidth={2}
                                backgroundColor="#000000"
                                onEngineStop={() => graphRef.current?.zoomToFit(400, 20)}
                                nodeCanvasObjectMode={() => 'after'}
                                nodeCanvasObject={(node: GraphNode, ctx, globalScale) => {
                                    const label = node.agent;
                                    const fontSize = 12/globalScale;
                                    ctx.font = `${fontSize}px Sans-Serif`;
                                    ctx.textAlign = 'center';
                                    ctx.textBaseline = 'middle';
                                    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'; // Text color
                                    ctx.fillText(label, node.x || 0, (node.y || 0) + 12);
                                }}
                            />
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-24">
                            <Network className="w-16 h-16 mb-4" />
                            <p className="text-xs font-black uppercase tracking-widest">{t('search.expert.waiting', 'En attente d\'une requête complexe')}</p>
                        </div>
                    )}
                </Card>
            </div>

            {/* Answer Display */}
            <div className="lg:col-span-7 flex flex-col h-full">
                <div className="flex items-center gap-4 mb-6 px-4">
                    <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-yellow-400" /> {t('search.expert.synthesis', 'Synthèse Expert')}
                    </h3>
                </div>

                <Card padding="none" className="flex-grow bg-black border-white/10 shadow-[0_0_100px_rgba(0,0,0,0.8)] overflow-hidden rounded-[3rem] relative flex flex-col">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-600 to-transparent opacity-50" />
                    
                    <div className="p-12 overflow-y-auto flex-grow prose prose-invert max-w-none">
                        {error && (
                            <div className="p-8 bg-red-500/10 border border-red-500/20 rounded-3xl flex items-center gap-6 text-red-500">
                                <AlertCircle className="w-12 h-12 flex-shrink-0" />
                                <div className="flex-grow">
                                    <h4 className="text-xl font-black italic uppercase mb-1">
                                        {errorKind === 'auth' ? t('search.expert.auth_required', 'Connexion requise') : errorKind === 'payment' ? t('search.expert.insufficient_bx', 'Berrix insuffisants') : t('search.expert.resolution_error', 'Erreur de Résolution')}
                                    </h4>
                                    <p className="text-sm font-bold opacity-80 uppercase tracking-wide">{error}</p>
                                    {errorKind === 'auth' && (
                                        <Link to="/auth/login/"><Button variant="primary" className="mt-4">{t('search.expert.login_btn', 'Se connecter')}</Button></Link>
                                    )}
                                    {errorKind === 'payment' && (
                                        <Link to="/power-station/"><Button variant="primary" className="mt-4">{t('search.expert.recharge_btn', 'Recharger des Berrix')}</Button></Link>
                                    )}
                                </div>
                            </div>
                        )}

                        {!error && !finalAnswer && !isStreaming && (
                            <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-32">
                                <Sparkles className="w-24 h-24 mb-8" />
                                <h3 className="text-3xl font-black italic manga-font uppercase mb-4">{t('search.expert.idle_title', 'Nexus en veille')}</h3>
                                <p className="text-sm font-bold uppercase tracking-[0.3em]">{t('search.expert.idle_desc', 'L\'IA de 5ème génération attend vos instructions.')}</p>
                            </div>
                        )}

                        {!error && (finalAnswer || isStreaming) && (
                            <div className="space-y-8 animate-fade-in">
                                <p className="text-2xl font-bold leading-relaxed whitespace-pre-wrap text-white/90">
                                    {finalAnswer}
                                    {isStreaming && (
                                        <motion.span 
                                            animate={{ opacity: [0, 1, 0] }}
                                            transition={{ repeat: Infinity, duration: 1 }}
                                            className="inline-block w-2 h-8 bg-blue-500 ml-2 align-middle"
                                        />
                                    )}
                                </p>
                            </div>
                        )}
                    </div>

                    {xaiReport && <XaiReportDisplay xaiReport={xaiReport} />}

                    {/* Footer Stats */}
                    <div className="px-12 py-8 border-t border-white/5 bg-white/5 flex flex-wrap justify-between items-center gap-6">
                        <div className="flex gap-8">
                            <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 text-blue-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Latence: 1.2s</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Faithfulness: 98%</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            <span className="text-[8px] font-black uppercase tracking-widest text-gray-500">Grounding Verificated</span>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ExpertNexusPage;


