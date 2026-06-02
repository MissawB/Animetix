import React, { useState } from 'react';
import { 
  Cpu, 
  Activity, 
  Globe, 
  Play, 
  Plus, 
  RefreshCw, 
  Layers, 
  ShieldCheck, 
  Flame, 
  Swords, 
  Zap, 
  Atom,
  Users,
  Target,
  BarChart3,
  Search,
  Film
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

const CONCEPTS = [
  'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
  'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
];

const SingularityLabPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'compiler' | 'plasticity' | 'multiverse' | 'quantum' | 'swarm'>('compiler');

  // State: Compiler
  const [fnName, setFnName] = useState('semantic_cosine_opt');
  const [cCode, setCCode] = useState('// Version optimisée générée à la volée\ndouble semantic_cosine_opt(double* a, double* b, int n) {\n    double dot = 0.0;\n    // ... calcul matriciel vectorisé C ...\n    return dot;\n}');
  const [compilerResult, setCompilerResult] = useState<any | null>(null);

  // State: Plasticity
  const [activations, setActivations] = useState<number[]>(Array(10).fill(0).map(() => Math.random()));
  const [selectedSpikes, setSelectedSpikes] = useState<number[]>([]);
  const [lr, setLr] = useState(0.05);
  const [plasticityResult, setPlasticityResult] = useState<any | null>(null);

  // State: Multiverse
  const [universeName, setUniverseName] = useState('ShinSekai');
  const [genre, setGenre] = useState('Cyberpunk');
  const [synthesizedResult, setSynthesizedResult] = useState<any | null>(null);

  // State: Quantum
  const [quantumTheme, setQuantumTheme] = useState('shonen');
  const [quantumResult, setQuantumResult] = useState<any | null>(null);

  // State: Swarm
  const [swarmFact, setSwarmFact] = useState('Luffy est plus fort que Naruto.');
  const [swarmMedia, setSwarmMedia] = useState('One Piece');
  const [swarmResult, setSwarmResult] = useState<any | null>(null);

  // Mutations
  const compileMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data) => setCompilerResult(data)
  });

  const plasticityMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data) => setPlasticityResult(data)
  });

  const synthesizeMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data) => setSynthesizedResult(data)
  });

  const quantumMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data) => setQuantumResult(data)
  });

  const swarmMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data) => setSwarmResult(data)
  });

  const toggleSpike = (idx: number) => {
    if (selectedSpikes.includes(idx)) {
      setSelectedSpikes(selectedSpikes.filter(i => i !== idx));
    } else {
      setSelectedSpikes([...selectedSpikes, idx]);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-6xl font-black italic manga-font mb-6 tracking-tighter uppercase text-center md:text-left">
        SINGULARITY <span className="text-red-500 text-glow">LAB</span>
      </h1>
      <p className="text-gray-400 max-w-2xl mb-12 text-center md:text-left leading-relaxed font-bold uppercase tracking-widest text-[10px] opacity-40">
        Protocoles IA de 5ème génération • Cognition Quantique & Intelligences Collectives
      </p>

      {/* Tabs */}
      <div className="flex gap-4 mb-10 overflow-x-auto pb-4 no-scrollbar">
        {[
            { id: 'compiler', icon: Cpu, label: 'Compiler' },
            { id: 'plasticity', icon: Activity, label: 'Plasticity' },
            { id: 'multiverse', icon: Globe, label: 'Multiverse' },
            { id: 'quantum', icon: Atom, label: 'Quantum Cognition' },
            { id: 'swarm', icon: Users, label: 'Swarm Intelligence' }
        ].map(tab => (
            <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-3 px-6 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all shrink-0 ${
                    activeTab === tab.id
                    ? 'bg-red-600 text-white shadow-[0_0_30px_rgba(220,38,38,0.3)] scale-105'
                    : 'bg-white/5 text-gray-500 hover:bg-white/10'
                }`}
            >
                <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? 'animate-pulse' : ''}`} /> {tab.label}
            </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        <div className="lg:col-span-1 space-y-8">
          {activeTab === 'compiler' && (
            <Card padding="lg" className="space-y-6 bg-navy-950/50 border-white/5">
              <h3 className="text-[10px] font-black uppercase opacity-30 tracking-widest">JIT Optimization</h3>
              <div className="space-y-4">
                <input type="text" value={fnName} onChange={(e) => setFnName(e.target.value)} className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold focus:border-red-500 outline-none" />
                <Button onClick={() => compileMutation.mutate({ action: 'compile', function_name: fnName })} disabled={compileMutation.isPending} fullWidth className="bg-red-600 border-none font-black italic">OPTIMISER</Button>
              </div>
            </Card>
          )}

          {activeTab === 'plasticity' && (
            <Card padding="lg" className="space-y-6 bg-navy-950/50 border-white/5">
              <h3 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Synaptic Parameters</h3>
              <div className="space-y-4">
                <input type="range" min="0.01" max="0.2" step="0.01" value={lr} onChange={(e) => setLr(parseFloat(e.target.value))} className="w-full accent-red-600" />
                <Button onClick={() => plasticityMutation.mutate({ action: 'plasticity', learning_rate: lr, trigger_spikes: selectedSpikes })} disabled={plasticityMutation.isPending} fullWidth className="bg-red-600 border-none font-black italic">SIMULER HEBB</Button>
              </div>
            </Card>
          )}

          {activeTab === 'multiverse' && (
            <Card padding="lg" className="space-y-6 bg-navy-950/50 border-white/5">
              <h3 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Genesis Config</h3>
              <div className="space-y-4">
                <input type="text" value={universeName} onChange={(e) => setUniverseName(e.target.value)} className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold focus:border-red-500 outline-none" />
                <select value={genre} onChange={(e) => setGenre(e.target.value)} className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white outline-none">
                    <option value="Cyberpunk">Cyberpunk</option><option value="Sci-Fi">Sci-Fi</option><option value="Fantasy">Fantasy</option>
                </select>
                <Button onClick={() => synthesizeMutation.mutate({ action: 'synthesize', universe_name: universeName, genre: genre })} disabled={synthesizeMutation.isPending} fullWidth className="bg-red-600 border-none font-black italic">SYNTHÉTISER</Button>
              </div>
            </Card>
          )}

          {activeTab === 'quantum' && (
            <Card padding="lg" className="space-y-6 bg-navy-950/50 border-white/5">
              <h3 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Born's Measurement</h3>
              <div className="space-y-4">
                <label className="text-[8px] font-black opacity-30 uppercase tracking-widest px-2">Observable Thématique</label>
                <select value={quantumTheme} onChange={(e) => setQuantumTheme(e.target.value)} className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white outline-none">
                    <option value="shonen">SHONEN</option><option value="seinen">SEINEN</option><option value="ghibli">GHIBLI</option><option value="comedy">COMEDY</option>
                </select>
                <Button onClick={() => quantumMutation.mutate({ action: 'quantum', theme: quantumTheme })} disabled={quantumMutation.isPending} fullWidth className="bg-purple-600 border-none font-black italic shadow-purple-500/20">EFFECTUER MESURE</Button>
              </div>
            </Card>
          )}

          {activeTab === 'swarm' && (
            <Card padding="lg" className="space-y-6 bg-navy-950/50 border-white/5">
              <h3 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Consensus Proposal</h3>
              <div className="space-y-4">
                <input type="text" value={swarmMedia} onChange={(e) => setSwarmMedia(e.target.value)} placeholder="Média..." className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold focus:border-emerald-500 outline-none" />
                <textarea value={swarmFact} onChange={(e) => setSwarmFact(e.target.value)} rows={3} placeholder="Fait à valider..." className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-xs font-bold outline-none resize-none" />
                <Button onClick={() => swarmMutation.mutate({ action: 'swarm', fact: swarmFact, media: swarmMedia })} disabled={swarmMutation.isPending} fullWidth className="bg-emerald-600 border-none font-black italic shadow-emerald-500/20">LANCER VOTE ESSAIM</Button>
              </div>
            </Card>
          )}
        </div>

        <div className="lg:col-span-3">
          <div className="bg-black/40 backdrop-blur-xl rounded-[4rem] shadow-2xl overflow-hidden min-h-[650px] relative border border-white/5 flex flex-col p-12">
            
            <AnimatePresence mode="wait">
                {/* TAB: QUANTUM */}
                {activeTab === 'quantum' && (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-12">
                        <div className="flex items-center justify-between border-b border-white/5 pb-6">
                            <Badge className="bg-purple-500/10 text-purple-500 border-purple-500/20 px-4 py-2 text-[10px] font-black italic uppercase tracking-widest">Quantum Preference Engine</Badge>
                            <Atom className="w-6 h-6 text-purple-500 animate-spin-slow" />
                        </div>

                        {quantumResult ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                <div className="space-y-8">
                                    <div className="p-8 bg-purple-500/5 rounded-[2.5rem] border border-purple-500/20 text-center relative overflow-hidden">
                                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-50" />
                                        <h4 className="text-[10px] font-black uppercase opacity-40 mb-6 tracking-[0.2em]">Mesure de Probabilité</h4>
                                        <div className="text-8xl font-black italic text-purple-400 manga-font mb-4">
                                            {Math.round(quantumResult.probability * 100)}%
                                        </div>
                                        <Badge className={`px-6 py-2 rounded-full font-black italic uppercase ${quantumResult.outcome ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'}`}>
                                            OUTCOME: {quantumResult.outcome ? 'COLLAPSED POSITIVE' : 'COLLAPSED NEGATIVE'}
                                        </Badge>
                                    </div>

                                    <Card padding="lg" className="bg-white/5 border-white/5">
                                        <h5 className="text-[10px] font-black uppercase opacity-30 mb-4 tracking-widest">Interprétation de Born</h5>
                                        <p className="text-xs font-bold leading-relaxed opacity-60 italic">
                                            L'IA modélise vos préférences comme une superposition d'états. La mesure force un choix binaire, mais conserve l'intrication sémantique avec les thèmes connexes.
                                        </p>
                                    </Card>
                                </div>

                                <div className="space-y-6">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest flex items-center gap-2 opacity-40">
                                        <Zap className="w-4 h-4 text-yellow-500" /> État du Vecteur de Conscience
                                    </h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        {quantumResult.state_vector.map((val: string, i: number) => (
                                            <div key={i} className="p-4 bg-black border border-white/5 rounded-2xl flex flex-col justify-center">
                                                <span className="text-[8px] font-black text-gray-500 mb-1">AMPLITUDE_{i}</span>
                                                <code className="text-[10px] font-mono text-purple-300 truncate">{val}</code>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="p-6 bg-navy-900/50 rounded-2xl border border-white/5 text-[10px] font-bold text-blue-400 italic">
                                        "L'incertitude est le socle de la créativité numérique."
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10">
                                <Atom className="w-32 h-32 mb-8 animate-spin-slow" />
                                <h3 className="text-3xl font-black italic uppercase manga-font">Système en Superposition</h3>
                                <p className="text-xs font-bold uppercase tracking-widest mt-2">Prêt pour une mesure d'observable thématique.</p>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* TAB: SWARM */}
                {activeTab === 'swarm' && (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-12">
                         <div className="flex items-center justify-between border-b border-white/5 pb-6">
                            <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 px-4 py-2 text-[10px] font-black italic uppercase tracking-widest">Swarm Intelligence Protocol</Badge>
                            <Users className="w-6 h-6 text-emerald-500" />
                        </div>

                        {swarmResult ? (
                            <div className="space-y-12">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                    <Card padding="lg" className="bg-emerald-500/5 border-emerald-500/20 text-center">
                                        <span className="text-[10px] font-black uppercase opacity-40 block mb-2">Consensus Score</span>
                                        <div className="text-5xl font-black italic text-emerald-500 manga-font">{(swarmResult.consensus_score * 100).toFixed(1)}%</div>
                                    </Card>
                                    <Card padding="lg" className="bg-white/5 border-white/5 text-center flex flex-col justify-center">
                                        <span className="text-[10px] font-black uppercase opacity-40 block mb-2">Decision</span>
                                        <div className={`text-xl font-black italic uppercase ${swarmResult.is_recorded ? 'text-blue-400' : 'text-red-400'}`}>
                                            {swarmResult.is_recorded ? 'FACT ACCEPTED' : 'FACT REJECTED'}
                                        </div>
                                    </Card>
                                    <Card padding="lg" className="bg-white/5 border-white/5 text-center flex flex-col justify-center">
                                        <span className="text-[10px] font-black uppercase opacity-40 block mb-2">Agent Pool</span>
                                        <div className="text-xl font-black italic uppercase text-white">7 MULTI-AGENTS</div>
                                    </Card>
                                </div>

                                <div className="space-y-6">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest opacity-40 flex items-center gap-2">
                                        <BarChart3 className="w-4 h-4" /> Répartition des Votes par Agent
                                    </h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                        {Object.entries(swarmResult.votes).map(([agent, score]: any) => (
                                            <div key={agent} className="p-4 bg-navy-950 rounded-2xl border border-white/5 space-y-2">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-[9px] font-black uppercase text-gray-500">{agent}</span>
                                                    <span className={`text-[10px] font-bold ${score >= 0.7 ? 'text-emerald-500' : 'text-red-500'}`}>{Math.round(score * 100)}%</span>
                                                </div>
                                                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                                    <div className={`h-full ${score >= 0.7 ? 'bg-emerald-500' : 'bg-red-500'}`} style={{ width: `${score * 100}%` }} />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <Card padding="lg" className="bg-blue-600/10 border-blue-500/20">
                                    <p className="text-xs font-bold italic leading-relaxed opacity-80 text-blue-100">
                                        "L'intelligence collective de l'essaim permet de filtrer les hallucinations et les biais individuels des agents en exigeant un consensus sémantique avant toute mise à jour du Knowledge Graph."
                                    </p>
                                </Card>
                            </div>
                        ) : (
                             <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10">
                                <Users className="w-32 h-32 mb-8" />
                                <h3 className="text-3xl font-black italic uppercase manga-font">Essaim en Veille</h3>
                                <p className="text-xs font-bold uppercase tracking-widest mt-2">En attente d'une proposition de fait pour arbitrage collectif.</p>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* TAB: COMPILER (Existing) */}
                {activeTab === 'compiler' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 flex-1 flex flex-col">
                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                            <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20 px-4 py-2 text-[10px] font-black italic uppercase tracking-widest">JIT COMPILER SOTA 2035</Badge>
                            <span className="text-[10px] font-black uppercase opacity-30">Auto-microcode loading</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 flex-1">
                            <div className="flex flex-col space-y-4">
                                <span className="text-[10px] font-black uppercase opacity-30 tracking-widest">Microcode source (C)</span>
                                <textarea value={cCode} onChange={(e) => setCCode(e.target.value)} className="w-full flex-1 min-h-[350px] bg-navy-950/80 border border-white/10 rounded-[2rem] p-8 font-mono text-xs text-green-400 focus:outline-none focus:border-red-500" />
                            </div>
                            <div className="bg-white/5 rounded-[2rem] border border-white/5 p-8 flex flex-col justify-between">
                                <div>
                                    <span className="text-[10px] font-black uppercase opacity-30 block mb-6 tracking-widest">Statut Compilation</span>
                                    {compilerResult ? (
                                        <div className="space-y-6 animate-fade-in">
                                            <div className="flex items-center gap-3 text-green-400 font-bold text-sm"><ShieldCheck className="w-5 h-5" /> {compilerResult.message}</div>
                                            <p className="text-xs font-bold text-gray-300 leading-relaxed font-mono bg-black/50 p-6 rounded-2xl border border-white/5">{compilerResult.test_output}</p>
                                            <div className="bg-navy-950 p-6 rounded-2xl border border-white/5">
                                                <span className="text-[8px] font-black uppercase text-gray-500 block mb-2">Signature chargée</span>
                                                <code className="text-[10px] font-mono text-yellow-400 block">{compilerResult.c_code_generated}</code>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-20 opacity-20"><Cpu className="w-24 h-24 mx-auto mb-4" /><span className="text-xs font-black uppercase tracking-widest block">Aucune compilation exécutée</span></div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* TAB: PLASTICITY (Existing) */}
                {activeTab === 'plasticity' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 flex-1 flex flex-col">
                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                            <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20 px-4 py-2 text-[10px] font-black italic uppercase tracking-widest">PLASTICITÉ SYNAPTIQUE SIMULATOR</Badge>
                            <span className="text-[10px] font-black uppercase opacity-30">Spike-Timing-Dependent Plasticity</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            {CONCEPTS.map((concept, idx) => (
                                <button key={concept} onClick={() => toggleSpike(idx)} className={`p-6 rounded-2xl border text-left flex flex-col justify-between h-28 transition-all hover:scale-105 ${selectedSpikes.includes(idx) ? 'bg-red-600 border-red-400 text-white shadow-[0_0_20px_rgba(220,38,38,0.3)]' : 'bg-white/5 border-white/5 text-gray-500'}`}>
                                    <span className="text-[9px] font-black uppercase tracking-wider block">{concept}</span>
                                    <span className="text-xs font-black font-mono">{selectedSpikes.includes(idx) ? 'SPIKE' : activations[idx].toFixed(2)}</span>
                                </button>
                            ))}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 flex-1">
                            <div className="bg-navy-950/80 border border-white/10 rounded-[2.5rem] p-10 flex flex-col">
                                <span className="text-[10px] font-black uppercase opacity-30 block mb-8 tracking-widest">Matrice de Poids Synaptiques (W)</span>
                                {plasticityResult ? (
                                    <div className="grid grid-cols-10 gap-2 flex-1 items-center justify-center max-w-[400px] mx-auto">
                                        {plasticityResult.weights.map((row: number[], rIdx: number) => row.map((val: number, cIdx: number) => (
                                            <div key={`${rIdx}-${cIdx}`} style={{ backgroundColor: `rgba(${Math.floor(val * 255)}, 100, 239, ${0.1 + val * 0.9})` }} className="aspect-square w-8 rounded-lg border border-white/5 flex items-center justify-center text-[8px] font-black font-mono text-white/40">{val > 0 ? val.toFixed(1) : '0'}</div>
                                        )))}
                                    </div>
                                ) : (
                                    <div className="text-center py-20 opacity-20 flex-1 flex flex-col justify-center"><Activity className="w-20 h-20 mx-auto mb-4 text-red-500 animate-pulse" /><span className="text-xs font-black uppercase tracking-widest block">Simulez pour charger la matrice</span></div>
                                )}
                            </div>
                            <div className="bg-white/5 rounded-[2.5rem] border border-white/5 p-10 flex flex-col">
                                <span className="text-[10px] font-black uppercase opacity-30 block mb-8 tracking-widest">Rapport STDP / Hebb</span>
                                {plasticityResult ? (
                                    <div className="space-y-6 overflow-y-auto max-h-[300px]">
                                        <div className="text-green-400 font-bold text-sm bg-green-500/10 p-4 rounded-2xl border border-green-500/10">{plasticityResult.message}</div>
                                        {plasticityResult.stdp_log.map((log: string, idx: number) => (<div key={idx} className="font-mono text-[10px] text-yellow-400 flex items-center gap-3"><Flame className="w-4 h-4 text-red-500" /> {log}</div>))}
                                    </div>
                                ) : (
                                    <div className="text-center py-20 opacity-20 flex-1 flex flex-col justify-center"><span className="text-xs font-black uppercase tracking-widest block">Aucun historique de spikes</span></div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* TAB: MULTIVERSE (Existing) */}
                {activeTab === 'multiverse' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 flex-1 flex flex-col">
                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                            <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20 px-4 py-2 text-[10px] font-black italic uppercase tracking-widest">ADMS NARRATIVE GENERATOR</Badge>
                            <span className="text-[10px] font-black uppercase opacity-30">Autonomous Domain Synthesizer</span>
                        </div>
                        {synthesizedResult ? (
                            <div className="space-y-8 flex-1 overflow-y-auto pr-4 max-h-[500px] no-scrollbar">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {[
                                        { label: 'Cohérence (IA)', val: synthesizedResult.evaluation.ai_score, threshold: 0.7 },
                                        { label: 'Popularité Communautaire', val: synthesizedResult.evaluation.community_score, threshold: 0.7 }
                                    ].map(s => (
                                        <Card key={s.label} padding="lg" className="bg-white/5 border-white/5 flex flex-col justify-between h-32">
                                            <span className="text-[8px] font-black uppercase opacity-40">{s.label}</span>
                                            <div className="flex items-end justify-between">
                                                <span className={`text-5xl font-black italic manga-font ${s.val >= s.threshold ? 'text-green-400' : 'text-red-400'}`}>{Math.round(s.val * 100)}%</span>
                                                <span className="text-[8px] font-bold opacity-20 uppercase">Threshold: {s.threshold * 100}%</span>
                                            </div>
                                        </Card>
                                    ))}
                                    <Card padding="lg" className="bg-white/5 border-white/5 flex flex-col justify-between h-32">
                                        <span className="text-[8px] font-black uppercase opacity-40">Statut Neo4j</span>
                                        <div className={`text-xl font-black italic uppercase ${synthesizedResult.persisted ? 'text-blue-400' : 'text-red-400'}`}>
                                            {synthesizedResult.persisted ? 'PERSISTÉ !' : 'REJETÉ'}
                                        </div>
                                    </Card>
                                </div>
                                <div className="bg-navy-950 p-12 rounded-[3.5rem] border border-white/5 space-y-10 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/5 blur-[100px] -mr-32 -mt-32" />
                                    <div className="flex justify-between items-center border-b border-white/5 pb-6">
                                        <h2 className="text-4xl font-black italic text-red-500 manga-font uppercase tracking-tighter">{synthesizedResult.universe.name}</h2>
                                        <Badge className="bg-red-500/10 text-red-500 border-red-500/20 uppercase tracking-widest text-[9px] font-black italic px-4 py-2">{synthesizedResult.universe.genre}</Badge>
                                    </div>
                                    <p className="text-xl font-bold text-gray-200 leading-relaxed italic">"{synthesizedResult.universe.description}"</p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-8">
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest flex items-center gap-2"><Users className="w-4 h-4" /> Personnages</h4>
                                            <div className="space-y-4">
                                                {synthesizedResult.universe.characters.map((char: any) => (
                                                    <div key={char.name} className="bg-white/5 border border-white/5 p-6 rounded-2xl flex justify-between items-center hover:bg-white/10 transition-colors">
                                                        <div><span className="font-black text-sm text-white block uppercase italic">{char.name}</span><span className="text-[10px] text-gray-500 block uppercase font-bold">{char.role}</span></div>
                                                        <Badge className="bg-red-600/20 text-red-400 border-none font-mono text-[10px]">PL: {char.power_level}</Badge>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest flex items-center gap-2"><Film className="w-4 h-4" /> Chronologie</h4>
                                            <div className="space-y-4">
                                                {synthesizedResult.universe.episodes.map((ep: any) => (
                                                    <div key={ep.number} className="bg-white/5 border border-white/5 p-6 rounded-2xl space-y-2 hover:bg-white/10 transition-colors">
                                                        <span className="font-black text-[10px] text-red-400 block uppercase tracking-widest">Épisode {ep.number} : {ep.title}</span>
                                                        <p className="text-xs font-bold text-gray-400 leading-relaxed italic">{ep.summary}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10"><Globe className="w-32 h-32 mb-8" /><h3 className="text-3xl font-black italic uppercase manga-font">Nexus de Création</h3><p className="text-xs font-bold uppercase tracking-widest mt-2">Prêt pour la synthèse d'un nouveau segment de multivers.</p></div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Global Loading Overlay (re-check) */}
            {(compileMutation.isPending || plasticityMutation.isPending || synthesizeMutation.isPending || quantumMutation.isPending || swarmMutation.isPending) && (
              <div className="absolute inset-0 bg-black/90 backdrop-blur-sm z-50 flex flex-col items-center justify-center rounded-[4rem]">
                <div className="relative w-32 h-32 mb-12">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 4, repeat: Infinity, ease: "linear" }} className="absolute inset-0 border-t-4 border-red-600 rounded-full" />
                    <motion.div animate={{ rotate: -360 }} transition={{ duration: 3, repeat: Infinity, ease: "linear" }} className="absolute inset-4 border-t-4 border-blue-600 rounded-full" />
                    <Cpu className="w-12 h-12 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
                </div>
                <span className="text-white font-black italic uppercase tracking-[0.4em] animate-pulse manga-font text-2xl">Singularity <span className="text-red-600">Active</span></span>
                <p className="text-[10px] font-black uppercase text-gray-500 mt-4 tracking-[0.2em]">Inférence haute intensité sur cluster H100</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SingularityLabPage;
