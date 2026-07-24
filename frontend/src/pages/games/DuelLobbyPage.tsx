import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useTranslation } from 'react-i18next';
import { Users, Hash, Zap, Trophy, ShieldAlert } from 'lucide-react';
import { apiClient } from '../../utils/apiClient';

const DuelLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = React.useState('');
  const [error, setError] = React.useState('');

  const createRoomMutation = useMutation({
    mutationFn: async (mediaType: string) => {
      return apiClient('/api/game/duel/create/', {
        method: 'POST',
        body: JSON.stringify({ media_type: mediaType }),
      });
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    },
  });

  const joinRoomMutation = useMutation({
    mutationFn: async (code: string) => {
      return apiClient('/api/game/duel/join/', {
        method: 'POST',
        body: JSON.stringify({ room_code: code }),
      });
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    },
    onError: (err) => {
      const error = err as Error;
      setError(error.message);
    },
  });

  const matchmakingMutation = useMutation({
    mutationFn: async (mediaType: string) => {
      return apiClient('/api/game/duel/matchmaking/', {
        method: 'POST',
        body: JSON.stringify({ media_type: mediaType }),
      });
    },
    onSuccess: (data) => {
      navigate(`/game/duel/arena/${data.room_code}/`);
    },
  });

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16">
          <header className="relative mb-16">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-44"
              aria-hidden
            />
            <div className="relative flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                決
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                {t('games.duel.lobby_tagline', "Affrontez d'autres Otakus en temps réel")}
              </span>
            </div>
            <h1 className="font-manga relative mt-4 text-5xl md:text-7xl font-black italic uppercase tracking-tighter leading-none">
              Duel <span className="text-[#E8442B]">Arena</span>
            </h1>
            <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Quick Match */}
            <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 text-[#E8442B] mb-6">
                  <Zap fill="currentColor" size={24} />
                  <h2 className="font-manga text-2xl font-black uppercase italic">Matchmaking</h2>
                </div>
                <p className="text-[#8F94A5] mb-8 leading-relaxed">
                  {t(
                    'games.duel.matchmaking_desc',
                    'Trouvez instantanément un adversaire de votre niveau et grimpez dans le classement mondial.',
                  )}
                </p>
              </div>
              <button
                onClick={() => matchmakingMutation.mutate('anime')}
                disabled={matchmakingMutation.isPending}
                className="w-full bg-[#E8442B] hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 text-[#F4F1E8] p-5 rounded-xl font-manga font-black italic uppercase tracking-widest transition-colors flex items-center justify-center gap-3 border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                {matchmakingMutation.isPending
                  ? t('games.duel.searching', 'RECHERCHE...')
                  : t('games.duel.launch_duel', 'LANCER UN DUEL')}
                <Trophy size={20} />
              </button>
            </section>

            {/* Private Room */}
            <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
              <div className="flex items-center gap-3 text-[#FDB913] mb-6">
                <Users size={24} />
                <h2 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]">
                  {t('games.duel.private_room', 'Salon Privé')}
                </h2>
              </div>

              <div className="space-y-6">
                <div className="relative">
                  <input
                    type="text"
                    value={roomCode}
                    onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                    placeholder={t('games.duel.code_placeholder', 'CODE DU SALON')}
                    aria-label={t('games.duel.code_aria', 'Code du salon')}
                    className="w-full bg-[#0B0C10] border border-[#F4F1E8]/15 rounded-xl px-6 py-4 focus:border-[#FDB913] outline-none transition-colors font-mono font-bold tracking-[0.5em] text-center text-[#F4F1E8] placeholder:text-[#8F94A5]/50 placeholder:tracking-normal"
                  />
                  {error && (
                    <div className="absolute -bottom-6 left-0 right-0 text-center text-[#E8442B] text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-1">
                      <ShieldAlert size={12} /> {error}
                    </div>
                  )}
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => joinRoomMutation.mutate(roomCode)}
                    disabled={!roomCode || joinRoomMutation.isPending}
                    className="flex-1 bg-[#E8442B] hover:bg-[#c93a24] disabled:opacity-30 disabled:cursor-not-allowed text-[#F4F1E8] p-4 rounded-xl font-manga font-black italic uppercase tracking-widest transition-colors border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                  >
                    {t('games.duel.join', 'REJOINDRE')}
                  </button>
                  <button
                    onClick={() => createRoomMutation.mutate('anime')}
                    disabled={createRoomMutation.isPending}
                    className="flex-1 border border-[#F4F1E8]/15 hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:opacity-40 text-[#8F94A5] p-4 rounded-xl font-manga font-black italic uppercase tracking-widest transition-colors bg-transparent cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                  >
                    {t('games.duel.create', 'CRÉER')}
                  </button>
                </div>
              </div>
            </section>
          </div>

          {/* Info Box */}
          <div className="mt-12 rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-6 flex gap-4 items-center">
            <Hash className="text-[#E8442B] shrink-0" size={24} />
            <p className="text-[#8F94A5] text-xs font-bold leading-relaxed uppercase">
              {t(
                'games.duel.info',
                'Les duels sont basés sur le mode "Classic" : devinez le titre de l\'œuvre avant votre adversaire. Chaque victoire en mode classé rapporte des points de prestige.',
              )}
            </p>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default DuelLobbyPage;
