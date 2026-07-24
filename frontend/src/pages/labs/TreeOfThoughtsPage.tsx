import React, { useState, useCallback, useRef, Suspense } from 'react';
import { Network } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import ForceGraph2D, { type ForceGraphMethods } from '../../components/LazyForceGraph2D';

import { useSSE } from '../../hooks/useSSE';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import type {
  ToTNode,
  ToTLink,
  ToTGraphData,
  ToTResponse,
} from '../../features/labs/types/totTypes';

import { ToTSidebarPanel } from './components/ToTSidebarPanel';
import { ToTNodeInspectionModal } from './components/ToTNodeInspectionModal';
import { ToTGuideProtocolSection } from './components/ToTGuideProtocolSection';

const getNodeColor = (type: string) => {
  switch (type) {
    case 'root':
      return '#ffffff';
    case 'selected':
      return '#10b981'; // Emerald-500
    case 'pruned':
      return '#991b1b'; // Red-800
    case 'final':
      return '#fbbf24'; // Yellow-400
    default:
      return '#6b7280';
  }
};

const getNodeSize = (type: string) => {
  switch (type) {
    case 'root':
      return 8;
    case 'selected':
      return 6;
    case 'final':
      return 7;
    case 'pruned':
      return 4;
    default:
      return 5;
  }
};

const TreeOfThoughtsPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<ToTNode | null>(null);
  const [graphData, setGraphData] = useState<ToTGraphData | null>(null);
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);

  // Accumulator ref for progressive graph building during streaming
  const accRef = useRef({
    nodes: [] as ToTNode[],
    links: [] as ToTLink[],
    lastSelectedId: 'root',
  });

  const sseUrl = query.trim() ? `/api/v1/stream/tot/?q=${encodeURIComponent(query)}` : '';

  const handleSSEEvent = useCallback((msg: import('../../hooks/useSSE').SSEEvent) => {
    const acc = accRef.current;
    if (msg.type === 'node_created') {
      const d = msg.data as {
        id: string;
        is_pruned: boolean;
        score: number;
        text: string;
        parent_id?: string;
      };
      const type: ToTNode['type'] = d.id === 'root' ? 'root' : d.is_pruned ? 'pruned' : 'selected';
      acc.nodes.push({
        id: d.id,
        type,
        score: d.score,
        full_text: d.text,
        label: (d.text || '').slice(0, 24),
      });
      if (d.parent_id) acc.links.push({ source: d.parent_id, target: d.id });
      if (!d.is_pruned && d.id !== 'root') acc.lastSelectedId = d.id;
      setGraphData({ nodes: [...acc.nodes], links: [...acc.links] });
    } else if (msg.type === 'final_answer') {
      const d = msg.data as { text: string };
      acc.nodes.push({
        id: 'final',
        type: 'final',
        score: 1.0,
        full_text: d.text,
        label: 'CONCLUSION',
      });
      acc.links.push({ source: acc.lastSelectedId, target: 'final' });
      setGraphData({ nodes: [...acc.nodes], links: [...acc.links] });
      setTimeout(() => fgRef.current?.zoomToFit(400), 300);
      return 'close' as const;
    } else if (msg.type === 'error') {
      return 'close' as const;
    }
  }, []);

  const {
    start: sseStart,
    isStreaming,
    error,
    errorKind,
  } = useSSE({
    url: sseUrl,
    onEvent: handleSSEEvent,
    authErrorMessage:
      "Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour lancer un raisonnement.",
    paymentErrorMessage:
      'Raisonnement refusé. Vérifie ton solde de Berrix (ce mode IA en consomme) puis réessaie.',
  });

  const startStream = useCallback(() => {
    if (!query.trim()) return;
    setSelectedNode(null);
    setGraphData({ nodes: [], links: [] });
    accRef.current = { nodes: [], links: [], lastSelectedId: 'root' };
    sseStart();
  }, [query, sseStart]);

  const totMutation = useMutation<ToTResponse, Error, { query: string }>({
    mutationFn: (body: { query: string }) =>
      apiClient('/api/v1/labs/tot/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      if (data.full_tree) {
        setGraphData(data.full_tree);
        setTimeout(() => {
          if (fgRef.current) {
            fgRef.current.zoomToFit(400);
          }
        }, 500);
      }
    },
  });

  const handleNodeClick = useCallback((node: ToTNode) => {
    setSelectedNode(node);
    if (fgRef.current && node.x !== undefined && node.y !== undefined) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2, 1000);
    }
  }, []);

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="h-[calc(100vh-84px)] w-full flex overflow-hidden relative z-10">
          {/* Input & Controls Sidebar */}
          <ToTSidebarPanel
            query={query}
            setQuery={setQuery}
            isPending={totMutation.isPending}
            isStreaming={isStreaming}
            onGenerateTree={() => totMutation.mutate({ query })}
            onStartStream={startStream}
            error={error}
            errorKind={errorKind}
          />

          {/* Main Visualization Area */}
          <div className="flex-1 relative bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-950/10 via-black to-black">
            {graphData ? (
              <Suspense
                fallback={
                  <div className="flex items-center justify-center h-full text-emerald-500">
                    Loading graph canvas...
                  </div>
                }
              >
                <ForceGraph2D
                  ref={fgRef}
                  graphData={graphData}
                  backgroundColor="rgba(0,0,0,0)"
                  nodeLabel={(node: ToTNode) => `${node.type.toUpperCase()} | Score: ${node.score}`}
                  nodeColor={(node: ToTNode) => getNodeColor(node.type)}
                  nodeRelSize={1}
                  nodeCanvasObject={(
                    node: ToTNode,
                    ctx: CanvasRenderingContext2D,
                    globalScale: number,
                  ) => {
                    const size = getNodeSize(node.type);
                    const color = getNodeColor(node.type);

                    if (node.type === 'selected' || node.type === 'final') {
                      ctx.shadowColor = color;
                      ctx.shadowBlur = 15 / globalScale;
                    } else {
                      ctx.shadowBlur = 0;
                    }

                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI, false);
                    ctx.fill();

                    if (globalScale > 3 || node.type === 'final' || node.type === 'root') {
                      const label =
                        node.type === 'root' ? 'START' : node.type === 'final' ? 'END' : '';
                      if (label) {
                        ctx.font = `${4 / globalScale}px font-black`;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = '#000';
                        ctx.fillText(label, node.x || 0, node.y || 0);
                      }
                    }
                  }}
                  linkColor={() => 'rgba(255, 255, 255, 0.05)'}
                  linkDirectionalParticles={2}
                  linkDirectionalParticleSpeed={0.005}
                  linkDirectionalParticleWidth={2}
                  linkDirectionalParticleColor={(link: ToTLink) => {
                    const targetId =
                      typeof link.target === 'object' ? (link.target as ToTNode).id : link.target;
                    const target = graphData.nodes.find((n) => n.id === targetId);
                    return target?.type === 'selected' || target?.type === 'final'
                      ? '#10b981'
                      : 'rgba(255,255,255,0.1)';
                  }}
                  onNodeClick={handleNodeClick}
                  cooldownTicks={100}
                />
              </Suspense>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center opacity-10">
                <Network className="w-64 h-64 mb-12 animate-pulse" />
                <h2 className="text-6xl font-black italic uppercase manga-font tracking-tighter">
                  WAITING FOR REASONING
                </h2>
              </div>
            )}

            {/* Node Details Overlay Panel */}
            <ToTNodeInspectionModal
              selectedNode={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          </div>
        </div>

        {/* Guide & Protocole */}
        <ToTGuideProtocolSection />
      </AnimatedPage>
    </div>
  );
};

export default TreeOfThoughtsPage;
