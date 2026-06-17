import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Gamepad2, Check, X, Clock } from 'lucide-react';

interface GameSession {
  id: number;
  game_mode: string;
  media_type: string;
  target_item: string;
  was_won: boolean;
  history: Record<string, unknown>[]; 
  created_at: string;
}

export const GameHistoryPanel: React.FC = () => {

  const { data: sessions, isLoading, isError } = useQuery<GameSession[]>({
    queryKey: ['gameplay-history'],
    queryFn: () => apiClient('/api/v1/social/gameplay-history/?limit=10'),
  });

  if (isLoading) {
    return <div className="animate-pulse bg-white/5 h-64 rounded-3xl"></div>;
  }

  if (isError || !sessions) {
    return <div className="text-center opacity-50 italic">Impossible de charger l'historique des jeux.</div>;
  }

  return (
    <Card padding="lg" className="bg-navy-900/40 border-white/5 h-full">
        <div className="flex items-center justify-between mb-8">
            <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                <Gamepad2 className="w-4 h-4 text-blue-500" /> Historique de Jeu
            </h3>
            <span className="text-[10px] font-black uppercase bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full">10 Derniers</span>
        </div>
        
        <div className="space-y-4 overflow-y-auto pr-2" style={{ maxHeight: '400px' }}>
            {sessions.map((session) => (
                <div key={session.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors">
                    <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${session.was_won ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}`}>
                            {session.was_won ? <Check className="w-6 h-6" /> : <X className="w-6 h-6" />}
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-black uppercase tracking-widest bg-white/10 px-2 py-0.5 rounded text-white">{session.game_mode}</span>
                                <span className="text-xs opacity-60 font-bold">{session.media_type}</span>
                            </div>
                            <p className="font-bold text-sm">Cible : <span className="text-yellow-500 italic">{session.target_item}</span></p>
                        </div>
                    </div>
                    
                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 opacity-50 text-[10px] font-black uppercase tracking-widest">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(session.created_at).toLocaleDateString()}</span>
                        <span>{session.history?.length || 0} Tours</span>
                    </div>
                </div>
            ))}
            
            {sessions.length === 0 && (
                <div className="text-center py-12">
                    <Gamepad2 className="w-12 h-12 mx-auto mb-4 opacity-10" />
                    <p className="opacity-40 italic font-bold">Aucune partie jouée récemment.</p>
                </div>
            )}
        </div>
    </Card>
  );
};
