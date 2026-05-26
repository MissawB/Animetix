import React, { useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useGraphData, GraphNode, GraphLink } from './useGraphData';

interface GraphExplorerProps {
  initialId: string;
  initialType: string;
}

export function GraphExplorer({ initialId, initialType }: GraphExplorerProps) {
  const [depth, setDepth] = useState(1);
  const { data, isLoading, error } = useGraphData(initialId, initialType, depth);

  const getNodeColor = (node: GraphNode) => {
    const label = node.labels?.[0] || '';
    switch (label) {
      case 'Anime': return '#ff7f0e';
      case 'Character': return '#2ca02c';
      case 'Game': return '#1f77b4';
      case 'Movie': return '#d62728';
      case 'Manga': return '#9467bd';
      default: return '#7f7f7f';
    }
  };

  const getLabel = (node: GraphNode) => {
    return node.properties?.title || node.properties?.name || node.id || 'Unknown';
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="p-4 bg-gray-800 text-white flex items-center justify-between z-10">
        <h2 className="text-xl font-bold">Graph Explorer</h2>
        <div className="flex items-center space-x-4">
          <label htmlFor="depth-slider" className="text-sm">Depth: {depth}</label>
          <input
            id="depth-slider"
            type="range"
            min="1"
            max="3"
            step="1"
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="w-32 cursor-pointer"
          />
        </div>
      </div>
      
      <div className="flex-grow relative w-full min-h-[600px] bg-gray-900 overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 z-20">
            <span className="text-white text-lg">Loading graph data...</span>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 z-20">
            <span className="text-red-500 text-lg">Error: {error.message}</span>
          </div>
        )}

        <div className="absolute inset-0">
          <ForceGraph2D
            graphData={data}
            nodeAutoColorBy={(node: any) => node.labels?.[0]}
            nodeColor={(node: any) => getNodeColor(node as GraphNode)}
            nodeLabel={(node: any) => getLabel(node as GraphNode)}
            linkLabel={(link: any) => link.type}
            backgroundColor="#111827"
          />
        </div>
      </div>
    </div>
  );
}
