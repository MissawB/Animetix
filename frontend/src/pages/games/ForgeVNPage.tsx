import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, Film, Play, Edit3, ArrowLeft, Sparkles } from 'lucide-react';
import { VNPlayer } from '../../features/games/components/VNPlayer';
import { VNDirector } from '../../features/games/components/VNDirector';

export const ForgeVNPage: React.FC = () => {
  const { fusionId } = useParams<{ fusionId: string }>();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'player' | 'director'>('player');
  const [scenes, setScenes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScript = async () => {
      try {
        // Simulation de l'appel API (à remplacer par votre appel réel)
        // const response = await fetch(`/api/v1/archetypist/vn/${fusionId}/`);
        // const data = await response.json();
        
        // Mock data pour la démo
        setTimeout(() => {
          setScenes([
            {
              background_url: "https://images.unsplash.com/photo-1578632738980-420af50de580?q=80&w=2070&auto=format&fit=crop",
              character_name: "Kaelith",
              character_sprite_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=kaelith",
              dialogue: "Le nexus est instable. Je sens les réalités se fragmenter autour de nous...",
              vibe: "Tense"
            },
            {
              background_url: "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=2094&auto=format&fit=crop",
              character_name: "Kaelith",
              character_sprite_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=kaelith",
              dialogue: "Si nous ne stabilisons pas le réacteur, la fusion sera irréversible.",
              vibe: "Urgent"
            }
          ]);
          setIsLoading(false);
        }, 1500);

      } catch (err) {
        setError("Impossible de charger le script du Visual Novel.");
        setIsLoading(false);
      }
    };

    if (fusionId) fetchScript();
  }, [fusionId]);

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-6">
        <Loader2 className="w-16 h-16 text-anime-accent animate-spin" />
        <p className="text-sm font-black uppercase tracking-[0.5em] opacity-40">Initialisation du Player VN...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-12">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => navigate(-1)}
            className="w-12 h-12 bg-white dark:bg-anime-dark-card rounded-2xl flex items-center justify-center shadow-lg hover:scale-110 transition-all border border-black/5 dark:border-white/5"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Film className="w-5 h-5 text-anime-accent" />
              <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Visual Novel Mode</span>
            </div>
            <h1 className="text-5xl font-black italic manga-font leading-none uppercase">LA FORGE <span className="text-anime-accent">VN</span></h1>
          </div>
        </div>

        <div className="bg-white/50 dark:bg-anime-dark-card/50 backdrop-blur-xl p-2 rounded-2xl flex gap-2 border border-black/5 dark:border-white/5 shadow-inner">
          <button 
            onClick={() => setMode('player')}
            className={`px-8 py-3 rounded-xl font-black italic flex items-center gap-2 transition-all ${mode === 'player' ? 'bg-black text-white dark:bg-white dark:text-black shadow-lg' : 'opacity-40 hover:opacity-100'}`}
          >
            <Play className="w-4 h-4" /> Player
          </button>
          <button 
            onClick={() => setMode('director')}
            className={`px-8 py-3 rounded-xl font-black italic flex items-center gap-2 transition-all ${mode === 'director' ? 'bg-black text-white dark:bg-white dark:text-black shadow-lg' : 'opacity-40 hover:opacity-100'}`}
          >
            <Edit3 className="w-4 h-4" /> Director
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-8">
          {mode === 'player' ? (
            <VNPlayer scenes={scenes} />
          ) : (
            <VNDirector scenes={scenes} setScenes={setScenes} onRegenerate={() => {}} />
          )}
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white dark:bg-anime-dark-card rounded-[2.5rem] p-8 shadow-xl border border-black/5 dark:border-white/5">
            <h3 className="text-xl font-black italic manga-font mb-6 flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-anime-accent" /> Infos Production
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-black/5 dark:border-white/5">
                <span className="text-[10px] font-black uppercase opacity-40">Fusion ID</span>
                <span className="text-xs font-mono font-bold">{fusionId?.slice(0, 8)}...</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-black/5 dark:border-white/5">
                <span className="text-[10px] font-black uppercase opacity-40">Scènes</span>
                <span className="text-xs font-bold">{scenes.length}</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-[10px] font-black uppercase opacity-40">Moteur</span>
                <span className="text-xs font-bold text-anime-accent">VN-FORGE v1.0</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-anime-accent to-orange-400 p-8 rounded-[2.5rem] shadow-xl text-black">
             <h4 className="font-black italic text-xl uppercase mb-2">Conseil du Réalisateur</h4>
             <p className="text-sm font-bold opacity-80 leading-relaxed">
               Utilisez le mode Director pour ajuster les dialogues et l'ambiance de chaque scène avant d'exporter votre création.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgeVNPage;


