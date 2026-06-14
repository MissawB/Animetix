import React, { useState } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Search, 
  Filter, 
  Clock, 
  User, 
  AlertTriangle, 
  ChevronRight, 
  Info,
  Lock,
  Eye,
  RefreshCw,
  Database
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

interface AISafetyEvent {
  id: number;
  event_type: 'input' | 'output' | 'system';
  action: 'block' | 'warn' | 'rewrite' | 'none';
  detected_categories: string[];
  input_text: string | null;
  output_text: string | null;
  reasoning: string | null;
  username: string | null;
  created_at: string;
}

const AISafetyAuditPage: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<AISafetyEvent | null>(null);

  const { data: events, isLoading, refetch } = useQuery<AISafetyEvent[]>({
    queryKey: ['safety-events'],
    queryFn: () => apiClient('/api/v1/mlops/safety/events/'),
  });

  const getActionColor = (action: string) => {
    switch (action) {
      case 'block': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'warn': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      case 'rewrite': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      default: return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#fafafa] dark:bg-[#0a0a0f] text-black dark:text-white pt-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          
          {/* Header */}
          <header className="mb-12 flex justify-between items-end">
              <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-[10px] font-black uppercase tracking-widest text-red-500 mb-4">
                      <Lock className="w-3 h-3" /> Compliance & Trust Hub
                  </div>
                  <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-2">
                      SAFETY <span className="text-red-500 text-glow">AUDIT</span>
                  </h1>
                  <p className="text-lg font-bold opacity-30 uppercase tracking-[0.3em]">Surveillance des Guardrails et Détection de Menaces.</p>
              </div>
              <Button 
                onClick={() => refetch()} 
                variant="outline" 
                className="border-black/10 dark:border-white/10 text-xs font-black uppercase tracking-widest"
              >
                <RefreshCw className="w-3 h-3 mr-2" /> Sync Logs
              </Button>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Events List */}
              <div className="lg:col-span-7 space-y-4">
                  <Card padding="none" className="bg-white dark:bg-navy-950/40 border-black/5 dark:border-white/5 rounded-[2.5rem] overflow-hidden shadow-xl">
                      <header className="px-8 py-6 border-b border-black/5 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-white/[0.02]">
                          <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40">
                              <ShieldAlert className="w-4 h-4" /> Live Safety Stream
                          </h3>
                          <div className="flex gap-2">
                              <Badge variant="neutral" className="bg-black/5 dark:bg-white/5 border-none text-[8px] italic">REAL_TIME_FILTERING</Badge>
                          </div>
                      </header>
                      
                      <div className="max-h-[700px] overflow-y-auto custom-scrollbar">
                          {isLoading ? (
                              <div className="py-20 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto opacity-20" /></div>
                          ) : events && events.length > 0 ? (
                              events.map((event) => (
                                  <div 
                                      key={event.id}
                                      onClick={() => setSelectedEvent(event)}
                                      className={`p-8 border-b border-black/5 dark:border-white/5 transition-all cursor-pointer group flex items-start gap-6 ${selectedEvent?.id === event.id ? 'bg-red-500/[0.03] dark:bg-red-500/[0.05]' : 'hover:bg-gray-50 dark:hover:bg-white/[0.02]'}`}
                                  >
                                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 border ${getActionColor(event.action)} shadow-lg shadow-current/10`}>
                                          {event.action === 'block' ? <AlertTriangle className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
                                      </div>
                                      
                                      <div className="flex-grow min-w-0">
                                          <div className="flex justify-between items-center mb-2">
                                              <div className="flex items-center gap-3">
                                                  <span className="text-[10px] font-black uppercase tracking-widest opacity-30">{new Date(event.created_at).toLocaleTimeString()}</span>
                                                  <Badge variant="neutral" className="bg-black/5 dark:bg-white/10 text-black dark:text-white border-none text-[8px] font-black uppercase tracking-widest">{event.event_type}</Badge>
                                              </div>
                                              <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest font-mono">#{event.id}</span>
                                          </div>
                                          <p className="text-sm font-bold text-black dark:text-white/80 line-clamp-1 mb-2 italic">
                                              "{event.input_text || event.output_text || 'System event'}"
                                          </p>
                                          <div className="flex flex-wrap gap-2">
                                              {event.detected_categories.map((cat, idx) => (
                                                  <span key={idx} className="text-[8px] font-black uppercase tracking-tighter text-red-500/60">{cat}</span>
                                              ))}
                                          </div>
                                      </div>
                                      
                                      <div className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                                          <ChevronRight className="w-4 h-4 opacity-20" />
                                      </div>
                                  </div>
                              ))
                          ) : (
                              <div className="py-32 text-center opacity-20">
                                  <ShieldCheck className="w-16 h-16 mx-auto mb-6" />
                                  <p className="text-xs font-black uppercase tracking-[0.3em]">No safety violations detected</p>
                              </div>
                          )}
                      </div>
                  </Card>
              </div>

              {/* Event Detail View */}
              <div className="lg:col-span-5">
                  <AnimatePresence mode="wait">
                      {selectedEvent ? (
                          <motion.div
                              key={selectedEvent.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                              className="sticky top-32 space-y-8"
                          >
                              <Card padding="lg" className="bg-white dark:bg-navy-950 border-2 border-red-500/20 rounded-[3rem] shadow-2xl relative overflow-hidden">
                                  <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none">
                                      <ShieldAlert className="w-48 h-48 text-red-500" />
                                  </div>

                                  <header className="mb-10 flex justify-between items-start">
                                      <div>
                                          <Badge className={`${getActionColor(selectedEvent.action)} border-none uppercase font-black italic px-4 py-1.5 mb-4`}>
                                              Action: {selectedEvent.action.toUpperCase()}
                                          </Badge>
                                          <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter text-black dark:text-white">Detailed Report</h2>
                                      </div>
                                      <button onClick={() => setSelectedEvent(null)} className="p-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl transition-all text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white" aria-label="Fermer le rapport">
                                          <Eye className="w-5 h-5 rotate-180" />
                                      </button>
                                  </header>

                                  <div className="space-y-8 relative z-10">
                                      {/* User Context */}
                                      <section className="p-6 bg-gray-50 dark:bg-white/[0.03] rounded-3xl border border-black/5 dark:border-white/5">
                                          <h4 className="text-[10px] font-black uppercase tracking-widest opacity-30 mb-4 flex items-center gap-2">
                                              <User className="w-3 h-3" /> Subject Identity
                                          </h4>
                                          <div className="flex items-center gap-3">
                                              <div className="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center text-[10px] font-black text-red-500">
                                                  {selectedEvent.username?.charAt(0) || 'G'}
                                              </div>
                                              <span className="text-sm font-bold uppercase tracking-wider text-black dark:text-white/80">{selectedEvent.username || 'Guest / Anonymous'}</span>
                                          </div>
                                      </section>

                                      {/* Text Analysis */}
                                      <section className="space-y-4">
                                          <h4 className="text-[10px] font-black uppercase tracking-widest opacity-30 flex items-center gap-2">
                                              <Info className="w-3 h-3" /> Captured Payload
                                          </h4>
                                          <div className="p-6 bg-black dark:bg-black/40 rounded-3xl border border-white/5 font-mono text-xs text-white/90 leading-relaxed max-h-[200px] overflow-y-auto custom-scrollbar italic">
                                              "{selectedEvent.input_text || selectedEvent.output_text}"
                                          </div>
                                      </section>

                                      {/* Security Reasoning */}
                                      <section className="space-y-4">
                                          <h4 className="text-[10px] font-black uppercase tracking-widest text-red-500 flex items-center gap-2">
                                              <Database className="w-3 h-3" /> Guardrail Reasoning
                                          </h4>
                                          <div className="p-6 bg-red-500/[0.03] dark:bg-red-500/[0.07] rounded-3xl border border-red-500/10 text-sm font-medium text-black dark:text-white/60 leading-relaxed italic">
                                              {selectedEvent.reasoning || "No detailed reasoning provided by the safety engine."}
                                          </div>
                                      </section>
                                  </div>
                              </Card>
                          </motion.div>
                      ) : (
                          <div className="h-[600px] flex flex-col items-center justify-center opacity-10 text-center border-4 border-dashed border-black/5 dark:border-white/5 rounded-[4rem]">
                              <ShieldCheck className="w-24 h-24 mb-8" />
                              <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Awaiting Selection</h3>
                              <p className="text-sm font-bold uppercase tracking-[0.3em]">Select an event to initiate deep audit.</p>
                          </div>
                      )}
                  </AnimatePresence>
              </div>
          </div>

          {/* Stats Bar */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                  { label: 'Blocked Attacks', value: events?.filter(e => e.action === 'block').length || 0, color: 'text-red-500' },
                  { label: 'Guardrail Warnings', value: events?.filter(e => e.action === 'warn').length || 0, color: 'text-amber-500' },
                  { label: 'Auto-Rewrites', value: events?.filter(e => e.action === 'rewrite').length || 0, color: 'text-blue-500' },
                  { label: 'Safe Interactions', value: events?.filter(e => e.action === 'none').length || 0, color: 'text-emerald-500' }
              ].map((stat, i) => (
                  <Card key={i} padding="md" className="bg-white dark:bg-navy-950 border-none shadow-lg">
                      <p className="text-[8px] font-black uppercase opacity-30 tracking-[0.2em] mb-1">{stat.label}</p>
                      <p className={`text-4xl font-black italic manga-font ${stat.color}`}>{stat.value}</p>
                  </Card>
              ))}
          </div>

        </div>
      </AnimatedPage>
    </div>
  );
};

export default AISafetyAuditPage;
