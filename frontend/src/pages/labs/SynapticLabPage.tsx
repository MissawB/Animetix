import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Activity,
  Flame,
  Loader2,
  Zap,
  Layers,
  Brain,
  Sparkles,
  Settings,
  Sliders,
  Compass
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { PlasticityResult } from '../../types';

interface PlasticityConfig {
  tau_plus: number;
  tau_minus: number;
  num_concepts: number;
}

interface PersonalizationFeatures {
  aura: boolean;
  font: boolean;
  accent: boolean;
}

interface PersonalizationSettings {
  mode: 'auto' | 'manual';
  intensity_multiplier: number;
  manual_archetype?: string;
  features?: PersonalizationFeatures;
}

interface CurrentArchetype {
  id: string;
  accent: string;
  aura_type: string;
  intensity: number;
  font_vibe: string;
}

interface UnifiedPlasticityState {
  status: string;
  weights: number[][];
  concepts: string[];
  plasticity_config: PlasticityConfig;
  personalization_settings: PersonalizationSettings;
  current_archetype: CurrentArchetype;
}

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

const SynapticLabPage: React.FC = () => {
  const { t } = useTranslation();
  
  // React Query Fetch Unified State
  const { data: state, isLoading, isError, refetch } = useQuery<UnifiedPlasticityState>({
    queryKey: ['singularity-lab-state'],
    queryFn: () => apiClient('/api/v1/singularity-lab/'),
  });

  // Local Form Config state
  const [tauPlus, setTauPlus] = useState(20.0);
  const [tauMinus, setTauMinus] = useState(20.0);
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [manualArchetype, setManualArchetype] = useState('shonen_hero');
  const [intensityMult, setIntensityMult] = useState(1.0);
  const [features, setFeatures] = useState<PersonalizationFeatures>({
    aura: true,
    font: true,
    accent: true,
  });

  // Simulation parameters
  const [selectedSpikes, setSelectedSpikes] = useState<number[]>([]);
  const [lr, setLr] = useState(0.05);
  const [plasticityResult, setPlasticityResult] = useState<PlasticityResult | null>(null);

  // Sync parameters on data fetch: reset the local form whenever the server
  // state *content* changes. Done during render (React's "adjusting state when
  // a prop changes" pattern) rather than in an effect. We key on a value
  // signature instead of object identity so a new-but-equal reference (e.g.
  // react-query without structural sharing, or a remock in tests) doesn't loop.
  const stateSig = state
    ? JSON.stringify({ c: state.plasticity_config, p: state.personalization_settings })
    : null;
  const [syncedSig, setSyncedSig] = useState<string | null>(null);
  if (state && stateSig !== syncedSig) {
    setSyncedSig(stateSig);
    setTauPlus(state.plasticity_config.tau_plus);
    setTauMinus(state.plasticity_config.tau_minus);
    setMode(state.personalization_settings.mode || 'auto');
    setManualArchetype(state.personalization_settings.manual_archetype || 'shonen_hero');
    setIntensityMult(state.personalization_settings.intensity_multiplier ?? 1.0);
    if (state.personalization_settings.features) {
      setFeatures(state.personalization_settings.features);
    }
  }

  // Mutations
  const configMutation = useMutation<UnifiedPlasticityState, Error, {
    action: string;
    tau_plus: number;
    tau_minus: number;
    mode: 'auto' | 'manual';
    manual_archetype: string;
    intensity_multiplier: number;
    features: PersonalizationFeatures;
  }>({
    mutationFn: (body) => 
      apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
      }),
    onSuccess: () => {
      refetch();
    }
  });

  const plasticityMutation = useMutation<PlasticityResult, Error, { action: string; learning_rate: number; trigger_spikes: number[] }>({
    mutationFn: (body) => 
      apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
      }),
    onSuccess: (data) => {
      setPlasticityResult(data);
      refetch();
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-12 h-12 animate-spin text-red-500 mb-4" />
        <p className="text-sm font-black uppercase tracking-[0.2em] opacity-40">Loading Synaptic Matrix...</p>
      </div>
    );
  }

  if (isError || !state) {
    return (
      <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center text-white text-center">
        <Brain className="w-16 h-16 text-red-500 mb-6 animate-pulse" />
        <h2 className="text-3xl font-black italic manga-font uppercase mb-2">Desynchronisation Cognitive</h2>
        <p className="text-white/40 uppercase font-bold tracking-widest mb-6">Impossible de se connecter au lab de plasticité.</p>
        <Button onClick={() => refetch()} className="bg-red-600 hover:bg-red-500">Réessayer</Button>
      </div>
    );
  }

  const concepts = state.concepts || [
    'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
    'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
  ];

  const currentW = plasticityResult?.weights || state.weights;
  const currentLogs = plasticityResult?.stdp_log || [];

  const toggleSpike = (idx: number) => {
    if (selectedSpikes.includes(idx)) {
      setSelectedSpikes(selectedSpikes.filter(i => i !== idx));
    } else {
      setSelectedSpikes([...selectedSpikes, idx]);
    }
  };

  const handleApplyConfig = () => {
    configMutation.mutate({
      action: 'update_config',
      tau_plus: tauPlus,
      tau_minus: tauMinus,
      mode,
      manual_archetype: manualArchetype,
      intensity_multiplier: intensityMult,
      features
    });
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20 pb-16">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-400 mb-4">
                  <Activity className="w-3 h-3 animate-pulse" /> Dynamic Plasticity Dashboard
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  {t('labs.plasticity.title', 'PLASTICITY').split(' ')[0]} <span className="text-red-500 text-glow">{t('labs.plasticity.title', 'LAB').split(' ')[1] || 'LAB'}</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Configuration de la plasticité cognitive et ajustement du drift d'archétype.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* Configuration Column */}
              <div className="lg:col-span-4 space-y-8">
                  
                  {/* Plasticity Config Card */}
                  <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-6 opacity-5">
                          <Sliders className="w-24 h-24" />
                      </div>
                      
                      <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                          <Settings className="w-4 h-4 text-red-500" /> Plasticity Parameters
                      </h3>

                      <div className="space-y-6">
                          {/* Sliders */}
                          <div className="space-y-2">
                              <div className="flex justify-between items-center px-1">
                                  <label htmlFor="tau-plus-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">LTP Time Constant (τ+)</label>
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
                                  <label htmlFor="tau-minus-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">LTD Time Constant (τ-)</label>
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
                                      className={`px-3 py-1 text-[8px] font-black uppercase rounded-lg transition-colors ${mode === 'auto' ? 'bg-red-600 text-white' : 'bg-transparent text-white/40'}`}
                                  >
                                      Auto
                                  </button>
                                  <button 
                                      onClick={() => setMode('manual')}
                                      className={`px-3 py-1 text-[8px] font-black uppercase rounded-lg transition-colors ${mode === 'manual' ? 'bg-red-600 text-white' : 'bg-transparent text-white/40'}`}
                                  >
                                      Manual
                                  </button>
                              </div>
                          </div>

                          {/* Manual Archetype Dropdown */}
                          {mode === 'manual' && (
                              <div className="space-y-2">
                                  <label htmlFor="archetype-select" className="text-[9px] font-black opacity-40 uppercase tracking-widest">Select Archetype</label>
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
                                  <label htmlFor="intensity-slider" className="text-[9px] font-black opacity-40 uppercase tracking-widest">Intensity Multiplier</label>
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
                              <span className="text-[9px] font-black opacity-40 uppercase tracking-widest block">Active Override Features</span>
                              <div className="grid grid-cols-3 gap-2">
                                  <button 
                                      onClick={() => setFeatures({ ...features, aura: !features.aura })}
                                      className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${features.aura ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'}`}
                                  >
                                      Aura
                                  </button>
                                  <button 
                                      onClick={() => setFeatures({ ...features, accent: !features.accent })}
                                      className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${features.accent ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'}`}
                                  >
                                      Accent
                                  </button>
                                  <button 
                                      onClick={() => setFeatures({ ...features, font: !features.font })}
                                      className={`p-2 rounded-xl border text-[8px] font-black uppercase transition-colors ${features.font ? 'border-red-500 bg-red-600/10 text-red-400' : 'border-white/5 bg-black/20 text-white/30'}`}
                                  >
                                      Font
                                  </button>
                              </div>
                          </div>

                          {/* Sync Button */}
                          <Button 
                              onClick={handleApplyConfig}
                              disabled={configMutation.isPending}
                              className="w-full bg-red-600 hover:bg-red-500 py-3 text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95"
                          >
                              {configMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Apply Parameters'}
                          </Button>
                      </div>
                  </Card>
              </div>

              {/* Central Neural Matrix Core */}
              <div className="lg:col-span-5 space-y-8">
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

                  {/* Heatmap Matrix */}
                  <Card padding="lg" className="bg-navy-950/40 border-white/10 rounded-[2rem] shadow-2xl flex flex-col min-h-[380px]">
                      <span className="text-[10px] font-black uppercase opacity-30 block mb-6 tracking-widest flex items-center gap-2">
                          <Layers className="w-4 h-4" /> Synaptic Weight Matrix (W)
                      </span>
                      <div className="grid grid-cols-10 gap-1.5 flex-1 items-center justify-center max-w-[380px] mx-auto">
                          {currentW.map((row: number[], rIdx: number) => row.map((val: number, cIdx: number) => (
                              <div 
                                  key={`${rIdx}-${cIdx}`} 
                                  style={{ backgroundColor: `rgba(${Math.floor(val * 255)}, 100, 239, ${0.08 + val * 0.92})` }} 
                                  className={`aspect-square w-7 rounded-md border border-white/5 flex items-center justify-center text-[7px] font-black font-mono transition-all duration-300 ${val > 0.5 ? 'text-white' : 'text-white/20'}`}
                                  title={`${concepts[rIdx]} -> ${concepts[cIdx]} : ${val.toFixed(2)}`}
                              >
                                  {val > 0 ? val.toFixed(1) : '0'}
                              </div>
                          )))}
                      </div>

                      {/* Simulator Trigger */}
                      <div className="mt-6 flex gap-4">
                          <div className="flex-grow space-y-1">
                              <div className="flex justify-between items-center px-1">
                                  <label htmlFor="learning-rate-slider" className="text-[8px] font-black opacity-30 uppercase tracking-widest">Step Learning Rate (η)</label>
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
                              onClick={() => plasticityMutation.mutate({ action: 'plasticity', learning_rate: lr, trigger_spikes: selectedSpikes })} 
                              disabled={plasticityMutation.isPending}
                              className="bg-red-600 hover:bg-red-500 text-white font-black italic uppercase tracking-wider text-xs px-6 py-4 rounded-xl shadow-lg transition-all active:scale-95"
                          >
                              {plasticityMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Simuler"}
                          </Button>
                      </div>
                  </Card>
              </div>

              {/* Master State Profile & Logs */}
              <div className="lg:col-span-3 space-y-8">
                  {/* Dominant Archetype Aura Card */}
                  <Card padding="none" className="bg-black border-white/10 overflow-hidden rounded-[2.5rem] relative group shadow-2xl min-h-[220px]">
                      {/* Aura Ambient Blur */}
                      <div 
                          className="absolute inset-0 opacity-20 transition-opacity duration-700 group-hover:opacity-35"
                          style={{ 
                              background: `radial-gradient(circle at center, ${state.current_archetype.accent} 0%, transparent 70%)`,
                              filter: 'blur(30px)'
                          }} 
                      />
                      
                      <div className="relative z-10 p-8 text-center flex flex-col items-center justify-center">
                          <div className="w-24 h-24 mx-auto mb-4 relative">
                              <div 
                                  className="absolute inset-0 rounded-full animate-pulse opacity-40"
                                  style={{ boxShadow: `0 0 35px ${state.current_archetype.accent}` }}
                              />
                              <div className="w-full h-full bg-navy-950 border-2 border-white/15 rounded-full flex items-center justify-center relative overflow-hidden">
                                  <Brain className="w-10 h-10 text-white opacity-25" />
                                  <div 
                                      className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-red-600/10 to-transparent h-1/2 animate-scan"
                                  />
                              </div>
                          </div>

                          <Badge 
                              variant="primary" 
                              style={{ backgroundColor: state.current_archetype.accent }}
                              className="mb-3 text-[8px] font-black italic uppercase tracking-widest py-1 px-4 border-none text-white"
                          >
                              {state.current_archetype.id.replace('_', ' ')}
                          </Badge>
                          
                          <h2 className="text-xl font-black italic manga-font uppercase mb-1 tracking-tight">Active Persona</h2>
                          <p className="text-[8px] font-bold opacity-30 uppercase tracking-widest">
                              Aura: {state.current_archetype.aura_type} ({Math.round(state.current_archetype.intensity * 100)}%)
                          </p>
                      </div>
                  </Card>

                  {/* STDP Logs */}
                  <Card padding="lg" className="bg-black border-white/5 flex flex-col min-h-[220px]">
                      <span className="text-[9px] font-black uppercase opacity-35 block mb-4 tracking-widest flex items-center gap-2">
                          <Flame className="w-4 h-4 text-orange-500" /> STDP Log Activity
                      </span>
                      <div className="space-y-3 overflow-y-auto max-h-[190px] pr-2 custom-scrollbar">
                          {currentLogs.map((log: string, idx: number) => (
                              <div key={idx} className="font-mono text-[8px] text-yellow-400 flex items-start gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
                                  <Flame className="w-3 h-3 text-red-500 shrink-0" /> 
                                  <span className="leading-tight">{log}</span>
                              </div>
                          ))}
                          {currentLogs.length === 0 && (
                              <div className="flex-1 flex flex-col items-center justify-center py-10 opacity-20 text-center">
                                  <span className="text-[9px] font-black uppercase tracking-widest block italic">No synaptic evolution recorded</span>
                              </div>
                          )}
                      </div>
                  </Card>
              </div>

          </div>

          {/* Guide & Protocole */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Brain className="w-64 h-64 text-red-500" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-red-400" /> Guide de la Plasticité
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">La Matrice :</span> Chaque case de la grille montre la force du lien entre deux concepts (Shonen, Mecha, Romance...). Plus la case est lumineuse, plus l'association est forte.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">Les Spikes :</span> Sélectionnez des concepts puis cliquez sur "Simuler" : les liens entre les concepts activés ensemble se renforcent, comme des neurones qui apprennent par association.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">Le Persona :</span> Les réglages de drift d'archétype (auto ou manuel, intensité, aura/accent/police) ajustent le thème visuel que l'application applique à votre profil.
                      </p>
                  </div>
              </Card>

              <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-red-200/60">
                      Simulation de plasticité synaptique : règle de Hebb et STDP (Spike-Timing-Dependent Plasticity), avec constantes de temps τ+ / τ- à décroissance exponentielle et taux d'apprentissage η appliqués à la matrice de poids. <br />
                      Les paramètres et le drift d'archétype sont persistés côté serveur via l'endpoint singularity-lab ; la matrice affichée est l'état réel renvoyé par l'API.
                  </p>
              </div>
          </div>

        </div>
      </AnimatedPage>
    </div>
  );
};

export default SynapticLabPage;
