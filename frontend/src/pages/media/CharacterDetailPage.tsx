import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  User,
  Play,
  Fingerprint, 
  Network, 
  ArrowLeft,
  Sparkles,
  Info,
  TrendingUp
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";

import { Appearance, Seiyuu } from '../../types';

const CharacterDetailPage: React.FC = () => {
  const { characterId } = useParams<{ characterId: string }>();

  // In a real scenario, this would call a dedicated endpoint like /api/v1/media/Character/:id/
  // For now, we use the media detail endpoint which handles the generic MediaItem model
  const { data: character, isLoading, isError } = useQuery({
    queryKey: ['character-detail', characterId],
    queryFn: () => apiClient(`/api/v1/media/Character/${characterId}/`),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  if (isError || !character) return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
          <h2 className="text-4xl font-black italic manga-font text-red-500 mb-6 uppercase">Personnage introuvable</h2>
          <p className="text-gray-500 font-bold uppercase tracking-widest mb-12">Il semble s'être perdu dans l'espace latent...</p>
          <Button as={Link} to="/explore/" variant="outline">RETOURNER AU NEXUS</Button>
      </div>
  );

  return (
    <AnimatedPage>
      {/* Background Decor */}
      <div className="absolute inset-0 top-0 h-[600px] overflow-hidden pointer-events-none opacity-20">
          <img src={character.image} className="w-full h-full object-cover blur-3xl scale-110" alt="" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-950 to-navy-950" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        <Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-12 no-underline group">
            <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Nexus
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
            {/* Image & Key Attributes */}
            <div className="lg:col-span-4 space-y-8">
                <div className="relative group">
                    <div className="absolute -inset-2 bg-gradient-to-br from-anime-accent to-purple-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                    <Card padding="none" className="relative overflow-hidden rounded-2xl shadow-2xl border-white/10">
                        <img src={character.image} className="w-full aspect-[3/4] object-cover" alt={character.title} />
                    </Card>
                    <Badge variant="primary" className="absolute top-6 left-6 shadow-xl bg-anime-accent font-black italic uppercase tracking-tighter">
                        CHARACTÈRES
                    </Badge>
                </div>

                <div className="space-y-4">
                    <div className="p-6 bg-navy-900/50 rounded-2xl border border-white/5 space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black opacity-30 uppercase">Archétype</span>
                            <span className="font-bold italic text-sm text-anime-accent">{character.metadata?.archetype || 'Analytique'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black opacity-30 uppercase">Alignement</span>
                            <span className="font-bold italic text-sm text-blue-400">{character.metadata?.alignment || 'Neutre Bon'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black opacity-30 uppercase">Popularité</span>
                            <span className="font-bold italic text-sm flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" /> #{character.popularity || '??'}
                            </span>
                        </div>
                    </div>
                    
                    <Button variant="outline" fullWidth className="py-4 border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10">
                        <Network className="w-3 h-3 mr-2" /> Analyser dans le Graphe
                    </Button>
                </div>
            </div>

            {/* Profile Content */}
            <div className="lg:col-span-8 space-y-12">
                <header>
                    <div className="flex flex-wrap gap-2 mb-6">
                        {character.metadata?.traits?.map((t: string) => (
                            <Badge key={t} variant="neutral" className="bg-white/5 border-white/10 text-[9px] uppercase tracking-widest font-black italic">{t}</Badge>
                        )) || <Badge variant="neutral" className="bg-white/5 border-white/10 text-[9px] uppercase tracking-widest font-black italic">Personnage Nexus</Badge>}
                    </div>
                    <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2 leading-none text-glow">
                        {character.title}
                    </h1>
                    {character.title_native && <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em] mb-4">{character.title_native}</p>}
                </header>

                {/* Bio Section */}
                <section>
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Info className="w-4 h-4 text-blue-400" /> Profil Cognitif
                    </h3>
                    <Card padding="lg" className="bg-white/5 border-white/5 shadow-inner">
                        <p className="text-sm leading-relaxed opacity-80 font-medium italic">
                            {character.description || "Les archives du Nexus n'ont pas encore indexé la biographie complète de ce sujet."}
                        </p>
                    </Card>
                </section>

                {/* Linked Media / Appearances */}
                <section>
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Play className="w-4 h-4 text-emerald-400" /> Apparitions majeures
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        {character.metadata?.appearances?.map((app: Appearance) => (
                            <Link key={app.id} to={`/media/Anime/${app.id}/`} className="no-underline group">
                                <Card className="p-4 bg-gray-900/50 border-white/5 group-hover:border-anime-accent/30 transition-all flex items-center gap-4">
                                    <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0">
                                        <img src={app.image || 'https://images.unsplash.com/photo-1614850523296-d8c1af93d400?auto=format&fit=crop&q=80&w=200'} className="w-full h-full object-cover" alt="" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black opacity-30 uppercase mb-1">Anime</p>
                                        <p className="font-black italic text-sm group-hover:text-anime-accent transition-colors">{app.title}</p>
                                    </div>
                                </Card>
                            </Link>
                        )) || (
                            <div className="col-span-2 p-12 border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center text-center">
                                <Fingerprint className="w-12 h-12 opacity-10 mb-4" />
                                <p className="text-xs font-bold uppercase opacity-20 tracking-widest">Calcul des relations en cours...</p>
                            </div>
                        )}
                    </div>
                </section>

                {/* Voice Actors (Seiyuu) */}
                {character.metadata?.seiyuu && (
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-yellow-400" /> Voix Originale (Seiyuu)
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            {character.metadata.seiyuu.map((actor: Seiyuu) => (
                                <Link key={actor.id} to={`/staff/${actor.id}/`} className="no-underline group">
                                    <Card className="p-4 bg-gray-900/50 border-white/5 group-hover:border-yellow-500/30 transition-all flex items-center gap-4">
                                        <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0 bg-yellow-500/10 flex items-center justify-center">
                                            <User className="w-8 h-8 opacity-20" />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-black opacity-30 uppercase mb-1">Seiyuu</p>
                                            <p className="font-black italic text-sm group-hover:text-yellow-400 transition-colors">{actor.name}</p>
                                        </div>
                                    </Card>
                                </Link>
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default CharacterDetailPage;
