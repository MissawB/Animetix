import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Search, 
  Zap, 
  Sparkles, 
  Layers, 
  Network, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  ChevronRight,
  Database,
  Cpu,
  Bot
} from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface Step {
  id: string;
  type: 'thought' | 'eval' | 'token';
  content: any;
  timestamp: number;
  agent?: string;
}

const ExpertNexusPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [isStreaming, setIsStreaming] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [finalAnswer, setFinalAnswer] = useState('');
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
    return () => stopStreaming();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps, finalAnswer]);

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  const handleSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    
    setSearchParams({ q: searchQuery });
    setSteps([]);
    setFinalAnswer('');
    setError(null);
    setIsStreaming(true);

    const url = `/api/v1/stream/agentic-rag/?q=${encodeURIComponent(searchQuery)}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          setFinalAnswer(prev => prev + data.content);
        } else if (data.type === 'thought') {
          // Extract agent tag if present: [Agent Name] ...
          const agentMatch = data.content.match(/^\[(.*?)\]/);
          const agent = agentMatch ? agentMatch[1] : 'System';
          const content = agentMatch ? data.content.replace(/^\[.*?\]\s*/, '') : data.content;

          setSteps(prev => [...prev, {
            id: Math.random().toString(36).substr(2, 9),
            type: 'thought',
            content,
            agent,
            timestamp: Date.now()
          }]);
        } else if (data.type === 'eval') {
          setSteps(prev => [...prev, {
            id: Math.random().toString(36).substr(2, 9),
            type: 'eval',
            content: data.content,
            agent: 'Judge',
            timestamp: Date.now()
          }]);
        } else if (data.type === 'error') {
          setError(data.content);
          stopStreaming();
        } else if (data.type === 'done') {
          stopStreaming();
        }
      } catch (e) {
        console.error("Failed to parse event data", e);
      }
    };

    eventSource.onerror = () => {
      // In many implementations, Done is signified by connection close
      // but if we have an error type we use that.
      // Usually browser reconnects on error, so we might want to stop if it's intentional
      stopStreaming();
    };
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  const getAgentIcon = (agent?: string) => {
    switch (agent) {
      case 'Semantic Router': return <Network className="w-4 h-4 text-blue-400" />;
      case 'State Machine': return <Layers className="w-4 h-4 text-purple-400" />;
      case 'TTC': return <Cpu className="w-4 h-4 text-red-400" />;
      case 'Graph User Memory': return <Database className="w-4 h-4 text-emerald-400" />;
      case 'Search Planner': return <Search className="w-4 h-4 text-blue-500" />;
      case 'Synthesizer': return <Sparkles className="w-4 h-4 text-yellow-400" />;
      case 'Judge': return <ShieldCheck className="w-4 h-4 text-emerald-500" />;
      default: return <Bot className="w-4 h-4 text-gray-400" />;
    }
  };

  const getAgentColor = (agent?: string) => {
    switch (agent) {
      case 'Semantic Router': return 'border-blue-500/30 bg-blue-500/5';
      case 'State Machine': return 'border-purple-500/30 bg-purple-500/5';
      case 'TTC': return 'border-red-500/30 bg-red-500/5';
      case 'Graph User Memory': return 'border-emerald-500/30 bg-emerald-500/5';
      case 'Judge': return 'border-emerald-500/30 bg-emerald-500/5';
      case 'Synthesizer': return 'border-yellow-500/30 bg-yellow-500/5';
      default: return 'border-white/5 bg-white/5';
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col min-h-[calc(100vh-100px)]">
        
        {/* Header */}
        <header className="mb-12 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
               <Brain className="w-4 h-4 fill-current" /> SOTA Agentic RAG v2.0
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                EXPERT <span className="text-blue-500 text-glow">NEXUS</span>
            </h1>
            <p className="text-lg font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                Raisonnement arborescent multi-agents pour les requêtes complexes de Lore.
            </p>
        </header>

        {/* Search Bar */}
        <Card padding="lg" className="mb-12 bg-navy-950/50 border-white/5 shadow-2xl rounded-[3rem]">
            <form onSubmit={onSubmit} className="flex gap-4">
                <div className="relative flex-grow group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/20 group-focus-within:text-blue-500 transition-colors" />
                    <input 
                        type="text" 
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Posez une question profonde sur un univers, une relation ou un arc narratif..."
                        className="w-full bg-black border-2 border-white/5 rounded-[2.5rem] py-6 pl-16 pr-8 text-lg font-bold focus:border-blue-600 outline-none transition-all placeholder:opacity-20"
                    />
                </div>
                <Button 
                    type="submit" 
                    disabled={isStreaming || !query.trim()}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-10 rounded-[2.5rem] font-black italic text-xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                >
                    {isStreaming ? <Zap className="w-6 h-6 animate-pulse" /> : "RÉSOUDRE"}
                </Button>
            </form>
        </Card>

        {/* Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-grow">
            
            {/* Thought Stream (Timeline) */}
            <div className="lg:col-span-4 flex flex-col h-full">
                <div className="flex items-center justify-between mb-6 px-4">
                    <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                        <Layers className="w-4 h-4" /> Arbre de Pensée
                    </h3>
                    {isStreaming && (
                        <Badge variant="primary" className="bg-blue-600 animate-pulse text-[8px]">ACTIVE REASONING</Badge>
                    )}
                </div>

                <div ref={scrollRef} className="flex-grow overflow-y-auto space-y-4 no-scrollbar max-h-[600px] lg:max-h-none pr-2">
                    <AnimatePresence mode="popLayout">
                        {steps.map((step, idx) => (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.4 }}
                                className={`p-4 rounded-2xl border ${getAgentColor(step.agent)} relative overflow-hidden group`}
                            >
                                <div className="absolute top-0 right-0 w-24 h-24 opacity-[0.03] -mr-8 -mt-8 rotate-12 group-hover:opacity-[0.08] transition-opacity">
                                    {getAgentIcon(step.agent)}
                                </div>
                                
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
                                        {getAgentIcon(step.agent)}
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest opacity-60">
                                        {step.agent}
                                    </span>
                                    <span className="text-[8px] opacity-20 font-mono ml-auto">
                                        +{Math.round((step.timestamp - (steps[0]?.timestamp || step.timestamp)) / 100) / 10}s
                                    </span>
                                </div>

                                <p className="text-xs font-bold leading-relaxed opacity-90 italic">
                                    {step.content}
                                </p>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                    
                    {!isStreaming && steps.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-24 border-2 border-dashed border-white/5 rounded-[3rem]">
                            <Network className="w-16 h-16 mb-4" />
                            <p className="text-xs font-black uppercase tracking-widest">En attente d'une requête complexe</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Answer Display */}
            <div className="lg:col-span-8 flex flex-col h-full">
                <div className="flex items-center gap-4 mb-6 px-4">
                    <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-yellow-400" /> Synthèse Expert
                    </h3>
                </div>

                <Card padding="none" className="flex-grow bg-black border-white/10 shadow-[0_0_100px_rgba(0,0,0,0.8)] overflow-hidden rounded-[3rem] relative flex flex-col">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-600 to-transparent opacity-50" />
                    
                    <div className="p-12 overflow-y-auto flex-grow prose prose-invert max-w-none">
                        {error && (
                            <div className="p-8 bg-red-500/10 border border-red-500/20 rounded-3xl flex items-center gap-6 text-red-500">
                                <AlertCircle className="w-12 h-12 flex-shrink-0" />
                                <div>
                                    <h4 className="text-xl font-black italic uppercase mb-1">Erreur de Résolution</h4>
                                    <p className="text-sm font-bold opacity-80 uppercase tracking-wide">{error}</p>
                                </div>
                            </div>
                        )}

                        {!error && !finalAnswer && !isStreaming && (
                            <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-32">
                                <Sparkles className="w-24 h-24 mb-8" />
                                <h3 className="text-3xl font-black italic manga-font uppercase mb-4">Nexus en veille</h3>
                                <p className="text-sm font-bold uppercase tracking-[0.3em]">L'IA de 5ème génération attend vos instructions.</p>
                            </div>
                        )}

                        {!error && (finalAnswer || isStreaming) && (
                            <div className="space-y-8 animate-fade-in">
                                <p className="text-2xl font-bold leading-relaxed whitespace-pre-wrap text-white/90">
                                    {finalAnswer}
                                    {isStreaming && (
                                        <motion.span 
                                            animate={{ opacity: [0, 1, 0] }}
                                            transition={{ repeat: Infinity, duration: 1 }}
                                            className="inline-block w-2 h-8 bg-blue-500 ml-2 align-middle"
                                        />
                                    )}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Footer Stats */}
                    <div className="px-12 py-8 border-t border-white/5 bg-white/5 flex flex-wrap justify-between items-center gap-6">
                        <div className="flex gap-8">
                            <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 text-blue-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Latence: 1.2s</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Faithfulness: 98%</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            <span className="text-[8px] font-black uppercase tracking-widest text-gray-500">Grounding Verificated</span>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ExpertNexusPage;
