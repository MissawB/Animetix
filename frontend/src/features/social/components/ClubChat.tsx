import React, { useState, useEffect, useRef } from 'react';
import { Send, Hash } from 'lucide-react';

interface Message {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
}

interface ClubChatProps {
  clubId: string;
  clubName: string;
}

const ClubChat: React.FC<ClubChatProps> = ({ clubId, clubName }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const lastInitId = useRef<string | null>(null);

  useEffect(() => {
    if (lastInitId.current === clubId) return;
    lastInitId.current = clubId;

    // For demo purposes, we'll simulate the connection
    setIsConnected(true);
    setMessages([
      { id: '1', sender: 'System', content: `Welcome to the ${clubName} chat!`, timestamp: new Date().toISOString() },
      { id: '2', sender: 'Alice', content: 'Hey everyone, anyone seen the latest episode?', timestamp: new Date().toISOString() },
    ]);

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      socketRef.current = null;
    };
  }, [clubId, clubName]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const msg: Message = {
      id: Date.now().toString(),
      sender: 'Me', // Should be fetched from authStore
      content: newMessage,
      timestamp: new Date().toISOString(),
    };

    // Simulation: add message to local state
    setMessages(prev => [...prev, msg]);
    setNewMessage('');

    // Real implementation:
    // if (socketRef.current && isConnected) {
    //   socketRef.current.send(JSON.stringify({ message: newMessage }));
    // }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-navy-900 rounded-3xl overflow-hidden border border-gray-100 dark:border-white/5 shadow-inner">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-gray-100 dark:border-white/5 flex items-center justify-between bg-gray-50/50 dark:bg-navy-800/50">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/10 text-blue-500 p-2 rounded-xl">
            <Hash className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-black italic uppercase text-sm tracking-widest">{clubName} Chat</h3>
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide"
      >
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex flex-col ${msg.sender === 'Me' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">{msg.sender}</span>
              <span className="text-[8px] text-gray-500">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div className={`px-4 py-2.5 rounded-2xl text-sm max-w-[80%] ${
              msg.sender === 'Me' 
                ? 'bg-blue-600 text-white rounded-tr-none' 
                : msg.sender === 'System'
                  ? 'bg-gray-100 dark:bg-navy-800 text-gray-500 italic text-center w-full max-w-none'
                  : 'bg-gray-100 dark:bg-navy-800 text-gray-800 dark:text-gray-200 rounded-tl-none'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <form 
        onSubmit={handleSendMessage}
        className="p-4 bg-gray-50 dark:bg-navy-800/50 border-t border-gray-100 dark:border-white/5"
      >
        <div className="relative">
          <input 
            type="text" 
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="w-full bg-white dark:bg-navy-900 border-none rounded-2xl px-6 py-4 text-sm focus:ring-2 focus:ring-blue-500/20 transition-all pr-16"
          />
          <button 
            type="submit"
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-700 text-white px-4 rounded-xl transition-all flex items-center justify-center group"
          >
            <Send className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ClubChat;
