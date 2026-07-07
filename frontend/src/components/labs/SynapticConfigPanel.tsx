import React from 'react';
import { Sliders, Settings, Compass, Loader2 } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { PersonalizationFeatures } from '../../types';

const ARCHETYPES = [
  { id: 'shonen_hero', name: 'Shonen Hero' },
  { id: 'seinen_mystery', name: 'Seinen Mystery' },
  { id: 'cyberpunk', name: 'Cyberpunk Rebel' },
  { id: 'tsundere', name: 'Tsundere' },
  { id: 'kuudere', name: 'Kuudere' },
  { id: 'yandere', name: 'Yandere' },
  { id: 'shonen', name: 'Shonen Base' },
  { id: 'seinen', name: 'Seinen Base' },
  { id: 'mahou_shoujo', name: 'Mahou Shoujo' },
  { id: 'isekai', name: 'Isekai' },
  { id: 'slice_of_life', name: 'Slice of Life' },
  { id: 'mecha', name: 'Mecha Pilot' },
  { id: 'horror', name: 'Horror / Creepy' },
  { id: 'fantasy', name: 'Fantasy' },
  { id: 'romance', name: 'Romance' },
  { id: 'psychological', name: 'Psychological' },
  { id: 'sports', name: 'Sports Athlete' },
];

interface SynapticConfigPanelProps {
  tauPlus: number;
  setTauPlus: (v: number) => void;
  tauMinus: number;
  setTauMinus: (v: number) => void;
  mode: 'auto' | 'manual';
  setMode: (m: 'auto' | 'manual') => void;
  manualArchetype: string;
  setManualArchetype: (a: string) => void;
  intensityMult: number;
  setIntensityMult: (i: number) => void;
  features: PersonalizationFeatures;
  setFeatures: (f: PersonalizationFeatures) => void;
  handleApplyConfig: () => void;
  isConfigPending: boolean;
}

export const SynapticConfigPanel: React.FC<SynapticConfigPanelProps> = ({
  tauPlus,
  setTauPlus,
  tauMinus,
  setTauMinus,
  mode,
  setMode,
  manualArchetype,
  setManualArchetype,
  intensityMult,
  setIntensityMult,
  features,
  setFeatures,
  handleApplyConfig,
  isConfigPending,
}) => {
  return (
    <div className="space-y-8">
      {/* Plasticity Config Card */}
      <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-6 opacity-5">
          <Sliders className="w-24 h-24" />
        </div>
        
        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
          <Settings className="w-4 h-4 text-red-500" /> Plasticity Parameters
        </h3>

        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex justify-between items-center px-1">
              <label htmlFor="tau-plus-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">
                LTP Time Constant (τ+)
              </label>
              <span className="text-xs font-mono text-red-500 font-bold">{tauPlus.toFixed(1)} ms</span>
            </div>
            <input
              id="tau-plus-slider"
              aria-label="Constante de temps LTP (τ+)"
              type="range"
              min="5.0"
              max="50.0"
              step="1.0"
              value={tauPlus}
              onChange={(e) => setTauPlus(parseFloat(e.target.value))}
              className="w-full accent-red-600 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center px-1">
              <label htmlFor="tau-minus-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">
                LTD Time Constant (τ-)
              </label>
              <span className="text-xs font-mono text-red-500 font-bold">{tauMinus.toFixed(1)} ms</span>
            </div>
            <input
              id="tau-minus-slider"
              aria-label="Constante de temps LTD (τ-)"
              type="range"
              min="5.0"
              max="50.0"
              step="1.0"
              value={tauMinus}
              onChange={(e) => setTauMinus(parseFloat(e.target.value))}
              className="w-full accent-red-600 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
            />
          </div>
        </div>
      </Card>

      {/* Archetype Drift Config Card */}
      <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl relative overflow-hidden">
        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
          <Compass className="w-4 h-4 text-red-500" /> Archetype Drift Override
        </h3>

        <div className="space-y-6">
          {/* Mode Switch */}
          <div className="flex items-center justify-between p-2 bg-black/40 rounded-xl border border-white/5">
            <span className="text-[9px] font-black uppercase tracking-widest opacity-40">Drift Mode</span>
            <div className="flex gap-1">
              <button
                onClick={() => setMode('auto')}
                className={`px-3 py-1 text-[8px] font-black uppercase rounded-lg transition-colors ${
                  mode === 'auto' ? 'bg-red-600 text-white' : 'bg-transparent text-white/40'
                }`}
              >
                Auto
              </button>
              <button
                onClick={() => setMode('manual')}
                className={`px-3 py-1 text-[8px] font-black uppercase rounded-lg transition-colors ${
                  mode === 'manual' ? 'bg-red-600 text-white' : 'bg-transparent text-white/40'
                }`}
              >
                Manual
              </button>
            </div>
          </div>

          {/* Manual Archetype Dropdown */}
          {mode === 'manual' && (
            <div className="space-y-2">
              <label htmlFor="archetype-select" className="text-[9px] font-black opacity-40 uppercase tracking-widest">
                Select Archetype
              </label>
              <select
                id="archetype-select"
                value={manualArchetype}
                onChange={(e) => setManualArchetype(e.target.value)}
                className="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-xs font-bold text-white accent-red-600 focus:outline-none"
              >
                {ARCHETYPES.map((arch) => (
                  <option key={arch.id} value={arch.id} className="bg-[#0a0a12] text-white">
                    {arch.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Intensity Multiplier */}
          <div className="space-y-2">
            <div className="flex justify-between items-center px-1">
              <label htmlFor="intensity-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">
                Intensity Multiplier
              </label>
              <span className="text-xs font-mono text-red-500 font-bold">{intensityMult.toFixed(1)}x</span>
            </div>
            <input
              id="intensity-slider"
              aria-label="Multiplicateur d'intensité"
              type="range"
              min="0.0"
              max="3.0"
              step="0.1"
              value={intensityMult}
              onChange={(e) => setIntensityMult(parseFloat(e.target.value))}
              className="w-full accent-red-600 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
            />
          </div>

          {/* Features Switches */}
          <div className="space-y-3">
            <span className="text-[9px] font-black opacity-40 uppercase tracking-widest block">
              Active Override Features
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setFeatures({ ...features, aura: !features.aura })}
                className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${
                  features.aura ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'
                }`}
              >
                Aura
              </button>
              <button
                onClick={() => setFeatures({ ...features, accent: !features.accent })}
                className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${
                  features.accent ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'
                }`}
              >
                Accent
              </button>
              <button
                onClick={() => setFeatures({ ...features, font: !features.font })}
                className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${
                  features.font ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'
                }`}
              >
                Font
              </button>
            </div>
          </div>

          {/* Sync Button */}
          <Button
            onClick={handleApplyConfig}
            disabled={isConfigPending}
            className="w-full bg-red-600 hover:bg-red-500 py-3 text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95"
          >
            {isConfigPending ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Apply Parameters'}
          </Button>
        </div>
      </Card>
    </div>
  );
};
