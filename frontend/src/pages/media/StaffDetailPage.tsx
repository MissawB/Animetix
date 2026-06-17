import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Building2, 
  MapPin, 
  Film, 
  Users, 
  ArrowLeft,
  Calendar,
  Globe,
  ExternalLink,
  ShieldCheck,
  Star
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";

import { NotableWork } from '../../types';

const StaffDetailPage: React.FC = () => {
  const { staffId } = useParams<{ staffId: string }>();

  // Use generic media detail for Actor/Staff types
  const { data: staff, isLoading, isError } = useQuery<MediaDetail>({
    queryKey: ['staff-detail', staffId],
    queryFn: () => apiClient(`/api/v1/media/Actor/${staffId}/`),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  if (isError || !staff) return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
          <h2 className="text-4xl font-black italic manga-font text-red-500 mb-6 uppercase">Artiste introuvable</h2>
          <p className="text-gray-500 font-bold uppercase tracking-widest mb-12">Cette fiche semble avoir été purgée du Graphe.</p>
          <Button as={Link} to="/explore/" variant="outline">RETOURNER AU NEXUS</Button>
      </div>
  );

  return (
    <AnimatedPage>
      <div className="absolute inset-0 top-0 h-[400px] overflow-hidden pointer-events-none opacity-10">
          <div className="w-full h-full bg-blue-600 blur-3xl scale-110" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        <Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-12 no-underline group">
            <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Nexus
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
            {/* Sidebar: Bio & Stats */}
            <div className="lg:col-span-4 space-y-8">
                <div className="relative group">
                    <Card padding="none" className="relative overflow-hidden rounded-2xl shadow-2xl border-white/10 aspect-square">
                        {staff.image ? (
                            <img src={staff.image} className="w-full h-full object-cover" alt={staff.title} />
                        ) : (
                            <div className="w-full h-full bg-navy-900 flex items-center justify-center">
                                <Users className="w-24 h-24 opacity-10" />
                            </div>
                        )}
                    </Card>
                    <Badge variant="primary" className="absolute top-6 left-6 shadow-xl bg-emerald-600 font-black italic uppercase tracking-tighter">
                        CRÉATIF
                    </Badge>
                </div>

                <div className="p-6 bg-navy-900/50 rounded-2xl border border-white/5 space-y-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/5 rounded-xl text-white/40">
                            <MapPin className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="text-[10px] font-black opacity-30 uppercase">Origine</p>
                            <p className="font-bold italic text-sm">{staff.metadata?.location || 'Japon'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/5 rounded-xl text-white/40">
                            <Calendar className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="text-[10px] font-black opacity-30 uppercase">Anniversaire</p>
                            <p className="font-bold italic text-sm">{staff.metadata?.birth_date || '?? / ??'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/5 rounded-xl text-white/40">
                            <Globe className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="text-[10px] font-black opacity-30 uppercase">Influence Nexus</p>
                            <p className="font-bold italic text-sm text-emerald-400">High Tier</p>
                        </div>
                    </div>
                </div>

                <Button variant="outline" fullWidth className="py-4 border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10">
                    <Film className="w-3 h-3 mr-2" /> Filmographie Complète
                </Button>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-8 space-y-12">
                <header>
                    <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2 leading-none">
                        {staff.title}
                    </h1>
                    {staff.title_native && <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em] mb-8">{staff.title_native}</p>}
                    
                    <div className="flex flex-wrap gap-3">
                        {staff.metadata?.roles?.map((role: string) => (
                            <Badge key={role} className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-4 py-2 uppercase text-[10px] font-black">{role}</Badge>
                        )) || <Badge className="bg-white/5 text-white/40 border-white/10 px-4 py-2 uppercase text-[10px] font-black">Professionnel de l'industrie</Badge>}
                    </div>
                </header>

                <section>
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-blue-400" /> Biographie
                    </h3>
                    <div className="prose prose-invert max-w-none">
                        <p className="text-lg leading-relaxed opacity-70 font-medium italic">
                            {staff.description || "Biographie en cours de synchronisation avec les serveurs de production."}
                        </p>
                    </div>
                </section>

                {/* Credits / Works */}
                <section>
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Star className="w-4 h-4 text-yellow-400" /> Œuvres Notables
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        {staff.metadata?.notable_works?.map((work: NotableWork) => (
                            <Link key={work.id} to={`/media/${work.type || 'Anime'}/${work.id}/`} className="no-underline group">
                                <Card className="p-4 bg-gray-900/50 border-white/5 group-hover:border-emerald-500/30 transition-all flex items-center gap-4">
                                    <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0">
                                        <img src={work.image || 'https://images.unsplash.com/photo-1614850523296-d8c1af93d400?auto=format&fit=crop&q=80&w=200'} className="w-full h-full object-cover" alt="" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black opacity-30 uppercase mb-1">{work.role || 'Crédit'}</p>
                                        <p className="font-black italic text-sm group-hover:text-emerald-400 transition-colors">{work.title}</p>
                                    </div>
                                </Card>
                            </Link>
                        )) || (
                            <div className="col-span-2 p-12 border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center text-center">
                                <ExternalLink className="w-12 h-12 opacity-10 mb-4" />
                                <p className="text-xs font-bold uppercase opacity-20 tracking-widest">Indexation de la filmographie...</p>
                            </div>
                        )}
                    </div>
                </section>
                
                {/* Reliability / Official Data */}
                <div className="p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl flex items-center gap-6">
                    <ShieldCheck className="w-12 h-12 text-emerald-500 opacity-40" />
                    <div>
                        <h4 className="text-xs font-black uppercase tracking-widest text-emerald-400 mb-1">Source Certifiée Nexus</h4>
                        <p className="text-[10px] text-gray-500 font-bold uppercase">Les données de cet artiste sont validées par le protocole de consensus sémantique.</p>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default StaffDetailPage;
