import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sparkles, Send, Brain, Bot, User, Target } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

import { animinatorService } from '../../features/games/services/animinatorService';

interface Message {
  role: 'ai' | 'user';
  text: string;
}

const AniminatorPage: React.FC = () => {
  const { t } = useTranslation();
  const INTRO: Message = {
    role: 'ai',
    text: t(
      'games.animinator.intro',
      "J'ai une œuvre mystère en tête (anime, manga ou personnage). Pose-moi des questions, puis tente de deviner ce que c'est !",
    ),
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
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thoughtProcess]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setIsThinking(true);
    setThoughtProcess(t('games.animinator.analyzing', 'Analyse de la requête...'));

    try {
      const data = await animinatorService.ask(userMsg, mediaType, difficulty);

      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            role: 'ai',
            text:
              data.answer ||
              t('games.animinator.default_answer', 'Je commence à voir plus clair...'),
          },
        ]);
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
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        text: t('games.animinator.guess_message', {
          defaultValue: "Je pense que c'est : {{guess}}",
          guess: g,
        }),
      },
    ]);
    try {
      const res = await animinatorService.guess(g);
      if (res.correct) {
        setWon(true);
        setMessages((prev) => [
          ...prev,
          {
            role: 'ai',
            text: t('games.animinator.correct_message', {
              defaultValue: "🎉 Exact ! C'était bien « {{secret}} ». Bien joué !",
              secret: res.secret,
            }),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'ai',
            text: t('games.animinator.wrong_message', {
              defaultValue: "Non, ce n'est pas « {{guess}} ». Continue à creuser !",
              guess: g,
            }),
          },
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
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-4xl mx-auto px-6 py-12 flex flex-col h-[calc(100vh-160px)]">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              命
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.animinator.subtitle', 'Génie Omni-Media IA')}
            </span>
          </div>
          <h1 className="text-5xl font-black italic font-manga tracking-tighter uppercase text-[#F4F1E8]">
            THE <span className="text-[#E8442B]">ANIMINATOR</span>
          </h1>
        </div>

        {/* Chat Area */}
        <div className="flex-grow overflow-hidden flex flex-col relative rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]">
          {/* Thought Overlay */}
          {isThinking && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-[#0B0C10]/90 px-6 py-3 rounded-xl border border-[#FDB913]/30 flex items-center gap-3 animate-slide-down">
              <Brain className="w-4 h-4 text-[#FDB913] animate-pulse" />
              <span className="text-[#F4F1E8] text-[10px] font-black uppercase tracking-widest">
                {thoughtProcess}
              </span>
            </div>
          )}

          <div className="flex-grow overflow-y-auto p-8 space-y-6">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${msg.role === 'ai' ? 'bg-[#FDB913] text-[#0B0C10]' : 'bg-[#E8442B] text-[#F4F1E8]'}`}
                  >
                    {msg.role === 'ai' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                  </div>
                  <div
                    className={`p-5 rounded-2xl font-medium text-lg ${msg.role === 'ai' ? 'bg-[#0B0C10] text-[#F4F1E8] rounded-tl-none border border-[#F4F1E8]/10' : 'bg-[#E8442B] text-[#F4F1E8] rounded-tr-none'}`}
                  >
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-8 bg-[#0B0C10]/50 border-t border-[#F4F1E8]/10 space-y-3">
            {won ? (
              <button
                onClick={handleReplay}
                className="w-full flex items-center justify-center gap-2 bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest py-5 rounded-xl transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                <Sparkles className="w-5 h-5" />{' '}
                {t('games.animinator.replay', 'Rejouer une nouvelle œuvre')}
              </button>
            ) : (
              <>
                <form onSubmit={handleSend} className="relative flex gap-4">
                  <div className="relative flex-grow">
                    <Sparkles className="absolute left-6 top-1/2 -translate-y-1/2 z-10 w-5 h-5 text-[#FDB913]" />
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      disabled={isThinking}
                      className="pl-16 !bg-[#0F1016] !border-[#F4F1E8]/15 focus:!border-[#FDB913] text-[#F4F1E8]"
                      placeholder={t(
                        'games.animinator.ask_placeholder',
                        'Posez votre question au génie...',
                      )}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isThinking || !input.trim()}
                    className="!bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] p-6 rounded-xl"
                  >
                    <Send className="w-6 h-6" />
                  </Button>
                </form>
                {/* Guess bar */}
                <form onSubmit={handleGuess} className="relative flex gap-4">
                  <div className="relative flex-grow">
                    <Target className="absolute left-6 top-1/2 -translate-y-1/2 z-10 w-5 h-5 text-[#FDB913]" />
                    <Input
                      value={guessInput}
                      onChange={(e) => setGuessInput(e.target.value)}
                      disabled={isThinking}
                      className="pl-16 !bg-[#0F1016] !border-[#F4F1E8]/15 focus:!border-[#FDB913] text-[#F4F1E8]"
                      placeholder={t('games.animinator.guess_placeholder', "Je pense que c'est…")}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isThinking || !guessInput.trim()}
                    className="!bg-[#FDB913] hover:!bg-[#e0a50f] !text-[#0B0C10] px-6 rounded-xl font-black uppercase tracking-widest text-sm"
                  >
                    {t('games.animinator.guess_btn', 'Deviner')}
                  </Button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AniminatorPage;
