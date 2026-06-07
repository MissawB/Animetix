import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { motion } from 'framer-motion';
import { Sword, Users, Hash, Zap, Trophy, ShieldAlert } from 'lucide-react';

const DuelLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = React.useState('');
  const [error, setError] = React.useState('');

  const createRoomMutation = useMutation({
    mutationFn: async (mediaType: string) => {
      const res = await fetch('/api/game/duel/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_type: mediaType })
      });
      if (!res.ok) throw new Error('Failed to create room');
      return res.json();
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    }
  });

  const joinRoomMutation = useMutation({
    mutationFn: async (code: string) => {
      const res = await fetch('/api/game/duel/join/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_code: code })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to join room');
      }
      return res.json();
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    },
    onError: (err: any) => {
      setError(err.message);
    }
  });

  const matchmakingMutation = useMutation({
    mutationFn: async (mediaType: string) => {
      const res = await fetch('/api/game/duel/matchmaking/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_type: mediaType })
      });
      if (!res.ok) throw new Error('Matchmaking failed');
      return res.json();
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    }
  });

  return (
    <AnimatedPage>
      <div className="max-w-4xl mx-auto px-6 py-16 text-white">
        <header className="text-center mb-16">
          <motion.div
            initial={{ rotate: -10, scale: 0.8 }}
            animate={{ rotate: 0, scale: 1 }}
            className="inline-block p-4 bg-red-600/20 rounded-3xl mb-6 border border-red-500/30"
          >
            <Sword size={48} className="text-red-500" />
          </motion.div>
          <h1 className="text-6xl font-black italic uppercase tracking-tighter mb-4">Duel <span className="text-red-500">Arena</span></h1>
          <p className="text-gray-400 font-bold uppercase tracking-widest text-sm">Affrontez d'autres Otakus en temps réel</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Quick Match */}
          <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 text-red-500 mb-6">
                <Zap fill="currentColor" size={24} />
                <h2 className="text-2xl font-black uppercase italic">Matchmaking</h2>
              </div>
              <p className="text-gray-400 mb-8 leading-relaxed">
                Trouvez instantanément un adversaire de votre niveau et grimpez dans le classement mondial.
              </p>
            </div>
            <button 
              onClick={() => matchmakingMutation.mutate('anime')}
              disabled={matchmakingMutation.isPending}
              className="w-full bg-red-600 hover:bg-red-500 p-5 rounded-2xl font-black italic uppercase tracking-widest transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-3"
            >
              {matchmakingMutation.isPending ? 'RECHERCHE...' : 'LANCER UN DUEL'}
              <Trophy size={20} />
            </button>
          </div>

          {/* Private Room */}
          <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5">
            <div className="flex items-center gap-3 text-blue-500 mb-6">
              <Users size={24} />
              <h2 className="text-2xl font-black uppercase italic">Salon Privé</h2>
            </div>
            
            <div className="space-y-6">
              <div className="relative">
                <input 
                  type="text" 
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                  placeholder="CODE DU SALON"
                  className="w-full bg-black border-2 border-gray-800 rounded-2xl px-6 py-4 focus:border-blue-600 outline-none transition-all font-mono font-bold tracking-[0.5em] text-center placeholder:text-gray-700 placeholder:tracking-normal"
                />
                {error && (
                  <div className="absolute -bottom-6 left-0 right-0 text-center text-red-500 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-1">
                    <ShieldAlert size={12} /> {error}
                  </div>
                )}
              </div>
              
              <div className="flex gap-4">
                <button 
                  onClick={() => joinRoomMutation.mutate(roomCode)}
                  disabled={!roomCode || joinRoomMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-20 p-4 rounded-2xl font-black italic uppercase tracking-widest transition-all"
                >
                  REJOINDRE
                </button>
                <button 
                  onClick={() => createRoomMutation.mutate('anime')}
                  disabled={createRoomMutation.isPending}
                  className="flex-1 border-2 border-blue-600/50 hover:bg-blue-600/10 p-4 rounded-2xl font-black italic uppercase tracking-widest transition-all"
                >
                  CRÉER
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-12 bg-red-950/10 p-6 rounded-3xl border border-red-900/20 flex gap-4 items-center">
            <Hash className="text-red-500 shrink-0" size={24} />
            <p className="text-gray-400 text-xs font-bold leading-relaxed uppercase">
                Les duels sont basés sur le mode "Classic" : devinez le titre de l'œuvre avant votre adversaire. 
                Chaque victoire en mode classé rapporte des points de prestige.
            </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default DuelLobbyPage;

