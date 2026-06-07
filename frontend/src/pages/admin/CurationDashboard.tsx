import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, AlertCircle, CheckCircle2, XCircle, Database, LayoutGrid, Clock, ChevronRight } from 'lucide-react';

const CurationDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedTicket, setSelectedTicket] = React.useState<any>(null);

  const { data: tickets, isLoading } = useQuery({
    queryKey: ['admin', 'curation', 'tickets'],
    queryFn: async () => {
      const res = await fetch('/api/v1/curation/');
      return res.json();
    }
  });

  const { data: stats } = useQuery({
    queryKey: ['admin', 'curation', 'stats'],
    queryFn: async () => {
      const res = await fetch('/api/v1/curation/stats/');
      return res.json();
    }
  });

  const resolveMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/v1/curation/${id}/resolve/`, { method: 'POST' });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'curation'] });
      setSelectedTicket(null);
    }
  });

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12 text-white">
        <header className="flex justify-between items-end mb-12">
            <div>
                <div className="flex items-center gap-2 text-cyan-500 font-black uppercase tracking-widest text-xs mb-2">
                    <ShieldCheck size={16} /> Admin Access Restricted
                </div>
                <h1 className="text-5xl font-black italic uppercase tracking-tighter">Data <span className="text-cyan-500">Curation</span></h1>
            </div>

            <div className="flex gap-6">
                <div className="text-right">
                    <div className="text-gray-500 text-[10px] font-black uppercase tracking-widest">Health Score</div>
                    <div className="text-2xl font-black text-green-500 italic">{stats?.health_score || 0}%</div>
                </div>
                <div className="text-right">
                    <div className="text-gray-500 text-[10px] font-black uppercase tracking-widest">Pending Tickets</div>
                    <div className="text-2xl font-black text-yellow-500 italic">{stats?.pending_tickets || 0}</div>
                </div>
            </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Tickets List */}
            <div className="lg:col-span-1 space-y-4">
                <h3 className="text-sm font-black uppercase tracking-widest text-gray-500 mb-6 flex items-center gap-2">
                    <Clock size={14} /> Inbox Flux
                </h3>
                <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2 no-scrollbar">
                    {tickets?.results?.map((ticket: any) => (
                        <motion.button
                            whileHover={{ x: 5 }}
                            key={ticket.id}
                            onClick={() => setSelectedTicket(ticket)}
                            className={`w-full text-left p-5 rounded-2xl border transition-all ${
                                selectedTicket?.id === ticket.id 
                                ? 'bg-cyan-500/10 border-cyan-500/50' 
                                : 'bg-gray-900/40 border-white/5 hover:border-white/10'
                            }`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${ticket.is_resolved ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
                                    {ticket.is_resolved ? 'Resolved' : 'Pending'}
                                </span>
                                <span className="text-gray-600 text-[10px] font-mono">#{ticket.id}</span>
                            </div>
                            <h4 className="font-black italic uppercase text-sm truncate">{ticket.item_title}</h4>
                            <p className="text-gray-500 text-xs line-clamp-1 mt-1 font-medium">{ticket.issue_description}</p>
                        </motion.button>
                    ))}
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
                            className="bg-gray-900/50 backdrop-blur-xl rounded-3xl border border-white/5 overflow-hidden"
                        >
                            <div className="p-8 border-b border-white/5 bg-gradient-to-r from-cyan-950/20 to-transparent flex justify-between items-center">
                                <div>
                                    <h2 className="text-3xl font-black italic uppercase tracking-tighter">{selectedTicket.item_title}</h2>
                                    <div className="text-gray-500 text-xs font-bold uppercase tracking-widest mt-1">
                                        Detected on {new Date(selectedTicket.created_at).toLocaleString()}
                                    </div>
                                </div>
                                {!selectedTicket.is_resolved && (
                                    <button 
                                        onClick={() => resolveMutation.mutate(selectedTicket.id)}
                                        disabled={resolveMutation.isPending}
                                        className="bg-green-600 hover:bg-green-500 px-6 py-3 rounded-xl font-black italic uppercase tracking-widest flex items-center gap-2 transition-all hover:scale-105"
                                    >
                                        <CheckCircle2 size={18} /> Approve Fix
                                    </button>
                                )}
                            </div>

                            <div className="p-8 space-y-8">
                                <section>
                                    <h4 className="text-xs font-black uppercase tracking-widest text-cyan-500 mb-4 flex items-center gap-2">
                                        <AlertCircle size={14} /> Contradiction Report
                                    </h4>
                                    <div className="bg-black/40 p-6 rounded-2xl text-gray-300 italic leading-relaxed border-l-4 border-cyan-600">
                                        "{selectedTicket.issue_description}"
                                    </div>
                                </section>

                                <div className="grid grid-cols-2 gap-8">
                                    <section>
                                        <h4 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-4 flex items-center gap-2">
                                            <Database size={14} /> PostgreSQL Source
                                        </h4>
                                        <pre className="bg-black p-4 rounded-xl text-[10px] font-mono text-gray-400 overflow-x-auto max-h-60">
                                            {JSON.stringify(selectedTicket.source_pg, null, 2)}
                                        </pre>
                                    </section>
                                    <section>
                                        <h4 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-4 flex items-center gap-2">
                                            <LayoutGrid size={14} /> Neo4j Source
                                        </h4>
                                        <pre className="bg-black p-4 rounded-xl text-[10px] font-mono text-gray-400 overflow-x-auto max-h-60">
                                            {JSON.stringify(selectedTicket.source_neo4j, null, 2)}
                                        </pre>
                                    </section>
                                </div>
                            </div>
                        </motion.div>
                    ) : (
                        <div className="h-full min-h-[400px] border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center text-center p-12">
                            <Database size={48} className="text-gray-800 mb-4" />
                            <h3 className="text-xl font-black italic uppercase text-gray-700">Select a ticket to inspect</h3>
                            <p className="text-gray-600 text-sm max-w-xs mx-auto mt-2">
                                Autonomous IA healers generate these tickets when they find structural drift in our knowledge graph.
                            </p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default CurationDashboard;

