import React, { useState, useEffect, useRef } from 'react';
import { Send, Hash } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';

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

const buildWelcomeMessages = (clubName: string): Message[] => [
  {
    id: 'system-welcome',
    sender: 'System',
    content: `Welcome to the ${clubName} chat!`,
    timestamp: new Date().toISOString(),
  },
];

const ClubChat: React.FC<ClubChatProps> = ({ clubId, clubName }) => {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>(() => buildWelcomeMessages(clubName));
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // Reset local messages for the new club room during render (avoids cascading
  // renders from setState-in-effect). React re-renders before committing.
  const [renderedClubId, setRenderedClubId] = useState(clubId);
  if (renderedClubId !== clubId) {
    setRenderedClubId(clubId);
    setMessages(buildWelcomeMessages(clubName));
  }

  useEffect(() => {
    if (!clubId) return;

    let ws: WebSocket | null = null;
    let reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted) return;

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socketUrl = `${wsProtocol}//${window.location.host}/ws/club/${clubId}/`;
      
      console.log(`Connecting to club chat WebSocket: ${socketUrl}`);
      ws = new WebSocket(socketUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (isMounted) {
          setIsConnected(true);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          setIsConnected(false);
          // Only reconnect if the socket reference wasn't updated/closed intentionally
          if (socketRef.current === ws) {
            console.log("WebSocket disconnected. Reconnecting in 3 seconds...");
            reconnectTimeoutId = setTimeout(connectWebSocket, 3000);
          }
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        ws?.close();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // ClubConsumer broadcasts message containing:
          // { "text": "...", "username": "...", "type": "chat", "club_id": "..." }
          if (data && data.type === 'chat') {
            const messageSender = data.username === user?.username ? 'Me' : data.username;
            const newMsg: Message = {
              id: `${Date.now()}-${Math.random()}`,
              sender: messageSender,
              content: data.text || '',
              timestamp: new Date().toISOString(),
            };
            if (isMounted) {
              setMessages((prev) => [...prev, newMsg]);
            }
          }
        } catch (e) {
          console.error("Error parsing WebSocket message:", e);
        }
      };
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      if (reconnectTimeoutId) {
        clearTimeout(reconnectTimeoutId);
      }
      if (ws) {
        ws.close();
      }
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };
  }, [clubId, clubName, user?.username]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify({ message: newMessage }));
      setNewMessage('');
    } else {
      console.warn("Cannot send message: WebSocket is not connected.");
    }
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
