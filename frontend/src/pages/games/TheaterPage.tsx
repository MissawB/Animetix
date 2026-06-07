import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Film, 
  Play, 
  Sparkles, 
  Clock, 
  User, 
  Heart,
  ChevronRight,
  BookOpen,
  Library
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

const TheaterPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: vns, isLoading, isError } = useQuery<any[]>({
    queryKey: ['theater-list'],
    queryFn: () => apiClient('/api/v1/archetypist/theater/'),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
        </div>
    </div>
  );

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-[10px] font-black uppercase tracking-widest text-red-500 mb-4">
                    <Library className="w-3 h-3" /> Narrative Archive
                </div>
                <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2 leading-none">
                    AI <span className="text-red-500 text-glow">THEATER</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                    Explorez la bibliothèque des Visual Novels générés par la Forge.
                </p>
            </div>
            
            <div className="flex gap-4">
                <Button as={Link} to="/forge/" variant="primary" className="bg-red-600 hover:bg-red-500 border-none py-6 px-10 rounded-2xl shadow-xl hover:scale-105 transition-all">
                    GÉNÉRER MON HISTOIRE
                </Button>
            </div>
        </header>

        {!vns || vns.length === 0 ? (
          <div className="text-center py-32 opacity-20 border-4 border-dashed border-white/5 rounded-[4rem]">
              <Film className="w-24 h-24 mx-auto mb-6" />
              <p className="text-2xl font-black italic manga-font uppercase">Aucun Visual Novel archivé pour le moment</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {vns.map((vn) => (
              <Card key={vn.id} padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-red-500/30 transition-all duration-500 hover:-translate-y-2 flex flex-col">
                <div className="aspect-[16/10] relative overflow-hidden bg-black">
                  {vn.image_url ? (
                    <img src={vn.image_url} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" alt={vn.title_a} />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center opacity-10">
                      <Film className="w-16 h-16 text-white" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
                  
                  {/* Overlay Play Button */}
                  <Link to={`/forge/vn/${vn.id}/`} className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100 no-underline">
                      <div className="w-20 h-20 bg-red-600 rounded-full flex items-center justify-center shadow-[0_0_40px_rgba(220,38,38,0.5)]">
                          <Play className="w-8 h-8 text-white fill-current" />
                      </div>
                  </Link>

                  <Badge variant="primary" className="absolute top-4 right-4 bg-red-600/80 backdrop-blur-md border-none text-[8px] font-black italic">
                      VISUAL NOVEL
                  </Badge>
                </div>
                
                <div className="p-8 space-y-6 flex-grow flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center text-[8px] font-black text-white/40">
                            {vn.creator_name?.[0].toUpperCase() || '?'}
                        </div>
                        <span className="text-[9px] font-black text-white/30 uppercase tracking-widest">{vn.creator_name || 'Anonyme'}</span>
                    </div>
                    <h3 className="font-black italic text-2xl leading-tight mb-4 uppercase manga-font text-white group-hover:text-red-500 transition-colors">
                        {vn.title_a} <span className="text-red-500">×</span> {vn.title_b}
                    </h3>
                    <p className="text-[10px] leading-relaxed opacity-40 uppercase font-bold line-clamp-3 italic">
                        "{vn.scenario_text?.substring(0, 120)}..."
                    </p>
                  </div>

                  <div className="pt-6 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-white/30">
                        <div className="flex items-center gap-1">
                            <Heart className="w-4 h-4" />
                            <span className="text-[10px] font-black">{vn.likes_count || 0}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span className="text-[10px] font-black">5 min</span>
                        </div>
                    </div>
                    <Link to={`/forge/vn/${vn.id}/`} className="no-underline">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-red-500 group-hover:gap-3 transition-all">
                            Jouer <ChevronRight className="w-3 h-3" />
                        </div>
                    </Link>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Legend Box */}
        <div className="mt-32 p-12 rounded-[4rem] bg-navy-900/40 border border-white/5 flex flex-col md:flex-row items-center gap-12 text-center md:text-left">
            <div className="relative">
                <div className="absolute -inset-4 bg-red-600/20 rounded-full blur-2xl animate-pulse"></div>
                <div className="w-24 h-24 bg-gradient-to-br from-red-600 to-orange-600 rounded-3xl flex items-center justify-center -rotate-6 shadow-2xl relative">
                    <BookOpen className="w-12 h-12 text-white" />
                </div>
            </div>
            <div>
                <h4 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter">Director's Cut v4.2</h4>
                <p className="text-sm font-bold opacity-40 uppercase leading-relaxed max-w-3xl italic text-justify">
                    Chaque Visual Novel est une création unique générée par des réseaux de neurones récurrents. Ils s'adaptent dynamiquement à vos choix et peuvent être remixés par la communauté pour explorer des embranchements narratifs alternatifs.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TheaterPage;

