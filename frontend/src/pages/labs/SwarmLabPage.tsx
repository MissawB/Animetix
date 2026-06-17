import React, { useState } from 'react';
import { 
  Users,
  BarChart3,
  Loader2,
  ShieldCheck,
  Activity,
  MessageSquare,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

interface SwarmResult {
    consensus_score: number;
    is_recorded: boolean;
    votes: Record<string, number>;
    phases?: {
        prepare?: {
            proposal_id: number;
            promises_received: string[];
        };
        accept?: {
            quorum_required: number;
            threshold: number;
        };
        learn?: {
            paxos_state: string;
            message: string;
        };
    };
}

const SwarmLabPage: React.FC = () => {
  const [swarmFact, setSwarmFact] = useState('Luffy est plus fort que Naruto.');
  const [swarmMedia, setSwarmMedia] = useState('One Piece');
  const [swarmResult, setSwarmResult] = useState<SwarmResult | null>(null);

  const swarmMutation = useMutation<SwarmResult, Error, { action: string; fact: string; media: string }>({
    mutationFn: (body: { action: string; fact: string; media: string }) => 
        apiClient('/api/v1/singularity-lab/', { 
            method: 'POST', 
            body: JSON.stringify(body) 
        }),
    onSuccess: (data) => setSwarmResult(data)
  });

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-4">
                  <Users className="w-3 h-3" /> Swarm Intelligence Protocol
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  SWARM <span className="text-emerald-500 text-glow">CONSENSUS</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Validation décentralisée des faits de lore par un essaim d'agents IA multi-spécialisés.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Configuration */}
              <div className="lg:col-span-4 space-y-8">
                  <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                          <Users className="w-24 h-24 rotate-12" />
                      </div>
                      
                      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-emerald-500" /> Consensus Proposal
                      </h3>

                      <div className="space-y-8">
                          <div className="space-y-6">
                              <div className="space-y-2">
                                  <label htmlFor="swarm-media" className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Média Cible</label>
                                  <input 
                                      id="swarm-media"
                                      type="text" 
                                      value={swarmMedia} 
                                      onChange={(e) => setSwarmMedia(e.target.value)} 
                                      placeholder="Nom de l'anime/manga..." 
                                      className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold focus:border-emerald-500 outline-none transition-all" 
                                  />
                              </div>
                              <div className="space-y-2">
                                  <label htmlFor="swarm-fact" className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Fait Sémantique</label>
                                  <textarea 
                                      id="swarm-fact"
                                      value={swarmFact} 
                                      onChange={(e) => setSwarmFact(e.target.value)} 
                                      rows={4} 
                                      placeholder="Ex: Le Gear 5 représente la liberté absolue..." 
                                      className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold outline-none resize-none focus:border-emerald-500 transition-all" 
                                  />
                              </div>
                          </div>

                          <Button 
                              onClick={() => swarmMutation.mutate({ action: 'swarm', fact: swarmFact, media: swarmMedia })} 
                              disabled={swarmMutation.isPending} 
                              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                          >
                              {swarmMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "LANCER VOTE ESSAIM"}
                          </Button>
                      </div>
                  </Card>

                  <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                      <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-emerald-400">Mécanique de l'Essaim</h4>
                      <p className="text-[10px] font-bold uppercase leading-relaxed mb-4">
                          Chaque proposition est soumise à 7 agents IA (Lore-Keeper, Logic-Gate, Sentiment-Scanner, etc.).
                      </p>
                      <ul className="space-y-3">
                          <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                              <div className="w-1 h-1 rounded-full bg-emerald-500 mt-1" /> Seuil de consensus : 70%.
                          </li>
                          <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                              <div className="w-1 h-1 rounded-full bg-emerald-500 mt-1" /> Persistance automatique si validé.
                          </li>
                      </ul>
                  </Card>
              </div>

              {/* Resultats */}
              <div className="lg:col-span-8">
                  <AnimatePresence mode="wait">
                      {swarmResult ? (
                          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-12">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                  <Card padding="lg" className="bg-emerald-500/5 border-emerald-500/20 text-center flex flex-col items-center justify-center py-12 shadow-2xl">
                                      <span className="text-[10px] font-black uppercase opacity-40 block mb-4 tracking-[0.2em]">Consensus Score</span>
                                      <div className="text-8xl font-black italic text-emerald-500 manga-font leading-none mb-4">
                                          {((swarmResult.consensus_score || 0) * 100).toFixed(1)}%
                                      </div>
                                      <div className="w-24 h-1 bg-emerald-500/20 rounded-full overflow-hidden">
                                          <div className="h-full bg-emerald-500 shadow-[0_0_10px_#10b981]" style={{ width: `${(swarmResult.consensus_score || 0) * 100}%` }} />
                                      </div>
                                  </Card>

                                  <Card padding="lg" className="bg-navy-950 border-white/5 text-center flex flex-col justify-center py-12">
                                      <span className="text-[10px] font-black uppercase opacity-40 block mb-6 tracking-[0.2em]">Collective Decision</span>
                                      <div className={`text-3xl font-black italic uppercase manga-font ${swarmResult.is_recorded ? 'text-blue-400' : 'text-red-400'}`}>
                                          {swarmResult.is_recorded ? 'FACT ACCEPTED' : 'FACT REJECTED'}
                                      </div>
                                      <p className="text-[8px] font-bold opacity-30 mt-4 uppercase tracking-widest">
                                          {swarmResult.is_recorded ? 'Intégré au Knowledge Graph' : 'Proposition rejetée par l\'essaim'}
                                      </p>
                                  </Card>

                                  <Card padding="lg" className="bg-navy-950 border-white/5 text-center flex flex-col justify-center py-12">
                                      <span className="text-[10px] font-black uppercase opacity-40 block mb-6 tracking-[0.2em]">Agent Pool</span>
                                      <div className="text-3xl font-black italic uppercase text-white manga-font">7 MULTI-AGENTS</div>
                                      <div className="flex gap-1 justify-center mt-4 opacity-30">
                                          {Array(7).fill(0).map((_, i) => <div key={i} className="w-1.5 h-1.5 rounded-full bg-white" />)}
                                      </div>
                                  </Card>
                              </div>

                              <div className="space-y-8">
                                  <h4 className="text-xs font-black uppercase tracking-widest opacity-40 flex items-center gap-3">
                                      <BarChart3 className="w-5 h-5 text-emerald-500" /> Répartition Individuelle des Votes
                                  </h4>
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                      {swarmResult.votes && Object.entries(swarmResult.votes).map(([agent, score]: [string, number]) => (
                                          <div key={agent} className="p-6 bg-black/40 rounded-[2rem] border border-white/5 space-y-4 group hover:border-emerald-500/30 transition-all">
                                              <div className="flex justify-between items-center">
                                                  <span className="text-[10px] font-black uppercase text-gray-500 tracking-tighter">{agent.replace('_', ' ')}</span>
                                                  <span className={`text-xs font-black ${score >= 0.7 ? 'text-emerald-500' : 'text-red-500'}`}>
                                                      {Math.round(score * 100)}%
                                                  </span>
                                              </div>
                                              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                  <div className={`h-full transition-all duration-1000 ${score >= 0.7 ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`} style={{ width: `${score * 100}%` }} />
                                              </div>
                                              <Badge variant="neutral" className="w-full bg-white/5 border-none text-[8px] font-black italic uppercase text-center">
                                                  {score >= 0.7 ? 'CONFIRMED' : 'DOUBT'}
                                              </Badge>
                                          </div>
                                      ))}
                                  </div>
                              </div>

                              <Card padding="lg" className="bg-blue-600/10 border-blue-500/20 relative overflow-hidden">
                                  <div className="absolute top-0 right-0 p-4 opacity-5">
                                      <ShieldCheck className="w-12 h-12" />
                                  </div>
                                  <p className="text-sm font-bold italic leading-relaxed opacity-80 text-blue-100 uppercase tracking-tight">
                                      "L'intelligence collective de l'essaim permet de filtrer les hallucinations et les biais individuels des agents en exigeant un consensus sémantique avant toute mise à jour du Knowledge Graph."
                                  </p>
                              </Card>

                              {/* Paxos-Semantic Diagnostics */}
                              {swarmResult.phases && (
                                <section className="space-y-8">
                                    <h4 className="text-xs font-black uppercase tracking-widest opacity-40 flex items-center gap-3">
                                        <Activity className="w-5 h-5 text-blue-500" /> Diagnostics Paxos-Sémantique
                                    </h4>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {/* Phase 1: Prepare */}
                                        <div className="p-6 bg-white/5 border border-white/10 rounded-3xl space-y-4">
                                            <div className="flex items-center justify-between">
                                                <Badge variant="neutral" className="bg-blue-500/20 text-blue-400 border-none text-[7px] uppercase">Phase 1: Prepare</Badge>
                                                <span className="text-[10px] font-black text-blue-500">{swarmResult.phases?.prepare?.proposal_id}</span>
                                            </div>
                                            <h5 className="text-[10px] font-black uppercase opacity-60">Promises Received</h5>
                                            <div className="flex flex-wrap gap-2">
                                                {swarmResult.phases?.prepare?.promises_received?.map((a: string) => (
                                                    <span key={a} className="text-[8px] font-bold px-2 py-1 bg-white/5 rounded-lg text-white/40">{a}</span>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Phase 2: Accept */}
                                        <div className="p-6 bg-white/5 border border-white/10 rounded-3xl space-y-4">
                                            <div className="flex items-center justify-between">
                                                <Badge variant="neutral" className="bg-yellow-500/20 text-yellow-400 border-none text-[7px] uppercase">Phase 2: Accept</Badge>
                                                <span className="text-[10px] font-black text-yellow-500">Quorum: {swarmResult.phases?.accept?.quorum_required}</span>
                                            </div>
                                            <h5 className="text-[10px] font-black uppercase opacity-60">Ballot Casting</h5>
                                            <p className="text-[9px] font-bold opacity-30 uppercase italic leading-tight">
                                                Vérification de la cohérence sémantique par rapport au seuil de {(swarmResult.phases?.accept?.threshold || 0.7) * 100}%.
                                            </p>
                                        </div>

                                        {/* Phase 3: Learn */}
                                        <div className="p-6 bg-white/5 border border-white/10 rounded-3xl space-y-4">
                                            <div className="flex items-center justify-between">
                                                <Badge variant="neutral" className="bg-emerald-500/20 text-emerald-400 border-none text-[7px] uppercase">Phase 3: Learn</Badge>
                                                <span className="text-[10px] font-black text-emerald-500">{swarmResult.phases?.learn?.paxos_state}</span>
                                            </div>
                                            <h5 className="text-[10px] font-black uppercase opacity-60">Global Decision</h5>
                                            <p className="text-[9px] font-bold opacity-40 uppercase text-emerald-400">
                                                {swarmResult.phases?.learn?.message}
                                            </p>
                                        </div>
                                    </div>
                                </section>
                              )}
                          </motion.div>
                      ) : (
                          <div className="h-full flex flex-col items-center justify-center py-32 opacity-10 text-center border-4 border-dashed border-white/5 rounded-[4rem]">
                              <Users className="w-48 h-48 mb-12" />
                              <h3 className="text-5xl font-black italic uppercase manga-font mb-4">Essaim en Veille</h3>
                              <p className="text-lg font-bold uppercase tracking-[0.4em]">En attente d'une proposition de fait pour arbitrage collectif.</p>
                          </div>
                      )}
                  </AnimatePresence>
              </div>
          </div>

          {/* Global Warning & Guide */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Users className="w-64 h-64 text-emerald-500" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-emerald-400" /> Guide de l'Essaim
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-emerald-400">Le Concept :</span> Un agent IA peut se tromper ou avoir des biais. L'essaim (Swarm) est une équipe de 7 IA expertes qui analysent vos propositions sous différents angles.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-emerald-400">Le Vote :</span> Pour qu'un fait soit validé, il doit obtenir un consensus de 70%. C'est une démocratie numérique où la majorité qualifiée l'emporte.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-emerald-400">Paxos-Sémantique :</span> C'est le protocole de "serrage de main" entre les IA. Il garantit que tous les agents ont bien reçu et compris l'information avant de l'accepter.
                      </p>
                  </div>
              </Card>

              <div className="p-12 rounded-[4rem] bg-gradient-to-br from-emerald-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed text-emerald-200/40">
                      Protocole Consensus : Les votes sont arbitrés via un algorithme de consensus distribué. <br />
                      Les faits validés sont injectés de manière permanente dans la matrice de lore.
                  </p>
              </div>
          </div>
        </div>
      </AnimatedPage>

    </div>
  );
};

export default SwarmLabPage;
