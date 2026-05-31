import React from 'react';
import { usePersonalizationStore } from '../../store/personalizationStore';
import { Sparkles, Sliders, Type, Palette, Zap, Info } from 'lucide-react';

const ARCHETYPES = [
  "shonen_hero", "seinen_mystery", "cyberpunk", "tsundere", "kuudere", "yandere",
  "shonen", "seinen", "mahou_shoujo", "isekai", "slice_of_life", "mecha",
  "horror", "fantasy", "romance", "psychological", "sports"
];

export const PersonalizationPanel: React.FC = () => {
  const { settings, updateSettings, isPersonalizationEnabled, setPersonalizationEnabled } = usePersonalizationStore();

  if (!isPersonalizationEnabled) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-dashed border-gray-300 dark:border-white/10 text-center">
        <Sparkles className="w-8 h-8 text-gray-400 mx-auto mb-2 opacity-50" />
        <p className="text-sm text-gray-500 italic mb-4">Hyper-Personalization is currently disabled.</p>
        <button 
          onClick={() => setPersonalizationEnabled(true)}
          className="px-4 py-2 bg-blue-500 text-white text-xs font-black italic uppercase tracking-widest rounded-lg hover:bg-blue-600 transition"
        >
          Enable System
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mode Selection */}
      <div className="flex items-center justify-between p-3 bg-white dark:bg-navy-800 rounded-xl border border-gray-100 dark:border-white/5 shadow-sm">
        <div className="flex items-center gap-3">
          <Zap className={`w-5 h-5 ${settings.mode === 'auto' ? 'text-yellow-400 animate-pulse' : 'text-gray-400'}`} />
          <div>
            <p className="text-xs font-black uppercase tracking-tighter italic">Personalization Mode</p>
            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
              {settings.mode === 'auto' ? 'Autonomous Evolution' : 'Manual Selection'}
            </p>
          </div>
        </div>
        <div className="flex bg-gray-100 dark:bg-navy-950 p-1 rounded-lg">
          <button 
            onClick={() => updateSettings({ mode: 'auto' })}
            className={`px-3 py-1 text-[10px] font-black uppercase rounded-md transition ${settings.mode === 'auto' ? 'bg-white dark:bg-navy-800 shadow-sm text-blue-500' : 'text-gray-400 hover:text-gray-600'}`}
          >
            Auto
          </button>
          <button 
            onClick={() => updateSettings({ mode: 'manual' })}
            className={`px-3 py-1 text-[10px] font-black uppercase rounded-md transition ${settings.mode === 'manual' ? 'bg-white dark:bg-navy-800 shadow-sm text-orange-500' : 'text-gray-400 hover:text-gray-600'}`}
          >
            Manual
          </button>
        </div>
      </div>

      {/* Manual Selection Grid */}
      {settings.mode === 'manual' && (
        <div className="grid grid-cols-2 gap-2">
          {ARCHETYPES.map(arch => (
            <button
              key={arch}
              onClick={() => updateSettings({ manual_archetype: arch })}
              className={`p-2 text-[10px] font-black uppercase tracking-widest rounded-lg border transition ${settings.manual_archetype === arch ? 'bg-orange-500/10 border-orange-500 text-orange-500' : 'bg-gray-50 dark:bg-navy-900 border-gray-100 dark:border-white/5 text-gray-400 hover:bg-gray-100'}`}
            >
              {arch.replace('_', ' ')}
            </button>
          ))}
        </div>
      )}

      {/* Intensity Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-500" />
            <p className="text-xs font-black uppercase tracking-widest">Aura Intensity</p>
          </div>
          <span className="text-xs font-mono font-bold text-blue-500">{Math.round(settings.intensity_multiplier * 100)}%</span>
        </div>
        <input 
          type="range" 
          min="0" 
          max="2" 
          step="0.1" 
          value={settings.intensity_multiplier}
          onChange={(e) => updateSettings({ intensity_multiplier: parseFloat(e.target.value) })}
          className="w-full h-1.5 bg-gray-200 dark:bg-navy-900 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
        <div className="flex justify-between text-[8px] font-bold text-gray-400 uppercase tracking-widest">
          <span>Subtle</span>
          <span>Normal</span>
          <span>Overdrive</span>
        </div>
      </div>

      {/* Feature Toggles */}
      <div className="grid grid-cols-3 gap-2">
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, aura: !settings.features.aura } })}
          className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition ${settings.features.aura ? 'bg-brand-accent/10 border-brand-accent text-brand-accent' : 'bg-gray-50 dark:bg-navy-900 border-gray-100 dark:border-white/5 text-gray-400 opacity-50'}`}
        >
          <Sparkles className="w-4 h-4" />
          <span className="text-[9px] font-black uppercase tracking-widest">Aura</span>
        </button>
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, font: !settings.features.font } })}
          className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition ${settings.features.font ? 'bg-blue-500/10 border-blue-500 text-blue-500' : 'bg-gray-50 dark:bg-navy-900 border-gray-100 dark:border-white/5 text-gray-400 opacity-50'}`}
        >
          <Type className="w-4 h-4" />
          <span className="text-[9px] font-black uppercase tracking-widest">Fonts</span>
        </button>
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, accent: !settings.features.accent } })}
          className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition ${settings.features.accent ? 'bg-purple-500/10 border-purple-500 text-purple-500' : 'bg-gray-50 dark:bg-navy-900 border-gray-100 dark:border-white/5 text-gray-400 opacity-50'}`}
        >
          <Palette className="w-4 h-4" />
          <span className="text-[9px] font-black uppercase tracking-widest">Accent</span>
        </button>
      </div>

      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-500/10 flex gap-3">
        <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
        <p className="text-[10px] text-blue-700 dark:text-blue-300 font-medium leading-relaxed italic">
          Your UI evolves dynamically based on your behavior. Manual mode allows you to "lock" a specific archetype, while Auto mode lets the system drift naturally.
        </p>
      </div>
    </div>
  );
};
