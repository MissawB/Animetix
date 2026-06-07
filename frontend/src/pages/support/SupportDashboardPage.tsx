import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { HelpCircle, Plus, ThumbsUp, ThumbsDown, Zap, ArrowLeft, Brain } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { apiClient } from '../../utils/apiClient';
import { Link } from 'react-router-dom';

const SupportDashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [showNewTicketForm, setShowNewTicketForm] = useState(false);
  const [subject, setSubject] = useState('');
  const [queryText, setQueryText] = useState('');

  const { data: tickets, isLoading } = useQuery({
    queryKey: ['support-tickets'],
    queryFn: async () => {
      return apiClient('/api/v1/support/tickets/');
    },
  });

  const createTicketMutation = useMutation({
    mutationFn: async (newTicket: { subject: string; query: string }) => {
      return apiClient('/api/v1/support/tickets/', {
        method: 'POST',
        body: JSON.stringify(newTicket),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] });
      setShowNewTicketForm(false);
      setSubject('');
      setQueryText('');
    },
  });

  const rateTicketMutation = useMutation({
    mutationFn: async ({ id, score }: { id: number; score: number }) => {
      return apiClient(`/api/v1/support/tickets/${id}/rate/`, {
        method: 'PATCH',
        body: JSON.stringify({ score }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] });
    },
  });

  const selectedTicket = tickets?.find((t: any) => t.id === selectedTicketId);

  return (
    <AnimatedPage>
      <div className="max-w-6xl mx-auto p-6 space-y-8 pt-24 pb-32">
        <Link to="/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-4 no-underline group">
            <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Lobby
        </Link>
        
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-blue-500/20 pb-8 gap-6">
          <div>
            <h1 className="text-4xl md:text-5xl font-black italic manga-font text-blue-500 flex items-center gap-4">
              <Zap className="w-10 h-10 text-glow" /> NEXUS SUPPORT
            </h1>
            <p className="text-xs uppercase tracking-widest opacity-40 font-bold mt-2">Protocole de Diagnostic & Résolution IA</p>
          </div>
          <Button onClick={() => setShowNewTicketForm(true)} className="bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-500/20 py-4 px-8 font-black uppercase italic tracking-widest">
            <Plus className="w-4 h-4 mr-2" /> Ouvrir un Portail
          </Button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Sidebar: Ticket List */}
          <aside className="space-y-6">
            <h2 className="text-[10px] font-black uppercase opacity-60 px-2 tracking-[0.3em]">Signaux Actifs</h2>
            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : tickets?.length === 0 ? (
                <p className="text-xs opacity-30 italic px-2 font-bold uppercase">Aucun signal détecté.</p>
              ) : (
                tickets?.map((ticket: any) => (
                  <Card 
                    key={ticket.id} 
                    padding="md" 
                    className={`cursor-pointer transition-all border-2 ${selectedTicketId === ticket.id ? 'border-blue-500 bg-blue-500/10' : 'border-white/5 bg-white/5 hover:border-white/20'}`}
                    onClick={() => {
                        setSelectedTicketId(ticket.id);
                        setShowNewTicketForm(false);
                    }}
                  >
                    <div className="flex justify-between items-start mb-2 gap-4">
                      <h3 className="font-black text-xs uppercase italic truncate flex-1">{ticket.subject}</h3>
                      <span className={`text-[8px] px-2 py-0.5 rounded-full font-black uppercase shrink-0 ${ticket.status === 'resolved' ? 'bg-green-500/20 text-green-500 border border-green-500/30' : ticket.status === 'closed' ? 'bg-gray-500/20 text-gray-400 border border-gray-500/30' : 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'}`}>
                        {ticket.status}
                      </span>
                    </div>
                    <p className="text-[10px] opacity-40 uppercase font-bold font-mono">{new Date(ticket.created_at).toLocaleString()}</p>
                  </Card>
                ))
              )}
            </div>
          </aside>

          {/* Main: Ticket Detail or New Form */}
          <main className="lg:col-span-2">
            {showNewTicketForm ? (
              <Card padding="lg" className="border-blue-500/30 bg-blue-500/5 shadow-2xl shadow-blue-500/10">
                <h2 className="manga-font text-2xl mb-8 uppercase italic italic text-white font-black">Initialiser Nouveau Diagnostic</h2>
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1">Sujet de la transmission</label>
                    <input 
                        type="text" 
                        placeholder="EX: PROBLÈME DE SYNCHRONISATION..." 
                        className="w-full bg-black/40 border border-white/10 p-4 rounded-xl focus:border-blue-500 outline-none text-sm font-bold uppercase tracking-tight transition-all text-white"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1">Données de la requête</label>
                    <textarea 
                        placeholder="DÉCRIVEZ VOTRE SITUATION ICI..." 
                        rows={8}
                        className="w-full bg-black/40 border border-white/10 p-4 rounded-xl focus:border-blue-500 outline-none text-sm font-bold tracking-tight transition-all text-white"
                        value={queryText}
                        onChange={(e) => setQueryText(e.target.value)}
                    />
                  </div>
                  <div className="flex flex-col sm:flex-row gap-4 pt-4">
                    <Button 
                        size="lg"
                        className="flex-1 font-black uppercase italic tracking-widest py-6"
                        onClick={() => createTicketMutation.mutate({ subject, query: queryText })} 
                        disabled={createTicketMutation.isPending || !subject || !queryText}
                    >
                      {createTicketMutation.isPending ? 'Transmission...' : 'Envoyer Signal'}
                    </Button>
                    <Button 
                        variant="outline" 
                        size="lg"
                        className="sm:w-1/3 font-black uppercase italic tracking-widest py-6"
                        onClick={() => setShowNewTicketForm(false)}
                    >
                        Annuler
                    </Button>
                  </div>
                </div>
              </Card>
            ) : selectedTicket ? (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <Card padding="lg" className="border-white/10 bg-white/5">
                  <h2 className="text-[10px] uppercase font-black opacity-40 mb-4 tracking-widest flex items-center gap-2">
                    <HelpCircle className="w-3 h-3" /> Requête Originale
                  </h2>
                  <h3 className="text-xl font-black uppercase italic mb-4">{selectedTicket.subject}</h3>
                  <p className="text-gray-300 font-medium leading-relaxed">{selectedTicket.query}</p>
                </Card>

                {selectedTicket.ai_response && (
                  <Card padding="lg" className="border-cyan-500/30 bg-cyan-500/5 relative overflow-hidden shadow-2xl shadow-cyan-500/5">
                    <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                      <Brain className="w-32 h-32 text-cyan-500" />
                    </div>
                    <h2 className="text-[10px] uppercase font-black text-cyan-400 mb-6 flex items-center gap-2 tracking-widest">
                      <Brain className="w-4 h-4" /> Réponse du Protocole Cyber
                    </h2>
                    <div className="prose prose-invert max-w-none">
                      <p className="text-gray-200 leading-relaxed font-semibold text-lg italic">{selectedTicket.ai_response}</p>
                    </div>
                    
                    <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-6">
                      <span className="text-[10px] font-black uppercase opacity-60 tracking-widest text-center sm:text-left">
                        {selectedTicket.feedback_score !== null 
                            ? "Retour enregistré. Merci." 
                            : "Ce diagnostic vous a-t-il aidé ?"}
                      </span>
                      {selectedTicket.feedback_score === null && (
                        <div className="flex gap-4">
                            <button 
                            onClick={() => rateTicketMutation.mutate({ id: selectedTicket.id, score: 1 })}
                            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-green-500/10 text-green-500 border border-green-500/20 hover:bg-green-500 hover:text-black transition-all font-black uppercase text-[10px] tracking-widest"
                            >
                            <ThumbsUp className="w-4 h-4" /> Utile
                            </button>
                            <button 
                            onClick={() => rateTicketMutation.mutate({ id: selectedTicket.id, score: 0 })}
                            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-black transition-all font-black uppercase text-[10px] tracking-widest"
                            >
                            <ThumbsDown className="w-4 h-4" /> Inutile
                            </button>
                        </div>
                      )}
                      {selectedTicket.feedback_score !== null && (
                        <div className={`flex items-center gap-2 px-6 py-3 rounded-xl font-black uppercase text-[10px] tracking-widest ${selectedTicket.feedback_score === 1 ? 'text-green-500' : 'text-red-500'}`}>
                            {selectedTicket.feedback_score === 1 ? <ThumbsUp className="w-4 h-4" /> : <ThumbsDown className="w-4 h-4" />}
                            SIGNAL {selectedTicket.feedback_score === 1 ? 'POSITIF' : 'NÉGATIF'} ENREGISTRÉ
                        </div>
                      )}
                    </div>
                  </Card>
                )}
              </div>
            ) : (
              <div className="h-[400px] flex flex-col items-center justify-center opacity-20 border-2 border-dashed border-white/10 rounded-3xl">
                <HelpCircle className="w-20 h-20 mb-6" />
                <p className="font-black italic uppercase tracking-[0.4em] text-center text-white">Sélectionnez un signal pour débuter le diagnostic</p>
              </div>
            )}
          </main>
        </div>
      </div>
      <style>{`
        .manga-font {
          font-family: 'Space Grotesk', sans-serif;
          letter-spacing: -0.05em;
        }
        .text-glow {
          text-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.02);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.3);
          border-radius: 10px;
        }
      `}</style>
    </AnimatedPage>
  );
};

export default SupportDashboardPage;
