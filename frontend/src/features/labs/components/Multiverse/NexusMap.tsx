import React, { useRef, useCallback, useMemo, useState, useEffect } from 'react';
import _ForceGraph2D from 'react-force-graph-2d';

// Handle CommonJS/ESM compatibility for react-force-graph-2d
const ForceGraph2D = (_ForceGraph2D as any).default || _ForceGraph2D;

interface NexusMapProps {
  data: any;
  loadingNodes: any[];
  onDropSeed: (seed: string, x: number, y: number) => void;
  onNodeClick: (node: any) => void;
}

export const NexusMap: React.FC<NexusMapProps> = ({ data, loadingNodes, onDropSeed, onNodeClick }) => {
  const fgRef = useRef<any>(null);
  const [, setFrame] = useState(0);

  // Performance: Use a Set for O(1) lookups in the render loop
  const loadingNodesSet = useMemo(() => new Set(loadingNodes.map(n => n.id)), [loadingNodes]);

  // Animation: Force redraws when there are loading nodes to prevent the pulse from stalling
  useEffect(() => {
    let animId: number;
    if (loadingNodes.length > 0) {
      const step = () => {
        setFrame(f => f + 1);
        animId = requestAnimationFrame(step);
      };
      animId = requestAnimationFrame(step);
    }
    return () => cancelAnimationFrame(animId);
  }, [loadingNodes.length]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const seed = e.dataTransfer.getData('seed');
    if (!fgRef.current || !seed) return;
    
    // Transform client coordinates to graph coordinates
    const { x, y } = fgRef.current.screen2GraphCoords(e.clientX, e.clientY);
    onDropSeed(seed, x, y);
  }, [onDropSeed]);

  return (
    <div 
      className="w-full h-full relative bg-[#05050a]" 
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        nodeLabel="name"
        onNodeClick={onNodeClick}
        nodeRelSize={6}
        nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
            // Schema mismatch fix
            const label = node.name || node.label || 'Unknown Universe';
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;
            
            const isLoading = loadingNodesSet.has(node.id);

            // Correct Canvas Rendering: Pulsing effect (Separate Path)
            if (isLoading) {
                const pulse = (Math.sin(Date.now() / 200) + 1) / 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, 8 + pulse * 4, 0, 2 * Math.PI, false);
                ctx.fillStyle = `rgba(239, 68, 68, ${0.3 + pulse * 0.3})`;
                ctx.fill();
            }

            // Core node (Separate Path)
            ctx.beginPath();
            ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.type === 'genre' ? '#10b981' : '#06b6d4';
            ctx.fill();

            // Label positioning scale-independent
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillText(label, node.x, node.y + 12 / globalScale);
        }}
      />
    </div>
  );
};
