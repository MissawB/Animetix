import React from 'react';
import { Zap, Flame } from 'lucide-react';
import { Card } from '../ui/Card';

interface SynapticSimulationPanelProps {
  concepts: string[];
  selectedSpikes: number[];
  toggleSpike: (idx: number) => void;
  currentLogs: string[];
}

export const SynapticSimulationPanel: React.FC<SynapticSimulationPanelProps> = ({
  concepts,
  selectedSpikes,
  toggleSpike,
  currentLogs,
}) => {
  return (
    <div className="space-y-8">
      {/* Spike grid */}
      <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl">
        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-500 animate-pulse" /> Trigger Neural Spikes
        </h3>
        <div className="grid grid-cols-5 gap-2">
          {concepts.map((concept, idx) => (
            <button
              key={concept}
              onClick={() => toggleSpike(idx)}
              className={`p-3 rounded-xl border text-center flex flex-col justify-center items-center h-16 transition-all hover:scale-105 ${
                selectedSpikes.includes(idx)
                  ? 'bg-red-600 border-red-400 text-white shadow-[0_0_20px_rgba(220,38,38,0.2)]'
                  : 'bg-black/40 border-white/5 text-gray-500 hover:border-white/10'
              }`}
            >
              <span className="text-[8px] font-black uppercase tracking-wider block">{concept}</span>
              {selectedSpikes.includes(idx) && (
                <span className="text-[7px] font-black font-mono text-yellow-300 mt-1">FIRE</span>
              )}
            </button>
          ))}
        </div>
      </Card>

      {/* STDP Logs */}
      <Card padding="lg" className="bg-black border-white/5 flex flex-col min-h-[220px]">
        <span className="text-[9px] font-black uppercase opacity-35 block mb-4 tracking-widest flex items-center gap-2">
          <Flame className="w-4 h-4 text-orange-500" /> STDP Log Activity
        </span>
        <div className="space-y-3 overflow-y-auto max-h-[190px] pr-2 custom-scrollbar">
          {currentLogs.map((log, idx) => (
            <div
              key={idx}
              className="font-mono text-[8px] text-yellow-400 flex items-start gap-2 p-2 bg-white/5 rounded-lg border border-white/5"
            >
              <Flame className="w-3 h-3 text-red-500 shrink-0" />
              <span className="leading-tight">{log}</span>
            </div>
          ))}
          {currentLogs.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center py-10 opacity-20 text-center">
              <span className="text-[9px] font-black uppercase tracking-widest block italic">
                No synaptic evolution recorded
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
