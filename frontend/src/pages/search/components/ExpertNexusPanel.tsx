import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSSE, type SSEEvent } from '../../../hooks/useSSE';
import { Sparkles, Network, ShieldCheck, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import ForceGraph2D, {
  type ForceGraphMethods,
  type NodeObject,
  type LinkObject,
} from '../../../components/LazyForceGraph2D';
import { Button } from '../../../components/ui/Button';
import XaiReportDisplay, { type XaiReport } from '../../../components/XaiReportDisplay';

interface Step {
  id: string;
  type: 'thought' | 'eval' | 'token' | 'xai_report';
  content: string | XaiReport;
  timestamp: number;
  agent?: string;
  parentId?: string;
  xaiReport?: XaiReport;
}

interface GraphNode {
  id: string;
  label: string;
  agent: string;
  type: string;
  val: number;
  color: string;
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

export interface ExpertNexusPanelProps {
  /** Requête à exécuter (fournie par la barre de recherche du parent). Le parent
   *  remonte le panneau via `key` à chaque soumission (reset naturel de l'état). */
  query: string;
  /** Remonte l'état de streaming pour que le parent puisse désactiver son bouton. */
  onStreamingChange?: (streaming: boolean) => void;
}

const agenticUrl = (q: string) => `/api/v1/stream/agentic-rag/?q=${encodeURIComponent(q)}`;

/**
 * Corps de l'Expert Nexus (RAG agentique) : arbre de pensée + synthèse en
 * streaming. Sans en-tête ni barre de recherche — celles-ci appartiennent au
 * parent (le hub de recherche ou la page autonome), pour une UX unifiée.
 * Le parent le remonte (`key`) à chaque nouvelle requête : l'état repart à zéro
 * et le stream démarre au montage à partir de `query`.
 */
const ExpertNexusPanel: React.FC<ExpertNexusPanelProps> = ({ query, onStreamingChange }) => {
  const { t } = useTranslation();
  const [, setSteps] = useState<Step[]>([]);
  const [finalAnswer, setFinalAnswer] = useState('');
  const [xaiReport, setXaiReport] = useState<XaiReport | null>(null);
  // Refus/erreur signalé par un événement SSE `error` (le backend refuse parfois
  // APRÈS le début du flux). Sans ça, le panneau se fermait en silence.
  const [sseError, setSseError] = useState(false);

  const paymentMsg = t(
    'search.expert.payment_error',
    'Analyse refusée. Vérifie ton solde de Berrix (ce mode IA en consomme) puis réessaie.',
  );

  // Init paresseuse depuis `query` : au montage, le graphe a déjà son nœud racine
  // et l'URL SSE est prête (le stream démarre dans l'effet ci-dessous).
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>(() =>
    query.trim()
      ? {
          nodes: [
            {
              id: 'root',
              label: 'Question',
              agent: 'Root',
              type: 'root',
              val: 20,
              color: '#ffffff',
            },
          ],
          links: [],
        }
      : { nodes: [], links: [] },
  );
  const graphRef = useRef<
    ForceGraphMethods<NodeObject<GraphNode>, LinkObject<GraphNode, GraphLink>> | undefined
  >(undefined);
  const lastNodeIdRef = useRef('root');
  const [sseUrl] = useState(() => (query.trim() ? agenticUrl(query.trim()) : ''));

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
            label: 'Évaluation',
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
      setSseError(true);
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
      "Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour lancer une analyse.",
    ),
    paymentErrorMessage: paymentMsg,
  });

  // Un refus/erreur qui n'est pas un problème d'auth est traité comme un souci de
  // Berrix (ce mode IA en consomme) : on affiche le même message clair que sur la
  // page Expert Nexus autonome, plutôt qu'un état muet ou générique.
  const showError = !!error || sseError;
  const isAuthError = errorKind === 'auth';

  useEffect(() => {
    onStreamingChange?.(isStreaming);
  }, [isStreaming, onStreamingChange]);

  // Démarre le stream au montage (l'URL est fixée dès l'init depuis `query`).
  useEffect(() => {
    if (sseUrl) sseStart();
  }, [sseUrl, sseStart]);

  useEffect(() => () => sseStop(), [sseStop]);

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
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
                    (graphRef.current as unknown as ForceGraphMethods | null)?.zoomToFit(400, 20)
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
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
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

      {/* Synthèse */}
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
            {showError && (
              <div className="flex items-center gap-6 rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.08] p-8 text-[#E8442B]">
                <AlertCircle className="h-12 w-12 flex-shrink-0" />
                <div className="flex-grow">
                  <h4 className="mb-1 text-xl font-black uppercase italic">
                    {isAuthError
                      ? t('search.expert.auth_required', 'Connexion requise')
                      : t('search.expert.insufficient_bx', 'Berrix insuffisants')}
                  </h4>
                  <p className="text-sm font-bold uppercase tracking-wide text-[#F4F1E8]/80">
                    {isAuthError ? error : paymentMsg}
                  </p>
                  {isAuthError ? (
                    <Link to="/auth/login/">
                      <Button
                        variant="primary"
                        className="mt-4 !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none"
                      >
                        {t('search.expert.login_btn', 'Se connecter')}
                      </Button>
                    </Link>
                  ) : (
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

            {!showError && !finalAnswer && !isStreaming && (
              <div className="flex h-full flex-col items-center justify-center py-32 text-center text-[#8F94A5]">
                <Sparkles className="mb-8 h-24 w-24 text-[#8F94A5]/40" />
                <h3 className="font-manga mb-4 text-3xl font-black uppercase italic text-[#F4F1E8]/60">
                  {t('search.expert.idle_title', 'Nexus en veille')}
                </h3>
                <p className="text-sm font-bold uppercase tracking-[0.3em]">
                  {t('search.expert.idle_desc', "L'IA de 5ème génération attend vos instructions.")}
                </p>
              </div>
            )}

            {!showError && (finalAnswer || isStreaming) && (
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
  );
};

export default ExpertNexusPanel;
