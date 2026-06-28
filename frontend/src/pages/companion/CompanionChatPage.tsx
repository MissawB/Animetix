import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Trash2,
  Sparkles,
  MessageSquare,
  Users,
  Bot
} from 'lucide-react';
import { useCompanionStore } from "../../features/companion/companionStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { AnimatedPage } from "../../components/ui/AnimatedPage";


const CompanionChatPage: React.FC = () => {
  const [input, setInput] = useState('');
  const { history, isLoading, sendMessage, activeMentor, setMentor, clearHistory, customPersona, setCustomPersona } = useCompanionStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
        sendMessage(input.trim());
        setInput('');
    }
  };

  const MENTORS = [
    { id: 'sensei', name: 'Sensei', desc: 'Sagesse et guidance technique.' },
    { id: 'tsundere', name: 'Tsundere-chan', desc: 'Émotionnelle et protectrice.' },
    { id: 'kuudere', name: 'Kuudere-san', desc: 'Calme et analyse logique.' },
    { id: 'senpai', name: 'Senpai', desc: 'Encourageant et un peu taquin.' },
    { id: 'rival', name: 'Rival', desc: 'Compétitif, te pousse à fond.' },
    { id: 'genki', name: 'Genki', desc: 'Énergie et optimisme débordants.' },
    { id: 'ojou', name: 'Ojou-sama', desc: 'Raffinée et un brin hautaine.' },
    { id: 'strategist', name: 'Stratège', desc: 'Analytique et calculateur.' },
    { id: 'custom', name: 'Personnalisé', desc: 'Définis ta propre personnalité.' },
  ];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col h-[calc(100vh-120px)]">
        
        <header className="mb-8 flex flex-col md:flex-row justify-between items-end gap-6">
            <div>
                <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2">
                    NEXUS <span className="text-blue-500 text-glow">COMPANION</span>
                </h1>
            </div>
            
            <div className="flex gap-4">
                <Button onClick={clearHistory} variant="outline" className="border-white/5 bg-white/5 hover:bg-red-500/10 hover:text-red-500 transition-all px-6 rounded-2xl">
                    <Trash2 className="w-4 h-4" /> REBOOT MÉMOIRE
                </Button>
            </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-grow min-h-0">
            
            {/* Sidebar: Mentor Selection */}
            <div className="lg:col-span-3 space-y-6 overflow-y-auto no-scrollbar pb-6">
                <Card padding="lg" className="bg-navy-900/40 border-white/5">
                    <h3 className="text-[10px] font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Users className="w-3 h-3" /> Sélection du Mentor
                    </h3>
                    <div className="space-y-3">
                        {MENTORS.map((m) => (
                            <button
                                key={m.id}
                                onClick={() => setMentor(m.id)}
                                className={`w-full p-4 rounded-2xl text-left transition-all border-2 group ${
                                    activeMentor === m.id 
                                    ? 'bg-white border-white text-black scale-105 shadow-2xl' 
                                    : 'bg-white/5 border-white/5 text-white/40 hover:bg-white/10'
                                }`}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-black italic uppercase text-xs manga-font tracking-tight">{m.name}</span>
                                    <div className={`w-2 h-2 rounded-full ${m.id === activeMentor ? 'bg-blue-500 animate-pulse' : 'bg-white/10'}`} />
                                </div>
                                <p className="text-[9px] font-bold opacity-60 leading-tight uppercase">{m.desc}</p>
                            </button>
                        ))}
                    </div>
                </Card>

                {activeMentor === 'custom' && (
                    <Card padding="lg" className="bg-navy-900/40 border-white/5">
                        <h3 className="text-[10px] font-black uppercase opacity-40 mb-3 tracking-widest flex items-center gap-2">
                            <Sparkles className="w-3 h-3" /> Personnalité
                        </h3>
                        <textarea
                            value={customPersona}
                            onChange={(e) => setCustomPersona(e.target.value)}
                            maxLength={600}
                            rows={5}
                            placeholder="Ex: Tu es un pirate jovial qui parle en métaphores marines et adore les défis."
                            aria-label="Personnalité du compagnon"
                            className="w-full p-3 rounded-2xl bg-black/40 border-2 border-white/5 focus:border-blue-500 outline-none text-xs font-medium leading-relaxed text-white placeholder-white/20 resize-none transition-all"
                        />
                        <p className="text-[9px] font-bold opacity-30 uppercase tracking-widest mt-2 text-right">{customPersona.length}/600</p>
                    </Card>
                )}
            </div>

            {/* Chat Area */}
            <div className="lg:col-span-9 flex flex-col h-full gap-6">
                <Card padding="none" className="flex-grow flex flex-col bg-black border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden rounded-[3rem]">
                    
                    {/* Chat Header */}
                    <div className="px-8 py-6 border-b border-white/5 bg-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-2xl bg-blue-500 flex items-center justify-center shadow-lg">
                                <Bot className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <span className="font-black italic uppercase text-sm">{activeMentor.toUpperCase()} HUB</span>
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div ref={scrollRef} className="flex-grow overflow-y-auto p-8 space-y-8 scroll-smooth no-scrollbar">
                        {history.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center opacity-10 text-center px-12">
                                <MessageSquare className="w-32 h-32 mb-6" />
                                <h3 className="text-2xl font-black italic manga-font uppercase mb-2">Nexus Ouvert</h3>
                                <p className="text-sm font-bold uppercase tracking-[0.2em]">Initialisez la communication avec votre compagnon.</p>
                            </div>
                        )}
                        
                        {history.map((msg, i) => (
                            <div 
                                key={i} 
                                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                            >
                                <div className={`max-w-[80%] flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <div className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center font-black italic text-[10px] ${
                                        msg.role === 'user' ? 'bg-white text-black' : 'bg-blue-600 text-white shadow-lg'
                                    }`}>
                                        {msg.role === 'user' ? 'ME' : 'AI'}
                                    </div>
                                    <div className={`p-6 rounded-[2rem] text-sm leading-relaxed ${
                                        msg.role === 'user' 
                                        ? 'bg-white/5 border border-white/10 text-white/90 rounded-tr-none' 
                                        : 'bg-navy-900 border border-blue-500/20 text-blue-50 rounded-tl-none italic font-medium'
                                    }`}>
                                        {msg.content}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex justify-start animate-pulse">
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center">
                                        <Loader2 className="w-4 h-4 animate-spin opacity-20" />
                                    </div>
                                    <div className="p-6 bg-white/5 rounded-[2rem] rounded-tl-none">
                                        <div className="flex gap-2">
                                            <div className="w-2 h-2 bg-blue-500/40 rounded-full animate-bounce" />
                                            <div className="w-2 h-2 bg-blue-500/40 rounded-full animate-bounce [animation-delay:0.2s]" />
                                            <div className="w-2 h-2 bg-blue-500/40 rounded-full animate-bounce [animation-delay:0.4s]" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="p-8 bg-white/5 border-t border-white/5">
                        <form onSubmit={handleSend} className="relative flex items-center gap-4">
                            <div className="relative flex-grow group">
                                <div className="absolute left-6 top-1/2 -translate-y-1/2">
                                    <Sparkles className="w-5 h-5 text-blue-500 opacity-20 group-focus-within:opacity-100 transition-opacity" />
                                </div>
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    aria-label="Message au compagnon"
                                    placeholder="Posez une question sur le Lore, les fusions ou demandez conseil..."
                                    className="w-full bg-black border-2 border-white/5 rounded-[2.5rem] py-5 pl-16 pr-8 text-sm font-bold focus:border-blue-600 outline-none transition-all placeholder:opacity-20"
                                />
                            </div>
                            <Button 
                                type="submit" 
                                disabled={!input.trim() || isLoading}
                                variant="primary" 
                                className="bg-blue-600 hover:bg-blue-500 border-none w-16 h-16 rounded-full p-0 flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-all"
                            >
                                <Send className="w-6 h-6 text-white" />
                            </Button>
                        </form>
                    </div>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

const Loader2: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
);

export default CompanionChatPage;


