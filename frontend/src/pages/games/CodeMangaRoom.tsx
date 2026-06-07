import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from "../../hooks/useSocket";
import { Code2, Send, Users, Sparkles } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';

import { useTranslation } from 'react-i18next';

const CodeMangaRoom: React.FC = () => {
  const { t } = useTranslation();
  const { roomCode } = useParams<{ roomCode: string }>();
  const { gameState, messages, connected, sendAction } = useSocket(roomCode, 'codemanga');
  const [inputMessage, setInputMessage] = useState<string>('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      sendAction('chat', { message: inputMessage });
      setInputMessage('');
    }
  };

  if (!connected) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-[0.4em]">Connexion au terminal...</div>;

  return (
    
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          
          {/* Sidebar Status */}
          <div className="lg:col-span-1 space-y-8">
              <Card padding="lg">
                  <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                      <Users className="w-4 h-4" /> Hackers actifs
                  </h3>
                  <div className="space-y-4">
                      {gameState?.players?.map((player: any) => (
                          <div key={player.id} className="flex items-center gap-4 p-2">
                              <div className={`w-3 h-3 rounded-full ${player.is_online ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-gray-300'}`}></div>
                              <span className="font-bold text-sm">{player.username}</span>
                          </div>
                      ))}
                  </div>
              </Card>

              <Card padding="lg" className="bg-brand-primary text-white border-none relative overflow-hidden shadow-brand-primary/20">
                  <Code2 className="w-20 h-20 absolute -right-4 -bottom-4 opacity-10" />
                  <h4 className="font-black italic mb-2 uppercase">MODE : DÉCRYPTAGE</h4>
                  <p className="text-xs opacity-80 leading-relaxed font-bold">Trouvez l'animé caché derrière les fragments de code générés par l'IA.</p>
              </Card>
          </div>

          {/* Main Terminal */}
          <div className="lg:col-span-3 bg-black rounded-[3.5rem] shadow-2xl border-4 border-white/5 min-h-[600px] flex flex-col overflow-hidden animate-fade-in">
              <div className="bg-white/5 p-6 flex justify-between items-center border-b border-white/5">
                  <div className="flex gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500 shadow-lg shadow-red-500/20"></div>
                      <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-lg shadow-yellow-500/20"></div>
                      <div className="w-3 h-3 rounded-full bg-green-500 shadow-lg shadow-green-500/20"></div>
                  </div>
                  <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.3em]">SESSION : {roomCode}</span>
              </div>

              <div className="flex-grow p-10 flex flex-col">
                  <div className="bg-gray-900 rounded-3xl p-8 mb-8 border border-white/10 font-mono text-green-400 relative shadow-inner">
                      <Sparkles className="w-6 h-6 absolute top-6 right-6 opacity-20" />
                      <pre className="whitespace-pre-wrap text-sm md:text-lg">
                          {gameState?.current_code || '// Initialisation de la session de hack...'}
                      </pre>
                  </div>

                  <div className="mt-auto">
                      <div className="bg-white/5 rounded-3xl p-6 mb-6 max-h-40 overflow-y-auto border border-white/5">
                          {messages.map((msg: any, i: number) => (
                              <div key={i} className="text-xs mb-2 animate-fade-in">
                                  <span className="text-blue-400 font-bold mr-2">[{msg.user}]:</span>
                                  <span className="text-white/70">{msg.text}</span>
                              </div>
                          ))}
                          {messages.length === 0 && <p className="text-center text-white/10 italic text-[10px]">TERMINAL SILENCIEUX</p>}
                      </div>

                      <form onSubmit={handleSendMessage} className="relative flex gap-4">
                          <Input 
                              value={inputMessage}
                              onChange={(e) => setInputMessage(e.target.value)}
                              className="flex-grow bg-white/10 border-white/10 text-white placeholder:text-white/20 border-none shadow-xl"
                              placeholder="Votre proposition de décryptage..."
                          />
                          <Button type="submit" variant="primary" className="p-5 bg-blue-500 hover:bg-blue-600 border-none">
                              <Send className="w-6 h-6" />
                          </Button>
                      </form>
                  </div>
              </div>
          </div>
        </div>
      </div>
    
  );
};

export default CodeMangaRoom;

