import React, { useState, useEffect } from 'react';
import { Users, Search, Plus, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Club {
  id: string;
  name: string;
  description: string;
  theme: string;
  member_count: number;
}

const ClubDiscoveryPage: React.FC = () => {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('All');

  useEffect(() => {
    // Mock fetch - in a real app, this would be an API call
    const fetchClubs = async () => {
      setLoading(true);
      try {
        // Simulating API call
        const response = [
          { id: '1', name: 'Shonen Jump Enthusiasts', description: 'Discussing the latest from WSJ.', theme: 'Shonen', member_count: 120 },
          { id: '2', name: 'Shojo Dreams', description: 'Everything about romance and drama.', theme: 'Shojo', member_count: 85 },
          { id: '3', name: 'Seinen Underground', description: 'Darker themes and complex plots.', theme: 'Seinen', member_count: 210 },
          { id: '4', name: 'Mecha War Room', description: 'Giant robots and tactical combat.', theme: 'Sci-Fi', member_count: 45 },
        ];
        setClubs(response);
      } catch (error) {
        console.error('Failed to fetch clubs', error);
      } finally {
        setLoading(false);
      }
    };
    fetchClubs();
  }, []);

  const filteredClubs = clubs.filter(club => 
    (selectedTheme === 'All' || club.theme === selectedTheme) &&
    (club.name.toLowerCase().includes(filter.toLowerCase()) || club.description.toLowerCase().includes(filter.toLowerCase()))
  );

  const themes = ['All', 'Shonen', 'Shojo', 'Seinen', 'Sci-Fi', 'Slice of Life'];

  return (
    <div className="p-6 max-w-7xl mx-auto min-h-screen bg-gray-50 dark:bg-navy-950">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-black italic uppercase tracking-tighter mb-2">Club Discovery</h1>
          <p className="text-gray-500">Find your community and join the discussion.</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-lg shadow-blue-500/20">
          <Plus className="w-5 h-5" /> Create Club
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-navy-900 p-6 rounded-3xl border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Search className="w-4 h-4" /> Search & Filter
            </h3>
            <div className="space-y-4">
              <input 
                type="text" 
                placeholder="Search clubs..."
                className="w-full bg-gray-100 dark:bg-navy-800 border-none rounded-xl px-4 py-3 text-sm"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">Theme</label>
                <div className="flex flex-wrap gap-2">
                  {themes.map(theme => (
                    <button
                      key={theme}
                      onClick={() => setSelectedTheme(theme)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        selectedTheme === theme 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-100 dark:bg-navy-800 text-gray-500 hover:bg-gray-200 dark:hover:bg-navy-700'
                      }`}
                    >
                      {theme}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Club Grid */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" />
              <p className="text-gray-500 font-bold italic">Gathering communities...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredClubs.map(club => (
                <div key={club.id} className="bg-white dark:bg-navy-900 rounded-3xl border border-gray-100 dark:border-white/5 p-6 hover:shadow-xl transition-all group">
                  <div className="flex items-start justify-between mb-4">
                    <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-2xl text-blue-600">
                      <Users className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 bg-gray-100 dark:bg-navy-800 rounded-full">
                      {club.theme}
                    </span>
                  </div>
                  <h2 className="text-xl font-black italic tracking-tight mb-2 group-hover:text-blue-500 transition-colors">
                    {club.name}
                  </h2>
                  <p className="text-sm text-gray-500 mb-6 line-clamp-2">
                    {club.description}
                  </p>
                  <div className="flex items-center justify-between mt-auto">
                    <span className="text-sm font-bold flex items-center gap-1.5 text-gray-400">
                      <Users className="w-4 h-4" /> {club.member_count} members
                    </span>
                    <Link 
                      to={`/clubs/${club.id}`}
                      className="bg-black dark:bg-white dark:text-black text-white px-6 py-2 rounded-xl font-bold text-sm hover:scale-105 transition-all"
                    >
                      Join
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
          {!loading && filteredClubs.length === 0 && (
            <div className="text-center py-20">
              <p className="text-gray-500">No clubs found matching your criteria.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClubDiscoveryPage;
