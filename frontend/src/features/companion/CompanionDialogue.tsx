import React, { useState, useRef, useEffect } from 'react';
import { useCompanionStore } from './companionStore';
import { Send, Loader2, Trash2, Bot, Maximize2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const CompanionDialogue: React.FC = () => {
  const { history, isLoading, sendMessage, clearHistory, activeMentor, setMentor, toggleOpen } = useCompanionStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const handleMaximize = () => {
    toggleOpen();
    navigate('/companion/chat/');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await sendMessage(message);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white rounded-lg overflow-hidden border border-slate-700 shadow-2xl">
      {/* Header */}
      <div className="p-4 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center">
            <Bot size={20} />
          </div>
          <div>
            <h3 className="font-bold text-sm leading-none">AI Mentor</h3>
            <span className="text-xs text-slate-400 capitalize">{activeMentor} Mode</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleMaximize}
            className="p-1 hover:bg-slate-700 rounded transition-colors text-slate-400 hover:text-blue-400"
            title="Open Full Hub"
          >
            <Maximize2 size={16} />
          </button>
          <button 
            onClick={clearHistory}
            className="p-1 hover:bg-slate-700 rounded transition-colors text-slate-400 hover:text-red-400"
            title="Clear history"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {history.length === 0 && (
          <div className="text-center py-8 text-slate-500 italic text-sm">
            Ask your mentor anything about this page...
          </div>
        )}
        
        {history.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700'
            }`}>
              {msg.content}
            </div>
          </motion.div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 p-3 rounded-2xl rounded-tl-none border border-slate-700">
              <Loader2 className="animate-spin text-indigo-500" size={18} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Mentors Selection (Small) */}
      <div className="px-4 py-2 bg-slate-800/50 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-700/50">
        {['sensei', 'tsundere', 'kuudere', 'yandere'].map((m) => (
          <button
            key={m}
            onClick={() => setMentor(m)}
            className={`px-2 py-1 rounded-md text-[10px] uppercase font-bold transition-all ${
              activeMentor === m 
                ? 'bg-indigo-600 text-white' 
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 bg-slate-800 border-t border-slate-700 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          aria-label="Message"
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 p-2 rounded-lg transition-colors"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

export default CompanionDialogue;
