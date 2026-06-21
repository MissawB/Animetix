import React, { useState } from 'react';
import { 
  Box, 
  Search, 
  Filter, 
  Maximize2, 
  Trash2, 
  Share2, 
  Download, 
  ArrowLeft,
  Cuboid,
  Sparkles,
  Clock,
  ExternalLink
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

interface Diorama {
  id: string;
  title: string;
  type: 'SGS' | 'DCS';
  preview_url: string;
  created_at: string;
  point_count: number;
  tags: string[];
}

const DioramaGalleryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  
  // Mock Data
  const mockDioramas: Diorama[] = [
    {
      id: '1',
      title: 'La Forge de Guts',
      type: 'SGS',
      preview_url: 'https://images.unsplash.com/photo-1614850523296-d8c1af93d400?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-10T14:30:00Z',
      point_count: 1250000,
      tags: ['Berserk', 'Architecture', 'Dark Fantasy']
    },
    {
      id: '2',
      title: 'Neo-Tokyo Rooftop',
      type: 'DCS',
      preview_url: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-11T09:15:00Z',
      point_count: 5400000,
      tags: ['Cyberpunk', 'Environment', 'Dynamic']
    },
    {
      id: '3',
      title: 'Forêt de Totoro',
      type: 'SGS',
      preview_url: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-12T18:45:00Z',
      point_count: 850000,
      tags: ['Ghibli', 'Nature', 'Atmospheric']
    }
  ];

  const filteredDioramas = mockDioramas.filter(d => 
    d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        {/* Header Decor */}
        <div className="absolute top-0 left-0 w-full h-[300px] bg-gradient-to-b from-blue-600/10 to-transparent pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          {/* Top Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-16">
            <div>
              <Link to="/lab/spatial/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-4 no-underline group">
                <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Retour au Lab Spatial
              </Link>
              <h1 className="text-5xl font-black italic manga-font uppercase tracking-tighter flex items-center gap-4">
                <Cuboid className="w-10 h-10 text-blue-500" />
                Galerie des <span className="text-blue-500">Dioramas</span>
              </h1>
              <p className="text-gray-500 font-bold uppercase tracking-widest mt-2 text-xs">
                Visualisez vos reconstructions volumétriques 3D générées par IA
              </p>
            </div>

            <div className="flex items-center gap-3">
               <div className="relative group">
                  <div className="absolute inset-0 bg-blue-500/20 rounded-xl blur-lg opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="relative bg-navy-900/50 border border-white/10 rounded-xl px-4 py-2 flex items-center gap-3 w-64 backdrop-blur-md">
                    <Search className="w-4 h-4 text-gray-500" />
                    <input 
                      type="text"
                      placeholder="RECHERCHER..."
                      aria-label="Rechercher une reconstruction"
                      className="bg-transparent border-none outline-none text-[10px] font-black uppercase tracking-widest w-full placeholder:opacity-30"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
               </div>
               <Button variant="outline" className="p-3 rounded-xl border-white/10 bg-white/5">
                  <Filter className="w-4 h-4" />
               </Button>
            </div>
          </div>

          {/* Grid */}
          {filteredDioramas.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredDioramas.map((diorama) => (
                <Card key={diorama.id} padding="none" className="group overflow-hidden bg-navy-900/20 border-white/5 hover:border-blue-500/30 transition-all duration-500 shadow-2xl hover:translate-y-[-8px]">
                  {/* Preview Image */}
                  <div className="relative aspect-video overflow-hidden">
                    <img 
                      src={diorama.preview_url} 
                      alt={diorama.title} 
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                      loading="lazy"
                      decoding="async"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#05050a] via-transparent to-transparent opacity-60" />
                    
                    <Badge variant="primary" className={`absolute top-4 left-4 font-black italic uppercase tracking-tighter ${diorama.type === 'SGS' ? 'bg-blue-600' : 'bg-purple-600'}`}>
                      {diorama.type === 'SGS' ? 'STATIC' : 'DYNAMIC'}
                    </Badge>
                    
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <Button variant="primary" className="rounded-full w-14 h-14 p-0 bg-blue-500 border-none shadow-[0_0_20px_rgba(59,130,246,0.5)]">
                        <Maximize2 className="w-6 h-6" />
                      </Button>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-black italic uppercase tracking-tighter line-clamp-1 group-hover:text-blue-400 transition-colors">
                        {diorama.title}
                      </h3>
                      <div className="flex items-center gap-1 text-[8px] font-black opacity-30">
                        <Clock className="w-3 h-3" />
                        {new Date(diorama.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-6">
                      {diorama.tags.map(tag => (
                        <span key={tag} className="text-[8px] font-black uppercase tracking-widest bg-white/5 px-2 py-1 rounded border border-white/5 opacity-50">
                          {tag}
                        </span>
                      ))}
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
                      <div className="flex flex-col">
                        <span className="text-[8px] font-black uppercase opacity-20 tracking-widest">Complexité</span>
                        <span className="text-[10px] font-bold text-blue-400 flex items-center gap-1">
                           <Sparkles className="w-3 h-3" />
                           {(diorama.point_count / 1000000).toFixed(1)}M Points
                        </span>
                      </div>
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-2 hover:bg-white/5 rounded-lg transition-colors opacity-30 hover:opacity-100">
                          <Share2 className="w-4 h-4" />
                        </button>
                        <button className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-lg transition-colors opacity-30 hover:opacity-100">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="py-32 flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-navy-900/50 rounded-full flex items-center justify-center mb-8 border border-white/5">
                <Box className="w-10 h-10 opacity-20" />
              </div>
              <h2 className="text-3xl font-black italic uppercase opacity-20 mb-4">Aucune création trouvée</h2>
              <p className="text-gray-500 font-bold uppercase tracking-widest text-xs mb-8">
                Vous n'avez pas encore généré de dioramas dans le Nexus.
              </p>
              <Button as={Link} to="/lab/spatial/" variant="primary">CRÉER MON PREMIER DIORAMA</Button>
            </div>
          )}

          {/* Footer stats */}
          <div className="mt-24 p-8 rounded-3xl bg-navy-900/10 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center gap-6">
                 <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-500">
                    <Download className="w-8 h-8" />
                 </div>
                 <div>
                    <h4 className="text-lg font-black italic uppercase tracking-tighter">Exporter en VR</h4>
                    <p className="text-xs text-gray-500 font-medium tracking-tight">Téléchargez vos modèles au format .PLY ou .USDZ pour visionnage externe.</p>
                 </div>
              </div>
              <Button variant="outline" className="border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30">
                <ExternalLink className="w-4 h-4 mr-2" /> ACCÉDER AU SDK VR
              </Button>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default DioramaGalleryPage;
