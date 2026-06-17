import React, { useState } from 'react';
import { 
  Cpu,
  Loader2,
  ShieldCheck,
  Zap,
  Target,
  Terminal,
  Code,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

import { CompilerResult } from '../../types';

const CompilerLabPage: React.FC = () => {
  const [fnName, setFnName] = useState('semantic_cosine_opt');
  const [cCode, setCCode] = useState('// Version optimisée générée à la volée\ndouble semantic_cosine_opt(double* a, double* b, int n) {\n    double dot = 0.0;\n    // ... calcul matriciel vectorisé C ...\n    return dot;\n}');
  const [compilerResult, setCompilerResult] = useState<CompilerResult | null>(null);

  const compileMutation = useMutation<CompilerResult, Error, { action: string; function_name: string }>({
    mutationFn: (body: { action: string; function_name: string }) => 
        apiClient('/api/v1/singularity-lab/', { 
            method: 'POST', 
            body: JSON.stringify(body) 
        }),
    onSuccess: (data) => setCompilerResult(data)
  });

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-400 mb-4">
                  <Terminal className="w-3 h-3" /> Self-Evolving Compiler
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  JIT <span className="text-red-600 text-glow">OPTIMIZER</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Optimisation temps réel du microcode sémantique via compilation JIT SOTA 2035.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Configuration */}
              <div className="lg:col-span-4 space-y-8">
                  <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                          <Cpu className="w-24 h-24 rotate-12" />
                      </div>
                      
                      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                          <Target className="w-4 h-4 text-red-500" /> Optimization Parameters
                      </h3>

                      <div className="space-y-8">
                          <div className="space-y-4">
                              <label htmlFor="fn-name" className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] px-2">Fonction Cible</label>
                              <input 
                                  id="fn-name"
                                  type="text" 
                                  value={fnName} 
                                  onChange={(e) => setFnName(e.target.value)} 
                                  className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold focus:border-red-500 outline-none transition-all text-white" 
                              />
                          </div>

                          <Button 
                              onClick={() => compileMutation.mutate({ action: 'compile', function_name: fnName })} 
                              disabled={compileMutation.isPending} 
                              className="w-full bg-red-600 hover:bg-red-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                          >
                              {compileMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "LANCER L'OPTIMISATION"}
                          </Button>
                      </div>
                  </Card>

                  <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                      <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-red-400">Pipeline JIT</h4>
                      <p className="text-[10px] font-bold uppercase leading-relaxed mb-4">
                          L'IA analyse le graphe d'exécution et génère du code C vectorisé pour les calculs de similarité critique.
                      </p>
                      <ul className="space-y-3">
                          <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                              <div className="w-1 h-1 rounded-full bg-red-500 mt-1" /> Vectorisation AVX-512.
                          </li>
                          <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                              <div className="w-1 h-1 rounded-full bg-red-500 mt-1" /> Low-latency microcode injection.
                          </li>
                      </ul>
                  </Card>
              </div>

              {/* Microcode & Status */}
              <div className="lg:col-span-8 space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
                      <div className="flex flex-col space-y-4">
                          <div className="flex justify-between items-center px-4">
                              <span className="text-[10px] font-black uppercase opacity-30 tracking-widest">Microcode Source (C)</span>
                              <Badge variant="neutral" className="bg-white/5 border-none text-[8px] uppercase">Read Only</Badge>
                          </div>
                          <div className="relative flex-1 group min-h-[450px]">
                              <textarea 
                                  readOnly
                                  value={cCode} 
                                  onChange={(e) => setCCode(e.target.value)} 
                                  className="w-full h-full bg-navy-950 border border-white/10 rounded-[2.5rem] p-10 font-mono text-sm text-green-400 focus:outline-none focus:border-red-500 transition-all custom-scrollbar resize-none" 
                              />
                              <div className="absolute top-6 right-6 opacity-20">
                                  <Code className="w-8 h-8" />
                              </div>
                          </div>
                      </div>

                      <div className="bg-white/5 rounded-[2.5rem] border border-white/5 p-10 flex flex-col justify-between shadow-2xl relative overflow-hidden min-h-[450px]">
                          <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/5 blur-[80px] -mr-32 -mt-32" />
                          
                          <div>
                              <span className="text-[10px] font-black uppercase opacity-30 block mb-10 tracking-widest">Compilation Status</span>
                              
                              <AnimatePresence mode="wait">
                                  {compilerResult ? (
                                      <motion.div 
                                          initial={{ opacity: 0, y: 10 }} 
                                          animate={{ opacity: 1, y: 0 }} 
                                          className="space-y-8 relative z-10"
                                      >
                                          <div className="flex items-center gap-4 text-emerald-400 font-black italic text-lg uppercase tracking-tight">
                                              <ShieldCheck className="w-8 h-8" /> {compilerResult.message}
                                          </div>
                                          
                                          <div className="p-8 bg-black/60 rounded-3xl border border-white/10 space-y-4">
                                              <p className="text-[10px] font-black uppercase opacity-30 tracking-widest">Performance Bench</p>
                                              <p className="text-sm font-bold text-gray-300 leading-relaxed font-mono italic">
                                                  {compilerResult.test_output}
                                              </p>
                                          </div>

                                          <div className="bg-navy-950/80 p-8 rounded-3xl border border-white/5">
                                              <span className="text-[10px] font-black uppercase text-gray-500 block mb-4 tracking-widest">Runtime Signature</span>
                                              <code className="text-xs font-mono text-yellow-400 block break-all">
                                                  {compilerResult.c_code_generated || "NO_SIGNATURE_GENERATED"}
                                              </code>
                                          </div>
                                      </motion.div>
                                  ) : (
                                      <div className="flex-1 flex flex-col items-center justify-center py-20 opacity-10">
                                          <Cpu className="w-24 h-24 mx-auto mb-8 animate-pulse" />
                                          <span className="text-sm font-black uppercase tracking-[0.3em] block text-center">En attente de déploiement</span>
                                      </div>
                                  )}
                              </AnimatePresence>
                          </div>

                          <div className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center opacity-30">
                              <span className="text-[8px] font-black uppercase tracking-widest">LLVM Backend 18.1</span>
                              <Zap className="w-4 h-4 text-yellow-500" />
                          </div>
                      </div>
                  </div>
              </div>
          </div>

          {/* Global Warning & Guide */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(220,38,38,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Terminal className="w-64 h-64 text-red-600" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-red-400" /> Guide du Compilateur Évolutif
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-500">Auto-Optimisation :</span> Contrairement aux logiciels classiques, notre IA analyse son propre code en temps réel pour détecter des goulots d'étranglement mathématiques.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-500">Génération de Kernel :</span> Si une fonction est trop lente (ex: calcul de similarité), le compilateur génère une version ultra-optimisée en langage C (bas niveau) et l'injecte instantanément.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-500">Performance :</span> Ce processus permet à Animetix de rester fluide même lors de calculs massifs sur des milliers d'archétypes simultanément.
                      </p>
                  </div>
              </Card>

              <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed text-red-200/40">
                      Backend LLVM : Les noyaux de calcul sont compilés via Clang/LLVM avec optimisations AVX-512. <br />
                      L'injection de code dynamique est sécurisée par un sandbox matériel isolé.
                  </p>
              </div>
          </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default CompilerLabPage;
