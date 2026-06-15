import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Activity,
  Flame,
  Loader2,
  ChevronRight,
  ShieldCheck,
  Zap,
  Target,
  Layers,
  Brain,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const CONCEPTS = [
  'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
  'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
];

const SynapticLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [activations] = useState<number[]>(Array(10).fill(0).map(() => Math.random()));
  const [selectedSpikes, setSelectedSpikes] = useState<number[]>([]);
  const [lr, setLr] = useState(0.05);
  const [plasticityResult, setPlasticityResult] = useState<any | null>(null);

  const plasticityMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
    }),
    onSuccess: (data) => setPlasticityResult(data)
  });

  const toggleSpike = (idx: number) => {
    if (selectedSpikes.includes(idx)) {
      setSelectedSpikes(selectedSpikes.filter(i => i !== idx));
    } else {
      setSelectedSpikes([...selectedSpikes, idx]);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-400 mb-4">
                  <Activity className="w-3 h-3 animate-pulse" /> Spike-Timing-Dependent Plasticity
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  {t('labs.plasticity.title').split(' ')[0]} <span className="text-red-500 text-glow">{t('labs.plasticity.title').split(' ')[1]}</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  {t('labs.plasticity.subtitle')}
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Configuration */}
              <div className="lg:col-span-4 space-y-8">
                  <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                          <Brain className="w-24 h-24 rotate-12" />
                      </div>
                      
                      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                          <Target className="w-4 h-4 text-red-500" /> Hebbian Parameters
                      </h3>

                      <div className="space-y-8">
                          <div className="space-y-6">
                              <div className="space-y-3">
                                  <div className="flex justify-between items-center px-2">
                                      <label className="text-[10px] font-black opacity-30 uppercase tracking-widest">Learning Rate (η)</label>
                                      <span className="text-xs font-mono text-red-500">{lr.toFixed(3)}</span>
                                  </div>
                                  <input 
                                      type="range" 
                                      min="0.01" 
                                      max="0.2" 
                                      step="0.01" 
                                      value={lr} 
                                      onChange={(e) => setLr(parseFloat(e.target.value))} 
                                      className="w-full accent-red-600 h-1.5 bg-white/5 rounded-full appearance-none cursor-pointer" 
                                  />
                              </div>
                          </div>

                          <div className="p-6 bg-black border border-white/5 rounded-2xl space-y-4">
                              <h4 className="text-[9px] font-black uppercase opacity-30 tracking-widest">Selected Concepts</h4>
                              <div className="flex flex-wrap gap-2">
                                  {selectedSpikes.length > 0 ? selectedSpikes.map(idx => (
                                      <Badge key={idx} variant="primary" className="bg-red-600/20 text-red-400 border-none text-[8px]">{CONCEPTS[idx]}</Badge>
                                  )) : <span className="text-[8px] font-bold opacity-20 italic">No spikes triggered</span>}
                              </div>
                          </div>

                          <Button 
                              onClick={() => plasticityMutation.mutate({ action: 'plasticity', learning_rate: lr, trigger_spikes: selectedSpikes })} 
                              disabled={plasticityMutation.isPending} 
                              className="w-full bg-red-600 hover:bg-red-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                          >
                              {plasticityMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "SIMULER HEBB"}
                          </Button>
                      </div>
                  </Card>

                  <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                      <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-red-400">Règle de Hebb</h4>
                      <p className="text-[10px] font-bold uppercase leading-relaxed mb-4 italic">
                          "Cells that fire together, wire together."
                      </p>
                      <p className="text-[9px] font-bold uppercase opacity-30 leading-relaxed">
                          Le simulateur modifie la matrice de poids synaptiques en fonction du timing des "spikes" (activations) de chaque concept.
                      </p>
                  </Card>
              </div>

              {/* Neural Map & Results */}
              <div className="lg:col-span-8 space-y-8">
                  {/* Concept Spikes Selector */}
                  <Card padding="lg" className="bg-navy-900 border-white/5 shadow-2xl">
                      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                          <Zap className="w-4 h-4 text-yellow-500" /> Trigger Neural Spikes
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                          {CONCEPTS.map((concept, idx) => (
                              <button 
                                  key={concept} 
                                  onClick={() => toggleSpike(idx)} 
                                  className={`p-6 rounded-[1.5rem] border-2 text-left flex flex-col justify-between h-32 transition-all hover:scale-105 group relative overflow-hidden ${
                                      selectedSpikes.includes(idx) 
                                      ? 'bg-red-600 border-red-400 text-white shadow-[0_0_30px_rgba(220,38,38,0.3)]' 
                                      : 'bg-black border-white/5 text-gray-500 hover:border-white/10'
                                  }`}
                              >
                                  {selectedSpikes.includes(idx) && (
                                      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
                                  )}
                                  <span className="text-[10px] font-black uppercase tracking-wider block relative z-10">{concept}</span>
                                  <span className="text-xs font-black font-mono relative z-10">
                                      {selectedSpikes.includes(idx) ? 'FIRE!' : activations[idx].toFixed(2)}
                                  </span>
                              </button>
                          ))}
                      </div>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Matrix View */}
                      <Card padding="lg" className="bg-navy-950 border-white/10 flex flex-col min-h-[400px]">
                          <span className="text-[10px] font-black uppercase opacity-30 block mb-10 tracking-widest flex items-center gap-2">
                              <Layers className="w-4 h-4" /> Synaptic Weight Matrix (W)
                          </span>
                          {plasticityResult ? (
                              <div className="grid grid-cols-10 gap-2 flex-1 items-center justify-center max-w-[420px] mx-auto animate-fade-in">
                                  {plasticityResult.weights?.map((row: number[], rIdx: number) => row.map((val: number, cIdx: number) => (
                                      <div 
                                          key={`${rIdx}-${cIdx}`} 
                                          style={{ backgroundColor: `rgba(${Math.floor(val * 255)}, 100, 239, ${0.1 + val * 0.9})` }} 
                                          className={`aspect-square w-9 rounded-lg border border-white/5 flex items-center justify-center text-[8px] font-black font-mono transition-all duration-500 ${val > 0.5 ? 'text-white' : 'text-white/20'}`}
                                          title={`Connection: ${CONCEPTS[rIdx]} -> ${CONCEPTS[cIdx]} : ${val.toFixed(2)}`}
                                      >
                                          {val > 0 ? val.toFixed(1) : '0'}
                                      </div>
                                  )))}
                              </div>
                          ) : (
                              <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10">
                                  <Activity className="w-20 h-20 mx-auto mb-6 text-red-500 animate-pulse" />
                                  <span className="text-sm font-black uppercase tracking-[0.2em] block">Waiting for spikes...</span>
                              </div>
                          )}
                      </Card>

                      {/* STDP Logs */}
                      <Card padding="lg" className="bg-black border-white/5 flex flex-col">
                          <span className="text-[10px] font-black uppercase opacity-30 block mb-10 tracking-widest flex items-center gap-2">
                              <Flame className="w-4 h-4 text-orange-500" /> STDP Activity Log
                          </span>
                          {plasticityResult ? (
                              <div className="space-y-6 overflow-y-auto max-h-[350px] pr-4 custom-scrollbar">
                                  <div className="text-emerald-400 font-bold text-[10px] bg-emerald-500/10 p-4 rounded-2xl border border-emerald-500/10 uppercase tracking-widest">
                                      <ShieldCheck className="w-4 h-4 inline mr-2" /> {plasticityResult.message}
                                  </div>
                                  {plasticityResult.stdp_log?.map((log: string, idx: number) => (
                                      <div key={idx} className="font-mono text-[10px] text-yellow-400 flex items-start gap-4 p-3 bg-white/5 rounded-xl border border-white/5">
                                          <Flame className="w-4 h-4 text-red-500 shrink-0" /> 
                                          <span className="leading-relaxed">{log}</span>
                                      </div>
                                  ))}
                              </div>
                          ) : (
                              <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10 text-center">
                                  <span className="text-xs font-black uppercase tracking-widest block italic">No synaptic evolution recorded</span>
                              </div>
                          )}
                      </Card>
                  </div>
              </div>
          </div>

          {/* Global Warning & Guide */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(220,38,38,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Brain className="w-64 h-64 text-red-500" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-red-400" /> {t('labs.plasticity.explainer_title')}
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          {t('labs.plasticity.explainer_text_card1')}
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          {t('labs.plasticity.explainer_text_card2')}
                      </p>
                  </div>
              </Card>

              <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed text-red-200/40">
                      {t('labs.plasticity.protocol_text')}
                  </p>
              </div>
          </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default SynapticLabPage;
