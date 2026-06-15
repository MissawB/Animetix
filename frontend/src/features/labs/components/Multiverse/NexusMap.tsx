import React, { useRef, useCallback } from 'react';
import _ForceGraph2D from 'react-force-graph-2d';
const ForceGraph2D = (_ForceGraph2D as any).default || _ForceGraph2D;

interface NexusMapProps {
  data: any;
  loadingNodes: any[];
  onDropSeed: (seed: string, x: number, y: number) => void;
  onNodeClick: (node: any) => void;
}

export const NexusMap: React.FC<NexusMapProps> = ({ data, loadingNodes, onDropSeed, onNodeClick }) => {
  const fgRef = useRef<any>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const seed = e.dataTransfer.getData('seed');
    if (!fgRef.current) return;
    
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
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;
            
            // Background circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.type === 'genre' ? '#10b981' : '#06b6d4';
            
            // Pulsing effect for loading/latent nodes
            const isLoading = loadingNodes.some(ln => ln.id === node.id);
            if (isLoading) {
                const pulse = (Math.sin(Date.now() / 200) + 1) / 2;
                ctx.fillStyle = `rgba(239, 68, 68, ${0.5 + pulse * 0.5})`;
                ctx.arc(node.x, node.y, 8 + pulse * 4, 0, 2 * Math.PI, false);
            }
            
            ctx.fill();

            // Label
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillText(label, node.x, node.y + 10);
        }}
      />
    </div>
  );
};
