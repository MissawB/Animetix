import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from "../../hooks/useSocket";
import { Users, Send, ShieldAlert } from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";



import { GamePlayer, ChatMessage } from '../../types';

const UndercoverRoom: React.FC = () => {
  
  const { roomCode } = useParams<{ roomCode: string }>();
  const { gameState, messages, connected, sendAction } = useSocket(roomCode, 'undercover');
  const [inputMessage, setInputMessage] = useState<string>('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      sendAction('chat', { message: inputMessage });
      setInputMessage('');
    }
  };

  if (!connected) return <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-[0.4em]">Connexion au réseau...</div>;

  const players = (gameState?.players as GamePlayer[]) || [];
  const chatMessages = (messages as unknown as ChatMessage[]) || [];

  return (
    
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          
          {/* Liste des Joueurs */}
          <Card padding="lg" className="lg:col-span-1 h-fit">
              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                  <Users className="w-4 h-4" /> Unité d'élite
              </h3>
              <div className="space-y-4">
                  {players.map((player) => (
                      <div key={player.id} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl border border-gray-100 dark:border-white/5">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black italic shadow-lg ${player.is_me ? 'bg-yellow-400 text-black border-2 border-black' : 'bg-gray-200 dark:bg-navy-700'}`}>
                              {player.username[0].toUpperCase()}
                          </div>
                          <span className="font-bold">{player.username}</span>
                          {player.is_ready && <Badge variant="success" className="ml-auto">PRÊT</Badge>}
                      </div>
                  ))}
              </div>
          </Card>

          {/* Zone de Jeu / Chat */}
          <div className="lg:col-span-2 space-y-8">
              <Card padding="lg" className="min-h-[400px] flex flex-col">
                  <h2 className="text-3xl font-black italic manga-font mb-8 flex items-center gap-3 uppercase tracking-tighter">
                      <ShieldAlert className="w-8 h-8 text-brand-danger" /> MISSION : <span className="text-brand-danger">{roomCode}</span>
                  </h2>

                  <div className="flex-grow bg-gray-50 dark:bg-navy-900 rounded-3xl p-6 mb-8 overflow-y-auto max-h-80 border border-gray-100 dark:border-white/5 shadow-inner">
                      {chatMessages.map((msg, i) => (
                          <div key={i} className="mb-4 flex flex-col animate-fade-in">
                              <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{msg.user}</span>
                              <span className="font-medium text-lg">{msg.text}</span>
                          </div>
                      ))}
                      {chatMessages.length === 0 && <p className="text-center py-20 opacity-20 italic">En attente de communications...</p>}
                  </div>

                  <form onSubmit={handleSendMessage} className="flex gap-4">
                      <Input 
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          placeholder="Tapez un message d'infiltration..."
                          className="flex-grow border-none shadow-xl"
                      />
                      <Button type="submit" variant="danger" className="p-5">
                          <Send className="w-6 h-6" />
                      </Button>
                  </form>
              </Card>
          </div>
        </div>
      </div>
    
  );
};

export default UndercoverRoom;


