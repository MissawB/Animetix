import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Sparkles, Send, Brain, Bot, User, Target } from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";


import { animinatorService } from "../../features/games/services/animinatorService";

interface Message {
  role: 'ai' | 'user';
  text: string;
}

const AniminatorPage: React.FC = () => {
  const INTRO: Message = {
    role: 'ai',
    text: "J'ai une œuvre mystère en tête (anime, manga ou personnage). Pose-moi des questions, puis tente de deviner ce que c'est !",
  };
  const [messages, setMessages] = useState<Message[]>([INTRO]);
  const [won, setWon] = useState(false);
  const [guessInput, setGuessInput] = useState('');
  const [input, setInput] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [thoughtProcess, setThoughtProcess] = useState<string>('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  // Univers + difficulté choisis dans le lobby Akinetix (au démarrage de la partie).
  const navState = location.state as { mediaType?: string; difficulty?: string } | null;
  const mediaType = navState?.mediaType;
  const difficulty = navState?.difficulty;

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thoughtProcess]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsThinking(true);
    setThoughtProcess('Analyse de la requête...');

    try {
      const data = await animinatorService.ask(userMsg, mediaType, difficulty);
      
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'ai', text: data.answer || "Je commence à voir plus clair..." }]);
        setThoughtProcess('');
        setIsThinking(false);
      }, 1500);

    } catch (err) {
      console.error(err);
      setIsThinking(false);
      setThoughtProcess('');
    }
  };

  const handleGuess = async (e: React.FormEvent) => {
    e.preventDefault();
    const g = guessInput.trim();
    if (!g || isThinking || won) return;
    setGuessInput('');
    setMessages((prev) => [...prev, { role: 'user', text: `Je pense que c'est : ${g}` }]);
    try {
      const res = await animinatorService.guess(g);
      if (res.correct) {
        setWon(true);
        setMessages((prev) => [
          ...prev,
          { role: 'ai', text: `🎉 Exact ! C'était bien « ${res.secret} ». Bien joué !` },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'ai', text: `Non, ce n'est pas « ${g} ». Continue à creuser !` },
        ]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleReplay = () => {
    setWon(false);
    setMessages([INTRO]);
  };

  return (
    
      <div className="max-w-4xl mx-auto px-6 py-12 flex flex-col h-[calc(100vh-200px)]">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase">
            THE <span className="text-yellow-400">ANIMINATOR</span>
          </h1>
          <p className="text-xs font-black uppercase opacity-40 tracking-[0.3em] mt-2">Génie Omni-Media IA</p>
        </div>

        {/* Chat Area */}
        <Card padding="none" className="flex-grow overflow-hidden flex flex-col relative border-none shadow-2xl">
          
          {/* Thought Overlay */}
          {isThinking && (
              <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-black/80 backdrop-blur-md px-6 py-3 rounded-2xl border border-yellow-400/30 flex items-center gap-3 animate-slide-down">
                  <Brain className="w-4 h-4 text-yellow-400 animate-pulse" />
                  <span className="text-white text-[10px] font-black uppercase tracking-widest">{thoughtProcess}</span>
              </div>
          )}

          <div className="flex-grow overflow-y-auto p-8 space-y-6">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === 'ai' ? 'bg-yellow-400 text-black' : 'bg-brand-primary text-white'}`}>
                    {msg.role === 'ai' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                  </div>
                  <div className={`p-5 rounded-3xl font-medium text-lg ${msg.role === 'ai' ? 'bg-gray-50 dark:bg-navy-900 text-black dark:text-white rounded-tl-none shadow-sm' : 'bg-brand-primary text-white rounded-tr-none shadow-xl'}`}>
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-8 bg-gray-50 dark:bg-navy-900/50 border-t border-gray-100 dark:border-white/5 space-y-3">
            {won ? (
              <button
                onClick={handleReplay}
                className="w-full flex items-center justify-center gap-2 bg-yellow-400 text-black font-black italic uppercase tracking-widest py-5 rounded-2xl shadow-xl hover:scale-[1.01] transition-all"
              >
                <Sparkles className="w-5 h-5" /> Rejouer une nouvelle œuvre
              </button>
            ) : (
              <>
                <form onSubmit={handleSend} className="relative flex gap-4">
                  <div className="relative flex-grow">
                    <Sparkles className="absolute left-6 top-1/2 -translate-y-1/2 z-10 w-5 h-5 text-yellow-500 opacity-50" />
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      disabled={isThinking}
                      className="pl-16 shadow-xl border-none bg-white dark:bg-navy-800"
                      placeholder="Posez votre question au génie..."
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isThinking || !input.trim()}
                    className="bg-black text-white p-6 rounded-2xl shadow-xl hover:scale-105"
                  >
                    <Send className="w-6 h-6" />
                  </Button>
                </form>
                {/* Guess bar */}
                <form onSubmit={handleGuess} className="relative flex gap-4">
                  <div className="relative flex-grow">
                    <Target className="absolute left-6 top-1/2 -translate-y-1/2 z-10 w-5 h-5 text-green-500 opacity-60" />
                    <Input
                      value={guessInput}
                      onChange={(e) => setGuessInput(e.target.value)}
                      disabled={isThinking}
                      className="pl-16 border-none bg-white dark:bg-navy-800"
                      placeholder="Je pense que c'est…"
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isThinking || !guessInput.trim()}
                    className="bg-green-600 text-white px-6 rounded-2xl shadow-xl hover:scale-105 font-black uppercase tracking-widest text-sm"
                  >
                    Deviner
                  </Button>
                </form>
              </>
            )}
          </div>
        </Card>
      </div>
    
  );
};

export default AniminatorPage;


