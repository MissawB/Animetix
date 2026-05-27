import React, { useState } from 'react';
import { Cpu, Activity, Globe, Play, Plus, RefreshCw, Layers, ShieldCheck, Flame } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CompilerResult, PlasticityResult, UniverseData, EvalResult } from '../../types';

const CONCEPTS = [
  'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
  'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
];

const SingularityLabPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'compiler' | 'plasticity' | 'multiverse'>('compiler');

  // State: Compiler
  const [fnName, setFnName] = useState('semantic_cosine_opt');
  const [cCode, setCCode] = useState('// Version optimisée générée à la volée\ndouble semantic_cosine_opt(double* a, double* b, int n) {\n    double dot = 0.0;\n    // ... calcul matriciel vectorisé C ...\n    return dot;\n}');
  const [compilerResult, setCompilerResult] = useState<CompilerResult | null>(null);

  // State: Plasticity
  const [activations, setActivations] = useState<number[]>(Array(10).fill(0).map(() => Math.random()));
  const [selectedSpikes, setSelectedSpikes] = useState<number[]>([]);
  const [lr, setLr] = useState(0.05);
  const [plasticityResult, setPlasticityResult] = useState<PlasticityResult | null>(null);

  // State: Multiverse
  const [universeName, setUniverseName] = useState('ShinSekai');
  const [genre, setGenre] = useState('Cyberpunk');
  const [synthesizedResult, setSynthesizedResult] = useState<{
    universe: UniverseData;
    evaluation: EvalResult;
    persisted: boolean;
  } | null>(null);

  // Mutations
  const compileMutation = useMutation({
    mutationFn: async () => {
      return apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'compile',
          function_name: fnName,
          slow_logic_code: cCode
        })
      });
    },
    onSuccess: (data) => setCompilerResult(data)
  });

  const plasticityMutation = useMutation({
    mutationFn: async () => {
      const activeActivations = Array(10).fill(0);
      activations.forEach((v, i) => {
        activeActivations[i] = selectedSpikes.includes(i) ? 1.0 : v * 0.3;
      });

      return apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'plasticity',
          activations: activeActivations,
          trigger_spikes: selectedSpikes,
          learning_rate: lr
        })
      });
    },
    onSuccess: (data) => setPlasticityResult(data)
  });

  const synthesizeMutation = useMutation({
    mutationFn: async () => {
      return apiClient('/api/v1/singularity-lab/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'synthesize',
          universe_name: universeName,
          genre: genre
        })
      });
    },
    onSuccess: (data) => setSynthesizedResult(data)
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
      {/* Title */}
      <h1 className="text-6xl font-black italic manga-font mb-6 tracking-tighter uppercase text-center md:text-left">
        SINGULARITY <span className="text-red-500">LAB</span>
      </h1>
      <p className="text-gray-400 max-w-2xl mb-12 text-center md:text-left leading-relaxed">
        Interface d'expérimentation ultime pour les modules IA de cinquième génération (Singularité SOTA 2035+).
      </p>

      {/* Tabs */}
      <div className="flex gap-4 mb-10 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveTab('compiler')}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-black uppercase tracking-widest transition-all ${
            activeTab === 'compiler'
              ? 'bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          <Cpu className="w-4 h-4" /> Méta-Compilateur
        </button>
        <button
          onClick={() => setActiveTab('plasticity')}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-black uppercase tracking-widest transition-all ${
            activeTab === 'plasticity'
              ? 'bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          <Activity className="w-4 h-4" /> Plasticité Synaptique
        </button>
        <button
          onClick={() => setActiveTab('multiverse')}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-black uppercase tracking-widest transition-all ${
            activeTab === 'multiverse'
              ? 'bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          <Globe className="w-4 h-4" /> Synthèse de Multivers
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Sidebar Controls */}
        <div className="lg:col-span-1 space-y-8">
          {activeTab === 'compiler' && (
            <Card padding="lg" className="space-y-6">
              <h3 className="text-xs font-black uppercase opacity-40 tracking-widest">
                Optimisation Dynamique
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-black uppercase text-gray-400 block mb-2">
                    Nom de Fonction
                  </label>
                  <input
                    type="text"
                    value={fnName}
                    onChange={(e) => setFnName(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-bold focus:outline-none focus:border-red-500 transition"
                  />
                </div>
                <Button
                  onClick={() => compileMutation.mutate()}
                  disabled={compileMutation.isPending}
                  variant="primary"
                  fullWidth
                  className="bg-red-500 hover:bg-red-600 border-none shadow-[0_0_15px_rgba(239,68,68,0.2)]"
                >
                  <Play className="w-4 h-4 mr-2" /> Compiler & Exécuter
                </Button>
              </div>
            </Card>
          )}

          {activeTab === 'plasticity' && (
            <Card padding="lg" className="space-y-6">
              <h3 className="text-xs font-black uppercase opacity-40 tracking-widest">
                Apprentissage Hebbien & STDP
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-black uppercase text-gray-400 block mb-2">
                    Learning Rate ({lr.toFixed(3)})
                  </label>
                  <input
                    type="range"
                    min="0.01"
                    max="0.2"
                    step="0.01"
                    value={lr}
                    onChange={(e) => setLr(parseFloat(e.target.value))}
                    className="w-full accent-red-500"
                  />
                </div>
                <Button
                  onClick={() => {
                    const nextAct = activations.map(() => Math.random());
                    setActivations(nextAct);
                  }}
                  variant="outline"
                  fullWidth
                  className="bg-white/5 border-white/10 text-white font-bold"
                >
                  <RefreshCw className="w-4 h-4 mr-2" /> Randomiser Activations
                </Button>
                <Button
                  onClick={() => plasticityMutation.mutate()}
                  disabled={plasticityMutation.isPending}
                  variant="primary"
                  fullWidth
                  className="bg-red-500 hover:bg-red-600 border-none"
                >
                  <Play className="w-4 h-4 mr-2" /> Simuler Spike & Hebb
                </Button>
              </div>
            </Card>
          )}

          {activeTab === 'multiverse' && (
            <Card padding="lg" className="space-y-6">
              <h3 className="text-xs font-black uppercase opacity-40 tracking-widest">
                Paramètres Multivers
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-black uppercase text-gray-400 block mb-2">
                    Nom de l'Univers
                  </label>
                  <input
                    type="text"
                    value={universeName}
                    onChange={(e) => setUniverseName(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-bold focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-black uppercase text-gray-400 block mb-2">
                    Genre Primaire
                  </label>
                  <select
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    className="w-full bg-navy-950 border border-white/10 rounded-xl px-4 py-3 text-sm font-bold text-white focus:outline-none"
                  >
                    <option value="Cyberpunk">Cyberpunk</option>
                    <option value="Sci-Fi">Sci-Fi</option>
                    <option value="Shonen">Shonen</option>
                    <option value="Seinen">Seinen</option>
                    <option value="Fantasy">Fantasy</option>
                    <option value="Documentary">Documentaire (Incohérent)</option>
                  </select>
                </div>
                <Button
                  onClick={() => synthesizeMutation.mutate()}
                  disabled={synthesizeMutation.isPending}
                  variant="primary"
                  fullWidth
                  className="bg-red-500 hover:bg-red-600 border-none shadow-[0_0_15px_rgba(239,68,68,0.2)]"
                >
                  <Plus className="w-4 h-4 mr-2" /> Synthétiser Univers
                </Button>
              </div>
            </Card>
          )}
        </div>

        {/* main Content Area */}
        <div className="lg:col-span-3">
          <div className="bg-black/40 backdrop-blur-xl rounded-[3rem] shadow-2xl overflow-hidden min-h-[600px] relative border border-white/5 flex flex-col p-8 md:p-12">
            
            {/* Loading Overlay */}
            {(compileMutation.isPending || plasticityMutation.isPending || synthesizeMutation.isPending) && (
              <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                <span className="text-white font-black italic uppercase tracking-[0.2em] animate-pulse">Singularity Computing...</span>
              </div>
            )}

            {/* TAB: COMPILER */}
            {activeTab === 'compiler' && (
              <div className="space-y-8 flex-1 flex flex-col">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20">
                    JIT COMPILER SOTA 2035
                  </Badge>
                  <span className="text-xs font-bold text-gray-500">Auto-microcode loading</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
                  {/* Code Editor */}
                  <div className="flex flex-col space-y-4">
                    <span className="text-xs font-black uppercase text-gray-400">Microcode source (C)</span>
                    <textarea
                      value={cCode}
                      onChange={(e) => setCCode(e.target.value)}
                      className="w-full flex-1 min-h-[250px] bg-navy-950/80 border border-white/10 rounded-2xl p-4 font-mono text-xs text-green-400 focus:outline-none focus:border-red-500"
                    />
                  </div>

                  {/* Output */}
                  <div className="bg-white/5 rounded-2xl border border-white/5 p-6 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-black uppercase text-gray-400 block mb-4">Statut Compilation</span>
                      {compilerResult ? (
                        <div className="space-y-4 animate-fade-in">
                          <div className="flex items-center gap-3 text-green-400 font-bold text-sm">
                            <ShieldCheck className="w-5 h-5" /> {compilerResult.message}
                          </div>
                          <p className="text-xs font-bold text-gray-300 leading-relaxed font-mono bg-black/50 p-4 rounded-xl border border-white/5">
                            {compilerResult.test_output}
                          </p>
                          <div className="bg-navy-950 p-4 rounded-xl border border-white/5">
                            <span className="text-[10px] font-black uppercase text-gray-500 block mb-2">Signature chargée</span>
                            <code className="text-[11px] font-mono text-yellow-400 block">{compilerResult.c_code_generated}</code>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-12 opacity-20">
                          <Cpu className="w-20 h-20 mx-auto mb-4" />
                          <span className="text-sm font-black uppercase tracking-wider block">Aucune compilation exécutée</span>
                        </div>
                      )}
                    </div>
                    <div className="border-t border-white/5 pt-4 text-[10px] text-gray-500 italic">
                      * Le JIT compile dynamiquement en microcode ou bascule vers un wrapper vectorisé NumPy hautement optimisé si aucun compilateur GCC/Clang n'est détecté.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: PLASTICITY */}
            {activeTab === 'plasticity' && (
              <div className="space-y-8 flex-1 flex flex-col">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20">
                    PLASTICITÉ SYNAPTIQUE SIMULATOR
                  </Badge>
                  <span className="text-xs font-bold text-gray-500">Spike-Timing-Dependent Plasticity</span>
                </div>

                {/* Activations & Spikes grid */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {CONCEPTS.map((concept, idx) => {
                    const isSpiked = selectedSpikes.includes(idx);
                    return (
                      <button
                        key={concept}
                        onClick={() => toggleSpike(idx)}
                        className={`p-4 rounded-2xl border text-left flex flex-col justify-between h-24 transition-all hover:scale-105 ${
                          isSpiked
                            ? 'bg-red-500 border-red-400 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                            : 'bg-white/5 border-white/5 text-gray-300'
                        }`}
                      >
                        <span className="text-[10px] font-black uppercase tracking-wider block">{concept}</span>
                        <div>
                          <span className="text-xs font-bold block opacity-60">Act.</span>
                          <span className="text-sm font-black font-mono">
                            {isSpiked ? 'SPIKE' : activations[idx].toFixed(2)}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Matrix and STDP Logs */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
                  {/* W Matrix visualization */}
                  <div className="bg-navy-950/80 border border-white/10 rounded-2xl p-6 flex flex-col">
                    <span className="text-xs font-black uppercase text-gray-400 block mb-4">Matrice de Poids Synaptiques (W)</span>
                    {plasticityResult ? (
                      <div className="grid grid-cols-10 gap-1.5 flex-1 items-center justify-center max-w-[350px] mx-auto">
                        {plasticityResult.weights.map((row: number[], rIdx: number) => 
                          row.map((val: number, cIdx: number) => {
                            // Plus la valeur est élevée, plus le vert/bleu est brillant
                            const intensity = Math.floor(val * 255);
                            const color = `rgba(${intensity}, ${intensity > 100 ? 200 : 50}, 239, ${0.1 + val * 0.9})`;
                            return (
                              <div
                                key={`${rIdx}-${cIdx}`}
                                style={{ backgroundColor: color }}
                                className="aspect-square w-6 rounded-md border border-white/5 flex items-center justify-center text-[7px] font-black font-mono text-white/40"
                                title={`Poids [${CONCEPTS[rIdx]} -> ${CONCEPTS[cIdx]}] = ${val.toFixed(3)}`}
                              >
                                {val > 0 ? val.toFixed(1) : '0'}
                              </div>
                            );
                          })
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-12 opacity-25 flex-1 flex flex-col justify-center">
                        <Activity className="w-16 h-16 mx-auto mb-2 text-red-500 animate-pulse" />
                        <span className="text-xs font-bold uppercase block">Simulez pour charger la matrice</span>
                      </div>
                    )}
                  </div>

                  {/* Logs list */}
                  <div className="bg-white/5 rounded-2xl border border-white/5 p-6 flex flex-col">
                    <span className="text-xs font-black uppercase text-gray-400 block mb-4">Rapport STDP / Hebb</span>
                    {plasticityResult ? (
                      <div className="space-y-4 overflow-y-auto max-h-[220px]">
                        <div className="text-green-400 font-bold text-sm bg-green-500/10 p-3 rounded-xl border border-green-500/10">
                          {plasticityResult.message}
                        </div>
                        {plasticityResult.stdp_log.map((log: string, idx: number) => (
                          <div key={idx} className="font-mono text-xs text-yellow-400 flex items-center gap-2">
                            <Flame className="w-4 h-4 text-red-500" /> {log}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 opacity-20 flex-1 flex flex-col justify-center">
                        <span className="text-xs font-bold uppercase tracking-wider block">Aucun historique de spikes</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB: MULTIVERSE */}
            {activeTab === 'multiverse' && (
              <div className="space-y-8 flex-1 flex flex-col">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20">
                    ADMS NARRATIVE GENERATOR
                  </Badge>
                  <span className="text-xs font-bold text-gray-500">Autonomous Domain Synthesizer</span>
                </div>

                {synthesizedResult ? (
                  <div className="space-y-6 flex-1 overflow-y-auto animate-fade-in pr-2 max-h-[480px]">
                    
                    {/* Status & Scores */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-white/5 rounded-2xl border border-white/5 p-4 flex flex-col justify-between h-28">
                        <span className="text-[10px] font-black uppercase text-gray-500 block">Cohérence (IA)</span>
                        <div className="flex items-end justify-between">
                          <span className={`text-4xl font-black font-mono ${synthesizedResult.evaluation.ai_score >= 0.7 ? 'text-green-400' : 'text-red-400'}`}>
                            {(synthesizedResult.evaluation.ai_score * 100).toFixed(0)}%
                          </span>
                          <span className="text-xs font-bold text-gray-400">Seuil : 70%</span>
                        </div>
                      </div>
                      <div className="bg-white/5 rounded-2xl border border-white/5 p-4 flex flex-col justify-between h-28">
                        <span className="text-[10px] font-black uppercase text-gray-500 block">Popularité Communautaire</span>
                        <div className="flex items-end justify-between">
                          <span className={`text-4xl font-black font-mono ${synthesizedResult.evaluation.community_score >= 0.7 ? 'text-green-400' : 'text-red-400'}`}>
                            {(synthesizedResult.evaluation.community_score * 100).toFixed(0)}%
                          </span>
                          <span className="text-xs font-bold text-gray-400">Seuil : 70%</span>
                        </div>
                      </div>
                      <div className="bg-white/5 rounded-2xl border border-white/5 p-4 flex flex-col justify-between h-28">
                        <span className="text-[10px] font-black uppercase text-gray-500 block">Statut Enregistrement Neo4j</span>
                        <div className="flex items-end justify-between">
                          {synthesizedResult.persisted ? (
                            <span className="text-xl font-black text-green-400 uppercase tracking-wider flex items-center gap-2">
                              <ShieldCheck className="w-6 h-6" /> PERSISTÉ !
                            </span>
                          ) : (
                            <span className="text-xl font-black text-red-500 uppercase tracking-wider">
                              REJETÉ
                            </span>
                          )}
                          <span className="text-[9px] font-black text-gray-500 uppercase max-w-[120px] text-right">
                            {synthesizedResult.persisted ? 'Enregistré dans le graphe' : 'Qualité insuffisante'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Universe Content */}
                    <div className="bg-navy-950 p-8 rounded-[2rem] border border-white/5 space-y-6">
                      <div className="flex justify-between items-center border-b border-white/5 pb-4">
                        <h2 className="text-2xl font-black italic text-yellow-400">{synthesizedResult.universe.name}</h2>
                        <Badge variant="primary" className="bg-yellow-400/10 text-yellow-400 border-yellow-400/20 uppercase tracking-widest text-[9px] font-black">
                          {synthesizedResult.universe.genre}
                        </Badge>
                      </div>
                      <p className="text-sm font-bold text-gray-300 leading-relaxed italic">{synthesizedResult.universe.description}</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
                        {/* Characters */}
                        <div className="space-y-4">
                          <h4 className="text-xs font-black uppercase text-gray-400 tracking-wider">Personnages Synthétisés</h4>
                          <div className="space-y-3">
                            {synthesizedResult.universe.characters.map((char) => (
                              <div key={char.name} className="bg-white/5 border border-white/5 p-4 rounded-xl flex justify-between items-center">
                                <div>
                                  <span className="font-black text-sm text-white block">{char.name}</span>
                                  <span className="text-[11px] text-gray-400 block">{char.role}</span>
                                </div>
                                <Badge variant="primary" className="bg-red-500/10 text-red-500 border-red-500/20 font-mono">
                                  PL: {char.power_level}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Episodes */}
                        <div className="space-y-4">
                          <h4 className="text-xs font-black uppercase text-gray-400 tracking-wider">Épisodes Synthétisés</h4>
                          <div className="space-y-3">
                            {synthesizedResult.universe.episodes.map((ep) => (
                              <div key={ep.number} className="bg-white/5 border border-white/5 p-4 rounded-xl space-y-1">
                                <span className="font-black text-xs text-yellow-400 block">Épisode {ep.number} : {ep.title}</span>
                                <p className="text-[11px] text-gray-300 leading-relaxed">{ep.summary}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-20 opacity-20 flex-1 flex flex-col justify-center">
                    <Globe className="w-24 h-24 mx-auto mb-4" />
                    <span className="text-lg font-black uppercase tracking-wider block">Générez un nouvel univers</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SingularityLabPage;
