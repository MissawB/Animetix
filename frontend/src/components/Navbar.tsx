import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { Menu, Shield, Sparkles, Box, FlaskConical, Network, Users } from 'lucide-react';
import { FeatureGate } from './utils/FeatureGate';
import { useTranslation } from 'react-i18next';

const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user } = useAuthStore();
  
  return (
    <nav className="px-6 md:px-12 py-6 flex items-center justify-between sticky top-0 bg-white/80 dark:bg-navy-950/80 backdrop-blur-md z-50 border-b border-gray-100 dark:border-white/5">
      <div className="flex items-center gap-6">
        <button className="bg-black text-white p-2 rounded-xl hover:scale-110 transition lg:hidden" onClick={toggleSidebar}>
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/" className="flex items-center no-underline group">
          <span className="font-black text-2xl italic tracking-tighter group-hover:text-blue-500 transition-colors">ANIMETIX</span>
        </Link>
        <div className="hidden md:flex items-center gap-8 ml-12">
          <Link to="/forge/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-yellow-400 transition-all uppercase tracking-widest">
            <Sparkles className="w-4 h-4 text-yellow-400" /> {t('navbar.forge')}
          </Link>
          <Link to="/latent-space/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
            <Box className="w-4 h-4 text-blue-500" /> {t('navbar.latent')}
          </Link>
          <Link to="/transparency/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-yellow-600 transition-all uppercase tracking-widest">
            <Shield className="w-4 h-4" /> {t('navbar.transparency')}
          </Link>
          
          <Link to="/lab/" className="flex items-center gap-2 no-underline text-xs font-black italic text-red-500 hover:scale-105 transition-all uppercase tracking-widest">
            <FlaskConical className="w-4 h-4" /> {t('navbar.lab', 'Laboratories')}
          </Link>

          {user && (
            <>
              <Link to="/clubs/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
                <Users className="w-4 h-4 text-blue-500" /> {t('navbar.clubs', 'Clubs')}
              </Link>
              <Link to={`/profile/${user.username}/`} className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-orange-500 transition-all uppercase tracking-widest">
                <User className="w-4 h-4 text-orange-500" /> {user.username}
              </Link>
            </>
          )}

          {user?.tier === 'premium' && (
            <Link to="/graph/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-purple-500 transition-all uppercase tracking-widest">
              <Network className="w-4 h-4 text-purple-500" /> Explore Graph
            </Link>
          )}

          {user?.is_staff && (
            <Link to="/admin/dashboard/" className="flex items-center gap-2 no-underline text-xs font-black italic text-cyan-500 hover:scale-105 transition-all uppercase tracking-widest">
              <Settings className="w-4 h-4" /> Admin
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
