import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Sparkles, MessageSquare, Users, Bot } from 'lucide-react';
import { useCompanionStore } from '../../features/companion/companionStore';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const CompanionChatPage: React.FC = () => {
  const [input, setInput] = useState('');
  const {
    history,
    isLoading,
    error,
    sendMessage,
    activeMentor,
    setMentor,
    clearHistory,
    customPersona,
    setCustomPersona,
  } = useCompanionStore();
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
      <div className="bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col h-[calc(100vh-120px)]">
          <header className="mb-8 flex flex-col md:flex-row justify-between items-end gap-6">
            <div>
              <div className="mb-2 flex items-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  伴
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  Compagnon · Mentor
                </span>
              </div>
              <h1 className="text-5xl font-black italic font-manga tracking-tighter uppercase">
                NEXUS <span className="text-[#E8442B]">COMPANION</span>
              </h1>
            </div>

            <div className="flex gap-4">
              <button
                onClick={clearHistory}
                className="inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 px-6 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#E8442B] hover:text-[#E8442B]"
              >
                <Trash2 className="w-4 h-4" /> REBOOT MÉMOIRE
              </button>
            </div>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-grow min-h-0">
            {/* Sidebar: Mentor Selection */}
            <div className="lg:col-span-3 space-y-6 overflow-y-auto no-scrollbar pb-6">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
                <h3 className="text-[10px] font-black uppercase text-[#8F94A5] mb-6 tracking-widest flex items-center gap-2">
                  <Users className="w-3 h-3" /> Sélection du Mentor
                </h3>
                <div className="space-y-3">
                  {MENTORS.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setMentor(m.id)}
                      className={`w-full p-4 rounded-xl text-left transition-colors border group ${
                        activeMentor === m.id
                          ? 'bg-[#F4F1E8] border-[#F4F1E8] text-[#0B0C10]'
                          : 'bg-[#0B0C10] border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#FDB913]/40 hover:text-[#F4F1E8]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-black italic uppercase text-xs font-manga tracking-tight">
                          {m.name}
                        </span>
                        <div
                          className={`w-2 h-2 rounded-full ${m.id === activeMentor ? 'bg-[#E8442B]' : 'bg-[#F4F1E8]/15'}`}
                        />
                      </div>
                      <p className="text-[9px] font-bold opacity-70 leading-tight uppercase">
                        {m.desc}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {activeMentor === 'custom' && (
                <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
                  <h3 className="text-[10px] font-black uppercase text-[#8F94A5] mb-3 tracking-widest flex items-center gap-2">
                    <Sparkles className="w-3 h-3 text-[#FDB913]" /> Personnalité
                  </h3>
                  <textarea
                    value={customPersona}
                    onChange={(e) => setCustomPersona(e.target.value)}
                    maxLength={600}
                    rows={5}
                    placeholder="Ex: Tu es un pirate jovial qui parle en métaphores marines et adore les défis."
                    aria-label="Personnalité du compagnon"
                    className="w-full p-3 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none text-xs font-medium leading-relaxed text-[#F4F1E8] placeholder:text-[#8F94A5]/60 resize-none transition-colors"
                  />
                  <p className="text-[9px] font-bold text-[#8F94A5]/60 uppercase tracking-widest mt-2 text-right">
                    {customPersona.length}/600
                  </p>
                </div>
              )}
            </div>

            {/* Chat Area */}
            <div className="lg:col-span-9 flex flex-col h-full gap-6">
              <div className="flex-grow flex flex-col bg-[#0F1016] border border-[#F4F1E8]/10 overflow-hidden rounded-2xl">
                {/* Chat Header */}
                <div className="px-8 py-6 border-b border-[#F4F1E8]/10 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-[#E8442B] flex items-center justify-center">
                      <Bot className="w-6 h-6 text-[#F4F1E8]" />
                    </div>
                    <div>
                      <span className="font-black italic uppercase text-sm font-manga">
                        {activeMentor.toUpperCase()} HUB
                      </span>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div
                  ref={scrollRef}
                  className="flex-grow overflow-y-auto p-8 space-y-8 scroll-smooth no-scrollbar"
                >
                  {history.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center px-12 text-[#8F94A5]/30">
                      <MessageSquare className="w-32 h-32 mb-6" />
                      <h3 className="text-2xl font-black italic font-manga uppercase mb-2 text-[#F4F1E8]/50">
                        Nexus Ouvert
                      </h3>
                      <p className="text-sm font-bold uppercase tracking-[0.2em]">
                        Initialisez la communication avec votre compagnon.
                      </p>
                    </div>
                  )}

                  {history.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                    >
                      <div
                        className={`max-w-[80%] flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                      >
                        <div
                          className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center font-black italic text-[10px] ${
                            msg.role === 'user'
                              ? 'bg-[#F4F1E8] text-[#0B0C10]'
                              : 'bg-[#E8442B] text-[#F4F1E8]'
                          }`}
                        >
                          {msg.role === 'user' ? 'ME' : 'AI'}
                        </div>
                        <div
                          className={`p-6 rounded-2xl text-sm leading-relaxed ${
                            msg.role === 'user'
                              ? 'bg-[#0B0C10] border border-[#F4F1E8]/10 text-[#F4F1E8]/90 rounded-tr-none'
                              : 'bg-[#0B0C10] border border-[#E8442B]/25 text-[#F4F1E8]/85 rounded-tl-none italic font-medium'
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start animate-pulse">
                      <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/10 flex items-center justify-center">
                          <Loader2 className="w-4 h-4 animate-spin text-[#8F94A5]/40" />
                        </div>
                        <div className="p-6 bg-[#0B0C10] border border-[#F4F1E8]/10 rounded-2xl rounded-tl-none">
                          <div className="flex gap-2">
                            <div className="w-2 h-2 bg-[#E8442B]/50 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-[#E8442B]/50 rounded-full animate-bounce [animation-delay:0.2s]" />
                            <div className="w-2 h-2 bg-[#E8442B]/50 rounded-full animate-bounce [animation-delay:0.4s]" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {error && (
                    <div className="flex justify-center animate-fade-in">
                      <div className="max-w-[90%] px-5 py-3 rounded-xl bg-[#E8442B]/10 border border-[#E8442B]/30 text-[#E8442B] text-xs font-bold text-center">
                        {error}
                      </div>
                    </div>
                  )}
                </div>

                {/* Input */}
                <div className="p-8 border-t border-[#F4F1E8]/10">
                  <form onSubmit={handleSend} className="relative flex items-center gap-4">
                    <div className="relative flex-grow group">
                      <div className="absolute left-6 top-1/2 -translate-y-1/2">
                        <Sparkles className="w-5 h-5 text-[#FDB913] opacity-40 group-focus-within:opacity-100 transition-opacity" />
                      </div>
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        aria-label="Message au compagnon"
                        placeholder="Posez une question sur le Lore, les fusions ou demandez conseil..."
                        className="w-full bg-[#0B0C10] border border-[#F4F1E8]/15 rounded-xl py-5 pl-16 pr-8 text-sm font-medium text-[#F4F1E8] focus:border-[#FDB913] outline-none transition-colors placeholder:text-[#8F94A5]/50"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={!input.trim() || isLoading}
                      className="bg-[#E8442B] hover:bg-[#c93a24] w-16 h-16 rounded-xl p-0 flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                    >
                      <Send className="w-6 h-6 text-[#F4F1E8]" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

const Loader2: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);

export default CompanionChatPage;
