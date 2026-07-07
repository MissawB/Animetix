import React from 'react';
import { useTranslation } from 'react-i18next';
import { Radio, Send } from 'lucide-react';
import { UMsg } from '../../types';

interface UndercoverChatPanelProps {
  messages: UMsg[];
  chat: string;
  setChat: (v: string) => void;
  sendChat: (e: React.FormEvent) => void;
}

export const UndercoverChatPanel: React.FC<UndercoverChatPanelProps> = ({
  messages,
  chat,
  setChat,
  sendChat,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col">
      <h3 className="text-[11px] font-black uppercase opacity-40 mb-3 tracking-[0.25em] flex items-center gap-2">
        <Radio className="w-4 h-4" /> {t('games.undercover.room.chat_title', "Canal d'infiltration")}
      </h3>
      <div className="flex-grow bg-black/40 rounded-2xl p-5 mb-4 overflow-y-auto max-h-72 min-h-[150px] border border-white/5 custom-scrollbar font-mono">
        {messages.length === 0 && (
          <p className="text-center py-12 opacity-20 italic font-sans">
            {t('games.undercover.room.chat_empty', 'En attente de communications…')}
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`mb-2.5 ${msg.is_system ? 'text-center' : ''}`}>
            {msg.is_system ? (
              <span className="text-[11px] font-black uppercase tracking-widest text-yellow-400/50">— {msg.text} —</span>
            ) : (
              <p className="text-sm">
                <span className="text-red-400/70 font-bold">{msg.user}&gt; </span>
                <span className="text-white/85">{msg.text}</span>
              </p>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={sendChat} className="flex gap-3">
        <input
          value={chat}
          onChange={(e) => setChat(e.target.value)}
          placeholder={t('games.undercover.room.chat_placeholder', "Message d'infiltration…")}
          aria-label={t('games.undercover.room.chat_aria', 'Message')}
          maxLength={100}
          className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-red-500 outline-none font-medium text-white placeholder:text-white/25 transition-colors"
        />
        <button type="submit" className="px-5 rounded-2xl bg-red-600 hover:bg-red-500 text-white transition-colors">
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};
