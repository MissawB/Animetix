import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import { Sword, User, Zap, Trophy, Timer, XCircle, Users, Radio } from 'lucide-react';
// Shapes pushed over the duel WebSocket (snake_case, distinct from the generic
// turn-based DuelGameState in src/types).
interface DuelGameState {
  player1: string;
  player2?: string;
  secret_title: string;
  media_type: string;
}

interface DuelLog {
  type: string;
  player: string;
  winner: string;
  score: number;
}

const DuelArenaPage: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [socket, setSocket] = React.useState<WebSocket | null>(null);
  const [gameState, setGameState] = React.useState<DuelGameState | null>(null);
  const [guess, setGuess] = React.useState('');
  const [logs, setLogs] = React.useState<DuelLog[]>([]);
  const [winner, setWinner] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!roomCode) return;
    let isMounted = true;
    const initSocket = async () => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/ws/duel/${roomCode}/`;
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'duel_state') {
                setGameState(data);
            } else if (data.type === 'opponent_guess') {
                setLogs(prev => [{ type: 'guess', ...data }, ...prev.slice(0, 4)]);
            } else if (data.type === 'duel_finished') {
                setWinner(data.winner);
                setLogs(prev => [{ type: 'win', ...data }, ...prev]);
            }
        };

        ws.onclose = () => {
            // Optionnel : gérer la déconnexion
        };

        if (isMounted) {
            setSocket(ws);
        }
    };

    initSocket();
    return () => {
        isMounted = false;
        // socket?.close() est géré par la fermeture de ws dans le cleanup
    };
  }, [roomCode]);

  const handleGuess = (e: React.FormEvent) => {
    e.preventDefault();
    if (!guess.trim() || !socket || winner) return;
    socket.send(JSON.stringify({ type: 'guess', guess }));
    setGuess('');
  };

  if (!gameState) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
        <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
    </div>
  );

  const isWaiting = !gameState.player2;

  return (
    <AnimatedPage>
      <div className="max-w-6xl mx-auto px-6 py-12 text-white">
        <header className="flex justify-between items-center mb-12">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-600/20 rounded-2xl border border-blue-500/30">
                    <Timer size={24} className="text-blue-500" />
                </div>
                <div>
                    <div className="text-gray-500 text-[10px] font-black uppercase tracking-widest">Salon Code</div>
                    <div className="text-2xl font-mono font-black tracking-widest text-blue-500">{roomCode}</div>
                </div>
            </div>

            <button 
                onClick={() => navigate('/game/duel/lobby/')}
                className="text-gray-600 hover:text-white transition-colors flex items-center gap-2 font-bold uppercase text-xs tracking-widest"
            >
                <XCircle size={18} /> Quitter
            </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Players Header */}
            <div className="lg:col-span-2 space-y-8">
                <div className="flex items-center justify-center gap-8 md:gap-16">
                    {/* Player 1 */}
                    <div className="text-center">
                        <div className={`w-24 h-24 md:w-32 md:h-32 rounded-full border-4 ${user?.username === gameState.player1 ? 'border-blue-500' : 'border-gray-800'} p-2 mb-4 relative`}>
                            <div className="w-full h-full bg-gray-900 rounded-full flex items-center justify-center">
                                <User size={48} className="text-gray-700" />
                            </div>
                            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-blue-600 px-3 py-1 rounded-full text-[10px] font-black uppercase italic">P1</div>
                        </div>
                        <div className="font-black italic uppercase text-lg">{gameState.player1}</div>
                    </div>

                    <div className="text-4xl font-black italic text-red-600 animate-pulse mt-[-40px]">VS</div>

                    {/* Player 2 */}
                    <div className="text-center">
                        <div className={`w-24 h-24 md:w-32 md:h-32 rounded-full border-4 ${user?.username === gameState.player2 ? 'border-blue-500' : (gameState.player2 ? 'border-gray-800' : 'border-dashed border-gray-700')} p-2 mb-4 relative`}>
                            <div className="w-full h-full bg-gray-900 rounded-full flex items-center justify-center">
                                {gameState.player2 ? <User size={48} className="text-gray-700" /> : <Zap size={32} className="text-gray-800 animate-pulse" />}
                            </div>
                            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-red-600 px-3 py-1 rounded-full text-[10px] font-black uppercase italic">P2</div>
                        </div>
                        <div className="font-black italic uppercase text-lg">
                            {gameState.player2 || 'Attente...'}
                        </div>
                    </div>
                </div>

                {isWaiting ? (
                    <div className="bg-blue-600/10 border-2 border-dashed border-blue-500/30 rounded-3xl p-12 text-center">
                        <motion.div 
                            animate={{ scale: [1, 1.1, 1] }} 
                            transition={{ duration: 2, repeat: Infinity }}
                            className="text-blue-500 mb-4 flex justify-center"
                        >
                            <Users size={64} />
                        </motion.div>
                        <h3 className="text-2xl font-black italic uppercase mb-2">En attente d'un adversaire</h3>
                        <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Partagez le code <span className="text-blue-500">{roomCode}</span> pour inviter un ami</p>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Duel Feedback Visualizer */}
                        <div className="aspect-video bg-gradient-to-br from-navy-900/50 to-black rounded-3xl border border-white/5 relative overflow-hidden flex items-center justify-center p-12 text-center">
                             <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10" />
                             
                             <AnimatePresence mode="wait">
                                {winner ? (
                                    <motion.div 
                                        initial={{ scale: 0.5, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        className="relative z-10"
                                    >
                                        <Trophy size={80} className="text-yellow-500 mx-auto mb-6" />
                                        <h2 className="text-5xl font-black italic uppercase mb-2">
                                            {winner === user?.username ? 'VICTOIRE !' : 'DÉFAITE'}
                                        </h2>
                                        <p className="text-gray-400 font-bold uppercase tracking-widest">Le titre était : <span className="text-blue-500">{gameState.secret_title || 'REDACTED'}</span></p>
                                        <button 
                                            onClick={() => navigate('/game/duel/lobby/')}
                                            className="mt-8 bg-white text-black px-8 py-3 rounded-xl font-black italic uppercase tracking-widest hover:scale-105 transition-all"
                                        >
                                            Retour au Lobby
                                        </button>
                                    </motion.div>
                                ) : (
                                    <motion.div 
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="relative z-10"
                                    >
                                        <Sword size={64} className="text-red-500 mx-auto mb-6 animate-bounce" />
                                        <h3 className="text-3xl font-black italic uppercase mb-4">Duel en cours !</h3>
                                        <p className="text-gray-500 uppercase font-bold tracking-widest text-sm">Devinez l'œuvre {gameState.media_type} avant l'adversaire</p>
                                    </motion.div>
                                )}
                             </AnimatePresence>
                        </div>

                        {/* Input Form */}
                        {!winner && (
                            <form onSubmit={handleGuess} className="relative group">
                                <input 
                                    type="text" 
                                    value={guess}
                                    onChange={(e) => setGuess(e.target.value)}
                                    placeholder="VOTRE RÉPONSE..."
                                    className="w-full bg-black border-2 border-gray-800 rounded-2xl px-6 py-5 focus:border-red-600 outline-none transition-all font-bold tracking-widest uppercase placeholder:text-gray-700"
                                />
                                <button 
                                    type="submit"
                                    className="absolute right-4 top-1/2 -translate-y-1/2 bg-red-600 hover:bg-red-500 px-8 py-3 rounded-xl font-black italic uppercase tracking-widest transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
                                >
                                    ENVOYER <Zap size={16} fill="currentColor" />
                                </button>
                            </form>
                        )}
                    </div>
                )}
            </div>

            {/* Duel Logs / Sidebar */}
            <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5 h-fit">
                <h3 className="text-xl font-black italic uppercase mb-8 flex items-center gap-3">
                    <Radio size={20} className="text-red-500" />
                    Flux de combat
                </h3>
                
                <div className="space-y-4">
                    {logs.length > 0 ? logs.map((log, i) => (
                        <motion.div 
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            key={i}
                            className={`p-4 rounded-xl border-l-4 ${log.type === 'win' ? 'bg-yellow-500/10 border-yellow-500' : 'bg-black/40 border-blue-500'} text-xs font-bold uppercase tracking-widest`}
                        >
                            {log.type === 'win' ? (
                                <div className="flex items-center gap-2 text-yellow-500">
                                    <Trophy size={14} /> {log.winner} a remporté le duel !
                                </div>
                            ) : (
                                <div className="text-gray-400">
                                    <span className="text-blue-500">@{log.player}</span> a tenté une attaque : <span className="text-white">{log.score}%</span>
                                </div>
                            )}
                        </motion.div>
                    )) : (
                        <div className="text-center py-12 text-gray-700 uppercase font-black italic tracking-widest text-xs">
                            En attente d'actions...
                        </div>
                    )}
                </div>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default DuelArenaPage;


