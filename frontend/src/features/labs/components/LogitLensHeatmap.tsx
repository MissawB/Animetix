import React from 'react';

interface LayerTrajectory {
  layer: number;
  top_tokens: string[];
  internal_probabilities: number[];
}

interface Props {
  trajectory: LayerTrajectory[];
}

const LogitLensHeatmap: React.FC<Props> = ({ trajectory }) => {
  return (
    <div className="w-full overflow-x-auto p-4 scrollbar-thin scrollbar-thumb-white/10">
      <div className="flex flex-col gap-1 min-w-max">
        {trajectory.map((layer) => (
          <div key={layer.layer} className="flex items-center gap-3">
            <span className="w-8 text-[8px] font-black text-gray-500 uppercase tracking-tighter">L{layer.layer.toString().padStart(2, '0')}</span>
            <div className="flex gap-1">
              {layer.top_tokens.map((token, idx) => {
                const prob = layer.internal_probabilities[idx];
                return (
                  <div
                    key={idx}
                    className="w-16 h-8 rounded-sm flex items-center justify-center relative group transition-all hover:scale-105 border border-white/5"
                    style={{
                      backgroundColor: `rgba(34, 211, 238, ${prob * 0.8})`,
                    }}
                  >
                    <span className={`text-[9px] font-black italic tracking-tighter truncate px-1 ${prob > 0.5 ? 'text-black' : 'text-cyan-400'}`}>
                      {token}
                    </span>
                    <div className="absolute bottom-full mb-2 hidden group-hover:block bg-black/95 text-[10px] p-2 rounded border border-cyan-500/30 z-30 pointer-events-none shadow-2xl">
                      <div className="font-black text-cyan-400 uppercase tracking-widest mb-1 text-[8px]">Synapse Data</div>
                      <div className="text-white">Token: <span className="text-cyan-200">{token}</span></div>
                      <div className="text-white">Confidence: <span className="text-cyan-200">{(prob * 100).toFixed(1)}%</span></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LogitLensHeatmap;
