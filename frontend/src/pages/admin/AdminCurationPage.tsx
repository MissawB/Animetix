import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Edit3, 
  Save, 
  X, 
  Info, 
  Check, 
  Database, 
  LayoutGrid, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Network
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useDPO } from '../../features/admin/hooks/useDPO';
import { useCurationTickets } from '../../features/admin/hooks/useCurationTickets';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const AdminCurationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dpo' | 'graph'>('dpo');
  const { feedbacks, isLoading: isDPOLoading, curate, isSubmitting: isDPOSubmitting } = useDPO();
  const { tickets, isLoading: isGraphLoading, stats: graphStats, resolve, isResolving } = useCurationTickets();
  const [editingDPOId, setEditingDPOId] = useState<number | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  
  const { register, handleSubmit, reset } = useForm<{ chosen_text: string }>();

  const onDPOSubmit = async (data: { chosen_text: string }, feedbackId: number) => {
    await curate({ feedback_id: feedbackId, chosen_text: data.chosen_text });
    setEditingDPOId(null);
    reset();
  };

  const isLoading = activeTab === 'dpo' ? isDPOLoading : isGraphLoading;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-16">
          
          {/* Header */}
          <div className="flex flex-col md:flex-row items-center justify-between mb-12 gap-8">
            <div>
              <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-2 text-black dark:text-white">
                CURATION <span className="text-red-500 text-glow">CENTER</span>
              </h1>
              <p className="text-xs font-black opacity-40 uppercase tracking-[0.3em] text-black dark:text-white">
                Alignement Sémantique & Intégrité du Knowledge Graph
              </p>
            </div>
            
            <div className="flex bg-black/5 dark:bg-white/5 p-1 rounded-3xl border border-black/5 dark:border-white/10 shadow-inner">
                <button 
                    onClick={() => setActiveTab('dpo')}
                    className={`px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'dpo' ? 'bg-red-500 text-white shadow-lg' : 'text-gray-400 hover:text-black dark:hover:text-white'}`}
                >
                    DPO Feedback ({feedbacks.length})
                </button>
                <button 
                    onClick={() => setActiveTab('graph')}
                    className={`px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'graph' ? 'bg-cyan-500 text-white shadow-lg' : 'text-gray-400 hover:text-black dark:hover:text-white'}`}
                >
                    Graph Healer ({tickets.length})
                </button>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-8">
              <CardSkeleton /><CardSkeleton />
            </div>
          ) : (
            <AnimatePresence mode="wait">
              {activeTab === 'dpo' ? (
                <motion.div 
                    key="dpo-tab"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="space-y-8"
                >
                    {feedbacks.map((fb: any) => (
                        <Card key={fb.id} padding="lg" className="relative overflow-hidden group border-none shadow-xl bg-white dark:bg-[#0f0f1a]">
                            <div className="absolute top-0 left-0 w-1.5 h-full bg-red-500 opacity-20 group-hover:opacity-100 transition-opacity" />
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 text-black dark:text-white">
                                <div className="space-y-6">
                                    <div>
                                        <h4 className="text-[10px] font-black uppercase opacity-30 mb-3 flex items-center gap-2">
                                            <Info className="w-3 h-3" /> Contexte Utilisateur
                                        </h4>
                                        <div className="bg-gray-50 dark:bg-black/20 p-5 rounded-2xl text-xs font-medium italic border border-black/5 dark:border-white/5">
                                            "{fb.context}"
                                        </div>
                                    </div>
                                    <div>
                                        <h4 className="text-[10px] font-black uppercase text-red-500/50 mb-3">Réponse Rejetée</h4>
                                        <div className="bg-red-500/5 p-5 rounded-2xl text-xs font-bold border border-red-500/10 text-red-600 dark:text-red-400">
                                            {fb.output}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col justify-center">
                                    {editingDPOId === fb.id ? (
                                        <form onSubmit={handleSubmit((d) => onDPOSubmit(d, fb.id))} className="space-y-4">
                                            <h4 className="text-[10px] font-black uppercase text-green-500/50">Réponse Idéale (Chosen)</h4>
                                            <textarea 
                                                {...register('chosen_text', { required: true })}
                                                className="w-full p-6 rounded-2xl bg-green-500/5 border-2 border-green-500/20 focus:border-green-500 outline-none text-xs font-bold min-h-[150px] dark:text-white"
                                                placeholder="Tapez la réponse parfaite..."
                                            />
                                            <div className="flex gap-3">
                                                <Button type="submit" variant="success" size="sm" disabled={isDPOSubmitting}>
                                                    <Save className="w-4 h-4" /> Valider
                                                </Button>
                                                <Button variant="outline" size="sm" onClick={() => setEditingDPOId(null)}>
                                                    <X className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </form>
                                    ) : (
                                        <div className="text-center py-8 space-y-6">
                                            <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto shadow-inner">
                                                <ShieldAlert className="w-8 h-8" />
                                            </div>
                                            <Button variant="primary" onClick={() => setEditingDPOId(fb.id)}>
                                                <Edit3 className="w-4 h-4" /> RÉPARER LE RAISONNEMENT
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </Card>
                    ))}

                    {feedbacks.length === 0 && (
                        <div className="text-center py-24 opacity-20 uppercase font-black tracking-widest animate-pulse italic text-black dark:text-white">
                            <Check className="w-20 h-20 mx-auto mb-4" />
                            Toutes les erreurs DPO ont été corrigées. <br />
                            Modèle aligné avec les préférences humaines.
                        </div>
                    )}
                </motion.div>
              ) : (
                <motion.div 
                    key="graph-tab"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="grid grid-cols-1 lg:grid-cols-3 gap-8"
                >
                    {/* Tickets List */}
                    <div className="lg:col-span-1 space-y-4">
                        <h3 className="text-xs font-black uppercase tracking-widest opacity-40 mb-6 flex items-center gap-2 text-black dark:text-white">
                            <Clock size={14} /> Flux des Contradictions
                        </h3>
                        <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2 no-scrollbar">
                            {tickets.map((ticket: any) => (
                                <motion.button
                                    whileHover={{ x: 5 }}
                                    key={ticket.id}
                                    onClick={() => setSelectedTicket(ticket)}
                                    className={`w-full text-left p-5 rounded-[2rem] border transition-all ${
                                        selectedTicket?.id === ticket.id 
                                        ? 'bg-cyan-500 text-white border-cyan-500 shadow-xl scale-[1.02]' 
                                        : 'bg-white dark:bg-gray-900/40 border-black/5 dark:border-white/5 text-black dark:text-white hover:border-cyan-500/50'
                                    }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <Badge variant={ticket.is_resolved ? 'success' : 'neutral'} className="text-[8px]">
                                            {ticket.is_resolved ? 'Résolu' : 'En Attente'}
                                        </Badge>
                                        <span className={`font-mono text-[9px] ${selectedTicket?.id === ticket.id ? 'text-white/50' : 'opacity-30'}`}>#{ticket.id}</span>
                                    </div>
                                    <h4 className="font-black italic uppercase text-sm truncate">{ticket.item_title}</h4>
                                    <p className={`text-[10px] line-clamp-1 mt-1 font-medium ${selectedTicket?.id === ticket.id ? 'text-white/70' : 'opacity-40'}`}>
                                        {ticket.issue_description}
                                    </p>
                                </motion.button>
                            ))}

                            {tickets.length === 0 && (
                                <div className="text-center py-12 opacity-20 uppercase font-black tracking-widest italic text-black dark:text-white">
                                    Aucun ticket de contradiction.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Ticket Detail */}
                    <div className="lg:col-span-2">
                        <AnimatePresence mode="wait">
                            {selectedTicket ? (
                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    key={selectedTicket.id}
                                    className="bg-white dark:bg-gray-900/50 backdrop-blur-xl rounded-[3rem] border border-black/5 dark:border-white/5 overflow-hidden shadow-2xl"
                                >
                                    <div className="p-8 border-b border-black/5 dark:border-white/5 bg-gradient-to-r from-cyan-500/10 to-transparent flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                                        <div>
                                            <h2 className="text-3xl font-black italic uppercase tracking-tighter text-black dark:text-white">{selectedTicket.item_title}</h2>
                                            <div className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mt-1 text-black dark:text-white">
                                                Détecté le {new Date(selectedTicket.created_at).toLocaleString()}
                                            </div>
                                        </div>
                                        {!selectedTicket.is_resolved && (
                                            <Button 
                                                onClick={() => {
                                                    resolve(selectedTicket.id);
                                                    setSelectedTicket({...selectedTicket, is_resolved: true});
                                                }}
                                                disabled={isResolving}
                                                variant="success"
                                                className="rounded-2xl px-8 py-6 font-black italic uppercase tracking-widest shadow-lg shadow-green-500/20"
                                            >
                                                <CheckCircle2 className="w-5 h-5 mr-2" /> Approuver le Healer
                                            </Button>
                                        )}
                                    </div>

                                    <div className="p-8 space-y-8 text-black dark:text-white">
                                        <section>
                                            <h4 className="text-[10px] font-black uppercase tracking-widest text-cyan-500 mb-4 flex items-center gap-2">
                                                <AlertCircle size={14} /> Rapport de Contradiction
                                            </h4>
                                            <div className="bg-gray-50 dark:bg-black/40 p-6 rounded-2xl text-xs italic leading-relaxed border-l-4 border-cyan-500 font-medium">
                                                "{selectedTicket.issue_description}"
                                            </div>
                                        </section>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <section>
                                                <h4 className="text-[10px] font-black uppercase tracking-widest opacity-30 mb-4 flex items-center gap-2">
                                                    <Database size={14} /> PostgreSQL Source
                                                </h4>
                                                <pre className="bg-gray-50 dark:bg-black/60 p-5 rounded-2xl text-[10px] font-mono opacity-60 overflow-x-auto max-h-60 border border-black/5 dark:border-white/5">
                                                    {JSON.stringify(selectedTicket.source_pg, null, 2)}
                                                </pre>
                                            </section>
                                            <section>
                                                <h4 className="text-[10px] font-black uppercase tracking-widest opacity-30 mb-4 flex items-center gap-2">
                                                    <Network size={14} /> Neo4j Source
                                                </h4>
                                                <pre className="bg-gray-50 dark:bg-black/60 p-5 rounded-2xl text-[10px] font-mono opacity-60 overflow-x-auto max-h-60 border border-black/5 dark:border-white/5">
                                                    {JSON.stringify(selectedTicket.source_neo4j, null, 2)}
                                                </pre>
                                            </section>
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                <div className="h-full min-h-[500px] border-4 border-dashed border-black/5 dark:border-white/5 rounded-[4rem] flex flex-col items-center justify-center text-center p-12">
                                    <div className="w-24 h-24 bg-cyan-500/10 text-cyan-500 rounded-full flex items-center justify-center mb-8 shadow-inner">
                                        <Database size={40} />
                                    </div>
                                    <h3 className="text-2xl font-black italic uppercase text-black/20 dark:text-white/20">SÉLECTIONNEZ UN TICKET</h3>
                                    <p className="text-black/30 dark:text-white/30 text-xs font-bold uppercase tracking-widest max-w-xs mx-auto mt-4">
                                        Les agents IA "Healers" génèrent ces tickets lorsqu'ils détectent une dérive sémantique entre les bases de données.
                                    </p>
                                </div>
                            )}
                        </AnimatePresence>
                    </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}

          {/* Footer stats / Global info */}
          <div className="mt-24 p-12 rounded-[4rem] bg-white dark:bg-[#0f0f1a] shadow-2xl border border-black/5 dark:border-white/5 flex flex-col md:flex-row items-center justify-between gap-12 text-black dark:text-white">
              <div className="flex items-center gap-8">
                  <div className="p-5 bg-red-500 rounded-3xl shadow-xl shadow-red-500/20">
                      <ShieldAlert className="w-8 h-8 text-white" />
                  </div>
                  <div>
                      <h4 className="text-2xl font-black italic manga-font uppercase tracking-tighter">Curation System v4.2</h4>
                      <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.3em]">Module de Supervision Cognitive</p>
                  </div>
              </div>
              
              <div className="flex gap-12">
                  <div className="text-center">
                      <p className="text-[10px] font-black uppercase opacity-30 mb-2">Santé du Graphe</p>
                      <p className="text-4xl font-black italic manga-font text-cyan-500">{graphStats?.health_score || 0}%</p>
                  </div>
                  <div className="text-center">
                      <p className="text-[10px] font-black uppercase opacity-30 mb-2">Alignement DPO</p>
                      <p className="text-4xl font-black italic manga-font text-red-500">{feedbacks.length === 0 ? 'STABLE' : 'DRIFT'}</p>
                  </div>
              </div>
          </div>

        </div>
      </div>
    </AnimatedPage>
  );
};

export default AdminCurationPage;
