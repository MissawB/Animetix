import React from 'react';
import { Layers, Loader2 } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface SynapticWeightMatrixProps {
  concepts: string[];
  currentW: number[][];
  lr: number;
  setLr: (v: number) => void;
  handleSimulate: () => void;
  isSimulationPending: boolean;
  selectedSpikes: number[];
}

export const SynapticWeightMatrix: React.FC<SynapticWeightMatrixProps> = ({
  concepts,
  currentW,
  lr,
  setLr,
  handleSimulate,
  isSimulationPending,
  selectedSpikes,
}) => {
  return (
    <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl flex flex-col min-h-[380px]">
      <span className="text-[10px] font-black uppercase opacity-30 block mb-6 tracking-widest flex items-center gap-2">
        <Layers className="w-4 h-4" /> Synaptic Weight Matrix (W)
      </span>
      <div className="grid grid-cols-10 gap-1.5 flex-1 items-center justify-center max-w-[380px] mx-auto">
        {currentW.map((row: number[], rIdx: number) =>
          row.map((val: number, cIdx: number) => (
            <div
              key={`${rIdx}-${cIdx}`}
              style={{
                backgroundColor: `rgba(${Math.floor(val * 255)}, 100, 239, ${0.08 + val * 0.92})`,
              }}
              className={`aspect-square w-7 rounded-md border border-white/5 flex items-center justify-center text-[7px] font-black font-mono transition-all duration-300 ${
                val > 0.5 ? 'text-white' : 'text-white/20'
              }`}
              title={`${concepts[rIdx] || `C${rIdx}`} -> ${concepts[cIdx] || `C${cIdx}`} : ${val.toFixed(2)}`}
            >
              {val > 0 ? val.toFixed(1) : '0'}
            </div>
          ))
        )}
      </div>

      {/* Simulator Trigger */}
      <div className="mt-6 flex gap-4">
        <div className="flex-grow space-y-1">
          <div className="flex justify-between items-center px-1">
            <label htmlFor="learning-rate-slider" className="text-[8px] font-black opacity-30 uppercase tracking-widest">
              Step Learning Rate (η)
            </label>
            <span className="text-[9px] font-mono text-red-500 font-bold">{lr.toFixed(3)}</span>
          </div>
          <input
            id="learning-rate-slider"
            aria-label="Taux d'apprentissage par étape (η)"
            type="range"
            min="0.01"
            max="0.2"
            step="0.01"
            value={lr}
            onChange={(e) => setLr(parseFloat(e.target.value))}
            className="w-full accent-red-600 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
          />
        </div>
        <Button
          onClick={handleSimulate}
          disabled={isSimulationPending}
          className="bg-red-600 hover:bg-red-500 text-white font-black italic uppercase tracking-wider text-xs px-6 py-4 rounded-xl shadow-lg transition-all active:scale-95"
        >
          {isSimulationPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Simuler'}
        </Button>
      </div>
    </Card>
  );
};
