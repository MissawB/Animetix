import React, { useState } from 'react';
import { Users, Search, Plus, Loader2, X, Shield, Layout, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { socialService } from '../../features/social/services/socialService';
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { queryClient } from "../../utils/queryClient";

interface Club {
  id: string;
  name: string;
  description: string;
  theme: string;
  member_count: number;
}

const ClubDiscoveryPage: React.FC = () => {
  const [filter, setFilter] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('All');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [newClub, setNewClub] = useState({ name: '', description: '', theme: 'General', is_private: false });

  const { data: clubs = [] } = useQuery<Club[]>({
    queryKey: ['clubs-list'],
    queryFn: () => apiClient('/api/v1/clubs/'),
  });

  const createMutation = useMutation({
    mutationFn: socialService.createClub,
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['clubs-list'] });
        setIsModalOpen(false);
        setNewClub({ name: '', description: '', theme: 'General', is_private: false });
    }
  });

  const filteredClubs = clubs.filter(club => 
    (selectedTheme === 'All' || club.theme === selectedTheme) &&
    (club.name.toLowerCase().includes(filter.toLowerCase()) || club.description.toLowerCase().includes(filter.toLowerCase()))
  );

  const themes = ['All', 'Shonen', 'Shojo', 'Seinen', 'Sci-Fi', 'Slice of Life', 'General'];

  return (
    <div className="p-6 max-w-7xl mx-auto min-h-screen bg-gray-50 dark:bg-navy-950">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-4xl font-black italic uppercase tracking-tighter mb-2 manga-font">Club <span className="text-blue-500">Discovery</span></h1>
          <p className="text-gray-500 font-bold uppercase text-[10px] tracking-widest">Rejoignez une communauté ou créez la vôtre.</p>
        </div>
        <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl font-black italic uppercase transition-all shadow-xl shadow-blue-500/20 hover:scale-105 active:scale-95"
        >
          <Plus className="w-5 h-5" /> Créer un Club
        </button>
      </div>

      {/* Creation Modal */}
      {isModalOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-6 animate-fade-in">
              <Card padding="none" className="w-full max-w-xl bg-navy-900 border-white/10 overflow-hidden rounded-[3rem] shadow-2xl">
                  <div className="p-8 border-b border-white/5 bg-white/5 flex justify-between items-center">
                      <h2 className="text-2xl font-black italic manga-font uppercase">Nouveau Nexus Social</h2>
                      <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-white/5 rounded-xl transition-colors"><X className="w-6 h-6 opacity-30" /></button>
                  </div>
                  <form className="p-10 space-y-8" onSubmit={(e) => { e.preventDefault(); createMutation.mutate(newClub); }}>
                      <div className="space-y-2">
                          <label htmlFor="club-name" className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1">Nom du Club</label>
                          <input
                            id="club-name"
                            required
                            type="text"
                            aria-label="Nom du club"
                            className="w-full bg-black border-2 border-white/5 rounded-2xl py-4 px-6 text-sm font-bold focus:border-blue-500 outline-none transition-all"
                            placeholder="ex: Les Héritiers du Lore"
                            value={newClub.name}
                            onChange={e => setNewClub({...newClub, name: e.target.value})}
                          />
                      </div>
                      <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label htmlFor="club-theme" className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1">Thème Principal</label>
                            <select 
                                id="club-theme"
                                className="w-full bg-black border-2 border-white/5 rounded-2xl py-4 px-6 text-sm font-bold focus:border-blue-500 outline-none transition-all appearance-none"
                                value={newClub.theme}
                                onChange={e => setNewClub({...newClub, theme: e.target.value})}
                            >
                                {themes.filter(t => t !== 'All').map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <span className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1 block">Confidentialité</span>
                            <div className="flex bg-black rounded-2xl p-1 border-2 border-white/5">
                                <button 
                                    type="button"
                                    onClick={() => setNewClub({...newClub, is_private: false})}
                                    className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase transition-all ${!newClub.is_private ? 'bg-blue-600 text-white' : 'text-white/20'}`}
                                >Public</button>
                                <button 
                                    type="button"
                                    onClick={() => setNewClub({...newClub, is_private: true})}
                                    className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase transition-all ${newClub.is_private ? 'bg-red-600 text-white' : 'text-white/20'}`}
                                >Privé</button>
                            </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                          <label htmlFor="club-description" className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1">Description (Lore)</label>
                          <textarea
                            id="club-description"
                            required
                            rows={4}
                            aria-label="Description du club"
                            className="w-full bg-black border-2 border-white/5 rounded-3xl py-4 px-6 text-sm font-bold focus:border-blue-500 outline-none transition-all resize-none"
                            placeholder="Décrivez l'objectif du club..."
                            value={newClub.description}
                            onChange={e => setNewClub({...newClub, description: e.target.value})}
                          />
                      </div>
                      <Button 
                        type="submit" 
                        disabled={createMutation.isPending}
                        variant="primary" 
                        fullWidth 
                        className="py-6 rounded-2xl bg-blue-600 hover:bg-blue-500 border-none shadow-xl"
                      >
                          {createMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "INITIALISER LE CLUB"}
                      </Button>
                  </form>
              </Card>
          </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Filters */}
        <div className="lg:col-span-1 space-y-6">
          <Card padding="lg" className="bg-white dark:bg-navy-900 border-gray-100 dark:border-white/5 shadow-sm h-fit">
            <h3 className="text-[10px] font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
              <Search className="w-4 h-4" /> Nexus Filter
            </h3>
            <div className="space-y-8">
              <div className="space-y-2">
                <label htmlFor="nexus-search" className="sr-only">Rechercher un club</label>
                <input
                  id="nexus-search"
                  type="text"
                  aria-label="Rechercher un club"
                  placeholder="Rechercher un club..."
                  className="w-full bg-gray-100 dark:bg-black/40 border-none rounded-xl px-4 py-4 text-xs font-bold focus:ring-2 ring-blue-500/20"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
              <div className="space-y-4">
                <span className="text-[8px] font-black text-gray-400 uppercase tracking-[0.2em] block">Secteur Thématique</span>
                <div className="flex flex-col gap-2">
                  {themes.map(theme => (
                    <button
                      key={theme}
                      onClick={() => setSelectedTheme(theme)}
                      className={`px-4 py-3 rounded-xl text-left text-[10px] font-black uppercase tracking-widest transition-all ${
                        selectedTheme === theme 
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20 translate-x-2' 
                        : 'bg-gray-100 dark:bg-white/5 text-gray-500 hover:bg-gray-200 dark:hover:bg-white/10'
                      }`}
                    >
                      {theme}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>
          
          <Card padding="lg" className="bg-blue-500/10 border-blue-500/20 text-blue-500/60">
              <Shield className="w-10 h-10 mb-4 opacity-20" />
              <p className="text-[10px] font-bold leading-relaxed uppercase italic">Les clubs privés nécessitent une invitation ou une validation par un officier du cercle.</p>
          </Card>
        </div>

        {/* Club Grid */}
        <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {filteredClubs.map(club => (
                <div key={club.id} className="bg-white dark:bg-navy-900 rounded-[2.5rem] border border-gray-100 dark:border-white/5 p-8 hover:shadow-2xl transition-all group relative overflow-hidden">
                  {/* Decor */}
                  <Layout className="absolute -right-8 -bottom-8 w-40 h-40 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity rotate-12" />
                  
                  <div className="flex items-start justify-between mb-6">
                    <div className="bg-blue-100 dark:bg-blue-500/10 p-4 rounded-2xl text-blue-600 group-hover:scale-110 transition-transform">
                      <Users className="w-8 h-8" />
                    </div>
                    <Badge variant="neutral" className="bg-gray-100 dark:bg-white/5 text-[8px] font-black uppercase tracking-widest">
                      {club.theme}
                    </Badge>
                  </div>
                  <h2 className="text-2xl font-black italic tracking-tight mb-3 uppercase manga-font group-hover:text-blue-500 transition-colors leading-none">
                    {club.name}
                  </h2>
                  <p className="text-xs font-medium text-gray-500 mb-8 line-clamp-2 uppercase tracking-wide opacity-60 italic">
                    "{club.description}"
                  </p>
                  <div className="flex items-center justify-between mt-auto pt-6 border-t border-gray-50 dark:border-white/5">
                    <span className="text-[10px] font-black flex items-center gap-2 text-gray-400 uppercase tracking-widest">
                      <Sparkles className="w-3 h-3 text-blue-400" /> {club.member_count} Membres
                    </span>
                    <Link 
                      to={`/clubs/${club.id}`}
                      className="bg-black dark:bg-white dark:text-black text-white px-8 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest hover:scale-105 transition-all shadow-xl no-underline"
                    >
                      Rejoindre
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          
          {filteredClubs.length === 0 && (
            <div className="text-center py-32 opacity-10 border-4 border-dashed border-white/5 rounded-[4rem]">
              <Users className="w-24 h-24 mx-auto mb-6" />
              <p className="text-2xl font-black italic manga-font uppercase">Aucun Nexus actif dans ce secteur</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClubDiscoveryPage;


