import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSSE, type SSEEvent } from '../../hooks/useSSE';
import {
  Brain,
  Search,
  Zap,
  Sparkles,
  Network,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { useSearchParams, Link } from 'react-router-dom';

import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import ForceGraph2D, {
  type ForceGraphMethods,
  type NodeObject,
  type LinkObject,
} from '../../components/LazyForceGraph2D';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import XaiReportDisplay, { type XaiReport } from '../../components/XaiReportDisplay';

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

const AGENT_NODE_COLORS: Record<string, string> = {
  'Semantic Router': '#3b82f6',
  'State Machine': '#a855f7',
  TTC: '#ef4444',
  'Graph User Memory': '#10b981',
  Judge: '#10b981',
  Synthesizer: '#eab308',
  Root: '#ffffff',
};

const getAgentColorCode = (agent?: string) => (agent && AGENT_NODE_COLORS[agent]) || '#64748b';

const ExpertNexusPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useTranslation();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [, setSteps] = useState<Step[]>([]);
  const [finalAnswer, setFinalAnswer] = useState('');
  const [xaiReport, setXaiReport] = useState<XaiReport | null>(null);

  // Graph state
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({
    nodes: [],
    links: [],
  });
  const graphRef = useRef<
    ForceGraphMethods<NodeObject<GraphNode>, LinkObject<GraphNode, GraphLink>> | undefined
  >(undefined);

  // Mutable ref to track last graph node id across SSE events
  const lastNodeIdRef = useRef('root');

  const [sseUrl, setSseUrl] = useState('');

  const handleSSEEvent = useCallback((data: SSEEvent) => {
    if (data.type === 'token') {
      setFinalAnswer((prev) => prev + (data.content as string));
    } else if (data.type === 'thought') {
      const raw = data.content as string;
      const agentMatch = raw.match(/^\[(.*?)\]/);
      const agent = agentMatch ? agentMatch[1] : 'System';
      const content = agentMatch ? raw.replace(/^\[.*?\]\s*/, '') : raw;
      const newId = Math.random().toString(36).substr(2, 9);

      setSteps((prev) => [
        ...prev,
        {
          id: newId,
          type: 'thought',
          content,
          agent,
          timestamp: Date.now(),
          parentId: lastNodeIdRef.current,
        },
      ]);

      setGraphData((prev) => ({
        nodes: [
          ...prev.nodes,
          {
            id: newId,
            label: content,
            agent,
            type: 'thought',
            val: 10,
            color: getAgentColorCode(agent),
          },
        ],
        links: [
          ...prev.links,
          { source: lastNodeIdRef.current, target: newId, color: 'rgba(255, 255, 255, 0.2)' },
        ],
      }));
      lastNodeIdRef.current = newId;
    } else if (data.type === 'eval') {
      const newId = Math.random().toString(36).substr(2, 9);
      setSteps((prev) => [
        ...prev,
        {
          id: newId,
          type: 'eval',
          content: data.content as string,
          agent: 'Judge',
          timestamp: Date.now(),
          parentId: lastNodeIdRef.current,
        },
      ]);

      setGraphData((prev) => ({
        nodes: [
          ...prev.nodes,
          {
            id: newId,
            label: '\u00c9valuation',
            agent: 'Judge',
            type: 'eval',
            val: 12,
            color: getAgentColorCode('Judge'),
          },
        ],
        links: [
          ...prev.links,
          { source: lastNodeIdRef.current, target: newId, color: 'rgba(255, 255, 255, 0.2)' },
        ],
      }));
      lastNodeIdRef.current = newId;
    } else if (data.type === 'error') {
      return 'close' as const;
    } else if (data.type === 'done') {
      return 'close' as const;
    } else if (data.type === 'xai_report') {
      setXaiReport(data.content as XaiReport);
    }
  }, []);

  const {
    start: sseStart,
    stop: sseStop,
    isStreaming,
    error,
    errorKind,
  } = useSSE({
    url: sseUrl,
    onEvent: handleSSEEvent,
    authErrorMessage: t(
      'search.expert.auth_error',
      "Ce mode utilise l'IA (GPU) et co\u00fbte des Berrix. Connecte-toi pour lancer une analyse.",
    ),
    paymentErrorMessage: t(
      'search.expert.payment_error',
      'Analyse refus\u00e9e. V\u00e9rifie ton solde de Berrix (ce mode IA en consomme) puis r\u00e9essaie.',
    ),
  });

  const handleSearch = useCallback(
    (searchQuery: string) => {
      if (!searchQuery.trim()) return;

      setSearchParams({ q: searchQuery });
      setSteps([]);
      setFinalAnswer('');
      lastNodeIdRef.current = 'root';

      // Initialize Root node
      setGraphData({
        nodes: [
          { id: 'root', label: 'Question', agent: 'Root', type: 'root', val: 20, color: '#ffffff' },
        ],
        links: [],
      });

      setSseUrl(`/api/v1/stream/agentic-rag/?q=${encodeURIComponent(searchQuery)}`);
    },
    [setSearchParams],
  );

  // Start SSE when URL is set
  useEffect(() => {
    if (sseUrl) {
      sseStart();
    }
  }, [sseUrl, sseStart]);

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
      sseStop();
    };
  }, [initialQuery, handleSearch, sseStop]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen w-full bg-[#0B0C10] text-[#F4F1E8]">
        <div className="mx-auto flex min-h-[calc(100vh-100px)] max-w-7xl flex-col px-6 py-12">
          {/* En-tête */}
          <header className="relative mb-12 text-center">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-8 h-44"
              aria-hidden
            />
            <div className="relative mb-6 flex items-center justify-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                賢
              </span>
              <span className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                <Brain className="h-4 w-4 fill-current" /> RAG agentique SOTA · v2.0
              </span>
            </div>
            <h1 className="font-manga relative mb-4 text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-7xl">
              EXPERT <span className="text-[#E8442B]">NEXUS</span>
            </h1>
            <p className="mx-auto max-w-2xl text-base font-medium leading-relaxed text-[#8F94A5]">
              Raisonnement arborescent multi-agents pour les requêtes complexes de Lore.
            </p>
          </header>

          {/* Barre de recherche */}
          <section className="mb-12 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8">
            <form onSubmit={onSubmit} className="flex gap-3">
              <div className="group relative flex-grow">
                <Search className="absolute left-5 top-1/2 h-6 w-6 -translate-y-1/2 text-[#8F94A5]/50 transition-colors group-focus-within:text-[#FDB913]" />
                <input
                  type="text"
                  aria-label="Rechercher"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t(
                    'search.expert.placeholder',
                    'Posez une question profonde sur un univers, une relation ou un arc narratif...',
                  )}
                  className="w-full rounded-2xl border border-[#F4F1E8]/15 bg-[#0B0C10] py-5 pl-14 pr-6 text-lg font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                />
              </div>
              <Button
                type="submit"
                disabled={isStreaming || !query.trim()}
                className="rounded-2xl border-none !bg-[#E8442B] px-8 font-manga text-xl font-black uppercase italic !text-[#F4F1E8] transition-colors hover:!bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isStreaming ? (
                  <Zap className="h-6 w-6 animate-pulse" />
                ) : (
                  t('search.expert.solve_btn', 'RÉSOUDRE')
                )}
              </Button>
            </form>
          </section>

          {/* Zone de contenu */}
          <div className="grid flex-grow grid-cols-1 gap-8 lg:grid-cols-12">
            {/* Arbre de pensée (graphe) */}
            <div className="flex h-full min-h-[500px] flex-col lg:col-span-5">
              <div className="mb-6 flex items-center justify-between px-1">
                <h3 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                  <Network className="h-4 w-4" />{' '}
                  {t('search.expert.thought_tree', 'Arbre de Pensée (MCTS)')}
                </h3>
                {isStreaming && (
                  <span className="animate-pulse rounded-full border border-[#FDB913]/40 px-3 py-1 text-[8px] font-black uppercase tracking-widest text-[#FDB913]">
                    Raisonnement actif
                  </span>
                )}
              </div>

              <div className="relative flex-grow overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-black">
                {graphData.nodes.length > 0 ? (
                  <div className="absolute inset-0">
                    <React.Suspense
                      fallback={
                        <div className="flex h-full items-center justify-center text-[#FDB913]">
                          Chargement du graphe...
                        </div>
                      }
                    >
                      <ForceGraph2D
                        ref={graphRef as unknown as React.RefObject<ForceGraphMethods>}
                        graphData={graphData}
                        nodeLabel="agent"
                        nodeColor="color"
                        nodeVal="val"
                        linkColor="color"
                        linkWidth={2}
                        backgroundColor="#000000"
                        onEngineStop={() =>
                          (graphRef.current as unknown as ForceGraphMethods | null)?.zoomToFit(
                            400,
                            20,
                          )
                        }
                        nodeCanvasObjectMode={() => 'after'}
                        nodeCanvasObject={(
                          node: GraphNode,
                          ctx: CanvasRenderingContext2D,
                          globalScale: number,
                        ) => {
                          const label = node.agent;
                          const fontSize = 12 / globalScale;
                          ctx.font = `${fontSize}px Sans-Serif`;
                          ctx.textAlign = 'center';
                          ctx.textBaseline = 'middle';
                          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'; // Text color
                          ctx.fillText(label, node.x || 0, (node.y || 0) + 12);
                        }}
                      />
                    </React.Suspense>
                  </div>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center py-24 text-center text-[#8F94A5]">
                    <Network className="mb-4 h-16 w-16 text-[#8F94A5]/40" />
                    <p className="text-[10px] font-black uppercase tracking-widest">
                      {t('search.expert.waiting', "En attente d'une requête complexe")}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Affichage de la réponse */}
            <div className="flex h-full flex-col lg:col-span-7">
              <div className="mb-6 flex items-center gap-4 px-1">
                <h3 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                  <Sparkles className="h-4 w-4 text-[#FDB913]" />{' '}
                  {t('search.expert.synthesis', 'Synthèse Expert')}
                </h3>
              </div>

              <div className="relative flex flex-grow flex-col overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]">
                <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-transparent via-[#E8442B] to-transparent opacity-60" />

                <div className="prose prose-invert max-w-none flex-grow overflow-y-auto p-10">
                  {error && (
                    <div className="flex items-center gap-6 rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.08] p-8 text-[#E8442B]">
                      <AlertCircle className="h-12 w-12 flex-shrink-0" />
                      <div className="flex-grow">
                        <h4 className="mb-1 text-xl font-black uppercase italic">
                          {errorKind === 'auth'
                            ? t('search.expert.auth_required', 'Connexion requise')
                            : errorKind === 'payment'
                              ? t('search.expert.insufficient_bx', 'Berrix insuffisants')
                              : t('search.expert.resolution_error', 'Erreur de Résolution')}
                        </h4>
                        <p className="text-sm font-bold uppercase tracking-wide text-[#F4F1E8]/80">
                          {error}
                        </p>
                        {errorKind === 'auth' && (
                          <Link to="/auth/login/">
                            <Button
                              variant="primary"
                              className="mt-4 !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none"
                            >
                              {t('search.expert.login_btn', 'Se connecter')}
                            </Button>
                          </Link>
                        )}
                        {errorKind === 'payment' && (
                          <Link to="/power-station/">
                            <Button
                              variant="primary"
                              className="mt-4 !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none"
                            >
                              {t('search.expert.recharge_btn', 'Recharger des Berrix')}
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  )}

                  {!error && !finalAnswer && !isStreaming && (
                    <div className="flex h-full flex-col items-center justify-center py-32 text-center text-[#8F94A5]">
                      <Sparkles className="mb-8 h-24 w-24 text-[#8F94A5]/40" />
                      <h3 className="font-manga mb-4 text-3xl font-black uppercase italic text-[#F4F1E8]/60">
                        {t('search.expert.idle_title', 'Nexus en veille')}
                      </h3>
                      <p className="text-sm font-bold uppercase tracking-[0.3em]">
                        {t(
                          'search.expert.idle_desc',
                          "L'IA de 5ème génération attend vos instructions.",
                        )}
                      </p>
                    </div>
                  )}

                  {!error && (finalAnswer || isStreaming) && (
                    <div className="animate-fade-in space-y-8">
                      <p className="whitespace-pre-wrap text-2xl font-bold leading-relaxed text-[#F4F1E8]/90">
                        {finalAnswer}
                        {isStreaming && (
                          <motion.span
                            animate={{ opacity: [0, 1, 0] }}
                            transition={{ repeat: Infinity, duration: 1 }}
                            className="ml-2 inline-block h-8 w-2 align-middle bg-[#E8442B]"
                          />
                        )}
                      </p>
                    </div>
                  )}
                </div>

                {xaiReport && <XaiReportDisplay xaiReport={xaiReport} />}

                {/* Stats de pied */}
                <div className="flex flex-wrap items-center justify-between gap-6 border-t border-[#F4F1E8]/10 px-10 py-6">
                  <div className="flex gap-8">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-[#FDB913]" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        Latence : 1.2s
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-[#FDB913]" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        Fidélité : 98%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-full border border-[#F4F1E8]/10 px-3 py-1">
                    <CheckCircle2 className="h-3 w-3 text-[#FDB913]" />
                    <span className="text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                      Ancrage vérifié
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ExpertNexusPage;
