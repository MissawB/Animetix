import React from 'react';
import { 
  Brain, 
  ShieldCheck, 
  Trash2, 
  Activity, 
  Zap, 
  RefreshCw, 
  Layers, 
  Lock,
  Fingerprint,
  Target,
  Scale,
  Loader2,
  Sparkles
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion } from 'framer-motion';

import { NeuroMemoryData, DeducedRule, NeuralSignal } from '../../types';

const NeuroMemoryPage: React.FC = () => {
  const { data, isLoading, refetch } = useQuery<NeuroMemoryData>({
    queryKey: ['neuro-memory'],
    queryFn: () => apiClient('/api/v1/cognition/neuro-memory/'),
  });

  const resetMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/cognition/neuro-memory/', {
        method: 'POST',
        body: JSON.stringify({ action: 'reset' })
    }),
    onSuccess: () => refetch()
  });

  const signalMutation = useMutation({
    mutationFn: (body: { action: string; feedback_id: number; weight?: number }) => apiClient('/api/v1/cognition/neuro-memory/', {
        method: 'POST',
        body: JSON.stringify(body)
    }),
    onSuccess: () => refetch()
  });

  if (isLoading) return (
    <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_20px_rgba(99,102,241,0.5)]"></div>
        <p className="text-sm font-black uppercase tracking-[0.3em] animate-pulse opacity-40">Accessing Neural Engrams...</p>
    </div>
  );

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-4">
                  <Fingerprint className="w-3 h-3" /> Cognitive Privacy Protocol
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  NEURO <span className="text-indigo-500 text-glow">MEMORY</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Gérez les règles logiques déduites par l'IA et contrôlez votre empreinte cognitive.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Logic Profile Summary */}
              <div className="lg:col-span-4 space-y-8">
                  <Card padding="lg" className="bg-indigo-600 text-white border-none shadow-2xl relative overflow-hidden">
                      <div className="absolute -right-8 -top-8 opacity-20 rotate-12">
                          <Brain className="w-48 h-48" />
                      </div>
                      <h3 className="text-2xl font-black italic manga-font uppercase mb-6 flex items-center gap-3">
                          <ShieldCheck className="w-8 h-8" /> Trust Center
                      </h3>
                      <p className="text-sm font-bold opacity-90 leading-relaxed uppercase mb-8 relative z-10">
                          Vous avez un contrôle total sur ce que le solveur Z3 déduit de vos interactions. Vous pouvez réinitialiser votre profil logique à tout moment.
                      </p>
                      <div className="bg-black/20 rounded-2xl p-6 mb-8 relative z-10">
                          <div className="flex justify-between items-center mb-2">
                              <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Neural Signals</span>
                              <span className="text-xl font-black italic manga-font">{data?.total_signals || 0}</span>
                          </div>
                          <div className="w-full h-1.5 bg-black/20 rounded-full overflow-hidden">
                              <motion.div 
                                  initial={{ width: 0 }}
                                  animate={{ width: '75%' }}
                                  className="h-full bg-white" 
                              />
                          </div>
                      </div>
                      <Button 
                          onClick={() => resetMutation.mutate()}
                          disabled={resetMutation.isPending}
                          fullWidth
                          className="bg-black text-white hover:bg-navy-950 py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                      >
                          {resetMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "RESET LOGIC PROFILE"}
                      </Button>
                  </Card>

                  <Card padding="lg" className="bg-navy-950 border-white/5 opacity-50">
                      <h4 className="text-[10px] font-black uppercase tracking-widest mb-4">Système de Déduction</h4>
                      <ul className="space-y-4">
                          <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                              <Target className="w-4 h-4 text-indigo-500 shrink-0" /> Formal Solver: Z3 Theorem Prover.
                          </li>
                          <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                              <Scale className="w-4 h-4 text-indigo-500 shrink-0" /> Contraintes: Logique SAT binaire.
                          </li>
                          <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                              <Lock className="w-4 h-4 text-indigo-500 shrink-0" /> Confidentialité: Local-first Inference.
                          </li>
                      </ul>
                  </Card>
              </div>

              {/* Deduced Rules List */}
              <div className="lg:col-span-8">
                  <Card padding="none" className="bg-navy-900/40 border-white/10 rounded-[3rem] overflow-hidden shadow-2xl">
                      <header className="px-12 py-8 border-b border-white/5 flex justify-between items-center">
                          <h3 className="text-2xl font-black italic manga-font uppercase flex items-center gap-3">
                              <Layers className="w-6 h-6 text-indigo-500" /> Neural Engrams
                          </h3>
                          <Badge variant="neutral" className="bg-indigo-500/10 text-indigo-500 border-none uppercase font-black italic">ACTIVE RULES</Badge>
                      </header>
                      
                      <div className="p-8">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {data?.deduced_rules && data.deduced_rules.length > 0 ? (
                                  data.deduced_rules.map((item: DeducedRule) => (
                                      <div key={item.id} className="group p-6 bg-black/40 rounded-[2rem] border border-white/5 hover:border-indigo-500/30 transition-all flex flex-col justify-between">
                                          <div>
                                              <div className="flex justify-between items-start mb-4">
                                                  <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-500">
                                                      <Zap className="w-5 h-5 fill-current" />
                                                  </div>
                                                  <Badge variant="neutral" className="bg-white/5 border-none text-[8px] uppercase">{item.source}</Badge>
                                              </div>
                                              <h4 className="text-lg font-black italic manga-font uppercase text-white mb-2 tracking-tighter">
                                                  {item.rule.replace(' == ', ': ')}
                                              </h4>
                                              <p className="text-[9px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
                                                  Déduit via analyse sémantique des feedbacks récents.
                                              </p>
                                          </div>
                                          <div className="mt-8 pt-6 border-t border-white/5 flex justify-between items-center">
                                              <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Confidence: {item.confidence * 100}%</span>
                                              <button className="text-red-500/40 hover:text-red-500 transition-colors">
                                                  <Trash2 className="w-4 h-4" />
                                              </button>
                                          </div>
                                      </div>
                                  ))
                              ) : (
                                  <div className="col-span-full py-24 text-center">
                                      <Activity className="w-20 h-20 text-indigo-500 mx-auto mb-6 opacity-10 animate-pulse" />
                                      <h4 className="text-2xl font-black italic manga-font uppercase opacity-20">Insufficient data for deduction</h4>
                                  </div>
                              )}
                          </div>
                      </div>
                  </Card>
                  </div>
                  </div>

                  {/* Granular Signal Management */}
                  <div className="mt-16">
                      <Card padding="none" className="bg-navy-950/40 border-white/5 rounded-[3rem] overflow-hidden">
                          <header className="px-12 py-8 border-b border-white/5 flex justify-between items-center">
                              <div>
                                  <h3 className="text-2xl font-black italic manga-font uppercase flex items-center gap-3 text-emerald-500">
                                      <Activity className="w-6 h-6" /> Raw Signal Management
                                  </h3>
                                  <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest mt-1">Ajustez le poids de chaque interaction ou révoquez les signaux obsolètes.</p>
                              </div>
                              <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-500 border-none uppercase font-black italic">GRANULAR CONTROL</Badge>
                          </header>

                          <div className="p-8">
                              <div className="grid grid-cols-1 gap-4">
                                  {data?.signals && data.signals.length > 0 ? (
                                      data.signals.map((signal: NeuralSignal) => (
                                          <div key={signal.id} className={`p-6 rounded-2xl border transition-all flex flex-col md:flex-row items-center gap-8 ${signal.is_ignored ? 'bg-black/20 border-white/5 opacity-40' : 'bg-white/5 border-white/10 hover:border-emerald-500/20'}`}>
                                              <div className="flex items-center gap-4 shrink-0">
                                                  <div className={`p-3 rounded-xl ${signal.is_positive ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                                                      {signal.is_positive ? <Zap className="w-4 h-4 fill-current" /> : <ShieldCheck className="w-4 h-4" />}
                                                  </div>
                                                  <div className="text-right">
                                                      <p className="text-[8px] font-black uppercase opacity-30">Weight</p>
                                                      <p className="text-sm font-black italic manga-font">x{signal.weight.toFixed(1)}</p>
                                                  </div>
                                              </div>

                                              <div className="flex-grow">
                                                  <p className="text-xs font-bold text-white/70 italic line-clamp-1">"{signal.input_context}"</p>
                                                  <p className="text-[8px] font-black uppercase opacity-20 mt-1">{new Date(signal.created_at).toLocaleDateString()} • {signal.feedback_type}</p>
                                              </div>

                                              <div className="flex items-center gap-6 shrink-0">
                                                  <div className="flex flex-col gap-1 w-32">
                                                      <input 
                                                          type="range" 
                                                          min="0.1" 
                                                          max="2.0" 
                                                          step="0.1" 
                                                          defaultValue={signal.weight}
                                                          onChange={(e) => signalMutation.mutate({ action: 'update_weight', feedback_id: signal.id, weight: parseFloat(e.target.value) })}
                                                          className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                                      />
                                                      <div className="flex justify-between text-[7px] font-black opacity-30 uppercase">
                                                          <span>Soft</span>
                                                          <span>Dominant</span>
                                                      </div>
                                                  </div>

                                                  <Button 
                                                      variant="ghost" 
                                                      size="sm"
                                                      onClick={() => signalMutation.mutate({ action: signal.is_ignored ? 'restore' : 'revoke', feedback_id: signal.id })}
                                                      className={`text-[9px] font-black uppercase tracking-widest ${signal.is_ignored ? 'text-emerald-500 hover:text-emerald-400' : 'text-red-500 hover:text-red-400'}`}
                                                  >
                                                      {signal.is_ignored ? <><RefreshCw className="w-3 h-3 mr-2" /> Restore</> : <><Trash2 className="w-3 h-3 mr-2" /> Revoke</>}
                                                  </Button>
                                              </div>
                                          </div>
                                      ))
                                  ) : (
                                      <div className="py-20 text-center opacity-20">
                                          <Fingerprint className="w-12 h-12 mx-auto mb-4" />
                                          <p className="text-[10px] font-black uppercase tracking-widest">No cognitive signals archived</p>
                                      </div>
                                  )}
                              </div>
                          </div>
                      </Card>
                  </div>

                  {/* Global Warning & Guide */}
                  <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
                  <Card padding="lg" className="bg-black/40 border-indigo-500/20 shadow-[0_0_50px_rgba(99,102,241,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Brain className="w-64 h-64" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-indigo-400" /> Guide de l'Intelligence
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-indigo-400">Qu'est-ce que c'est ?</span> Cette page est votre "Panneau de Contrôle Cognitif". À chaque fois que vous interagissez avec Animetix, notre IA essaie de comprendre vos goûts, vos valeurs et vos habitudes.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-indigo-400">Les Engrammes :</span> Ce sont les "règles" que l'IA a déduites sur vous (ex: "Vous préférez les héros solitaires"). Vous pouvez voir ces règles à droite et décider de les garder ou de les supprimer.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-indigo-400">Pourquoi réinitialiser ?</span> Si vous sentez que l'IA se trompe sur vous ou que vous voulez repartir de zéro pour changer d'archétype, utilisez le bouton "RESET" en haut à gauche.
                      </p>
                  </div>
                  </Card>

                  <div className="p-12 rounded-[4rem] bg-gradient-to-br from-indigo-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed">
                      Avertissement : Les déductions neuro-symboliques sont basées sur des modèles stochastiques résolus en temps réel. <br />
                      Le profil logique est synchronisé avec votre Archétype Nexus.
                  </p>
                  </div>
                  </div>
                  </div>
                  </AnimatedPage>
    </div>
  );
};

export default NeuroMemoryPage;
