import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Users, UserPlus, Search, UserMinus, ChevronRight } from 'lucide-react';
import { searchUsers } from '../../api';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Link } from 'react-router-dom';
import { User } from "../../types";
import { useToastStore } from "../../store/toastStore";
import { useSocialDashboard } from "../../features/social/hooks/useSocialDashboard";

const SocialHubPage: React.FC = () => {
  const { t } = useTranslation();
  const { addToast } = useToastStore();
  const { data: dashboardData, isLoading: isDashboardLoading, toggleFollow } = useSocialDashboard();
  
  const [searchResults, setSearchUsers] = useState<(User & { is_following: boolean })[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'following' | 'followers' | 'discovery'>('following');

  const following = dashboardData?.following || [];
  const followers = dashboardData?.followers || [];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.length < 2) return;
    try {
      const results = await searchUsers(searchQuery);
      setSearchUsers(results);
      setActiveTab('discovery');
    } catch (err) {
      addToast("Erreur lors de la recherche.", "error");
    }
  };

  const handleToggleFollow = async (userId: number) => {
    try {
      toggleFollow(userId, {
        onSuccess: () => {
          addToast("Action effectuée avec succès !", "success");
          if (activeTab === 'discovery') {
            // Optimistic or manual update of search results if needed
            setSearchUsers(prev => prev.map(u => u.id === userId ? { ...u, is_following: !u.is_following } : u));
          }
        },
        onError: () => {
          addToast("Action impossible.", "error");
        }
      });
    } catch (err) {
      addToast("Action impossible.", "error");
    }
  };

  if (isDashboardLoading) {
    return <div className="p-20 text-center animate-pulse font-black uppercase tracking-widest">Initialisation du réseau social...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase flex items-center gap-3">
            <Users className="w-10 h-10 text-yellow-500" /> HUB SOCIAL
          </h1>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mt-2">
            Gérez vos connexions, découvrez de nouveaux héros et restez informé.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="w-full md:w-96 relative">
          <input
            type="text"
            placeholder="Rechercher un utilisateur..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white dark:bg-navy-900 border-2 border-transparent focus:border-yellow-500 rounded-2xl px-6 py-4 outline-none font-bold shadow-sm transition-all pr-12"
          />
          <button type="submit" className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-yellow-500 transition-colors">
            <Search className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-8 overflow-x-auto pb-2 no-scrollbar">
        {[
          { id: 'following', label: 'Abonnements', count: following.length },
          { id: 'followers', label: 'Abonnés', count: followers.length },
          { id: 'discovery', label: 'Découverte', count: searchResults.length }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-6 py-3 rounded-xl font-black uppercase text-xs tracking-widest transition-all whitespace-nowrap ${
              activeTab === tab.id 
                ? 'bg-yellow-500 text-white shadow-lg' 
                : 'bg-white dark:bg-navy-900 text-gray-500 hover:bg-gray-50 dark:hover:bg-navy-800'
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {activeTab === 'following' && following.map(item => (
          <Card key={item.id} padding="md" className="group hover:border-yellow-500/30 transition-all">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white font-black text-xl italic">
                {item.username[0]}
              </div>
              <div className="flex-1">
                <Link to={`/profile/${item.username}/`} className="font-black uppercase tracking-tight hover:text-yellow-500 transition-colors no-underline">
                  {item.username}
                </Link>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] bg-gray-100 dark:bg-navy-800 px-2 py-0.5 rounded text-gray-500 font-black uppercase">Niv. {item.level}</span>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => handleToggleFollow(item.to_user)} className="text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white">
                <UserMinus className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        ))}

        {activeTab === 'followers' && followers.map(item => (
          <Card key={item.id} padding="md">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white font-black text-xl italic">
                {item.username[0]}
              </div>
              <div className="flex-1">
                <Link to={`/profile/${item.username}/`} className="font-black uppercase tracking-tight hover:text-blue-500 transition-colors no-underline">
                  {item.username}
                </Link>
                <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Vous suit</p>
              </div>
              <Link to={`/profile/${item.username}/`} className="text-gray-400 hover:text-blue-500">
                <ChevronRight className="w-5 h-5" />
              </Link>
            </div>
          </Card>
        ))}

        {activeTab === 'discovery' && searchResults.map(user => (
          <Card key={user.id} padding="md" className="border-2 border-transparent hover:border-yellow-500/20">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-navy-800 flex items-center justify-center font-black text-xl italic">
                {user.username[0]}
              </div>
              <div className="flex-1">
                <Link to={`/profile/${user.username}/`} className="font-black uppercase tracking-tight hover:text-yellow-500 transition-colors no-underline">
                  {user.username}
                </Link>
                <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Niveau {user.level || 1}</p>
              </div>
              <Button 
                variant={user.is_following ? "outline" : "primary"} 
                size="sm" 
                onClick={() => handleToggleFollow(user.id)}
              >
                {user.is_following ? <UserMinus className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
              </Button>
            </div>
          </Card>
        ))}

        {/* Empty States */}
        {((activeTab === 'following' && following.length === 0) || 
          (activeTab === 'followers' && followers.length === 0) ||
          (activeTab === 'discovery' && searchResults.length === 0)) && (
          <div className="col-span-full py-20 text-center opacity-40">
            <Users className="w-16 h-12 mx-auto mb-4" />
            <p className="font-black uppercase tracking-widest text-sm">Rien à afficher ici pour le moment.</p>
          </div>
        )}

      </div>
    </div>
  );
};

export default SocialHubPage;


