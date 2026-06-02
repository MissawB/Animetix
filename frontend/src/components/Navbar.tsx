import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { 
  Menu, Shield, Sparkles, Box, FlaskConical, Network, Users, Radio, Search, 
  Gamepad2, Film, User, Settings, Sliders, LogOut, LogIn, UserPlus 
} from 'lucide-react';
import { FeatureGate } from './utils/FeatureGate';
import { useTranslation } from 'react-i18next';
import { DynamicAuraWrapper } from './shared/DynamicAuraWrapper';

import { usePersonalizationStore } from '../store/personalizationStore';
import { PersonalizationPanel } from './shared/PersonalizationPanel';

const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user, logout } = useAuthStore();
  const { isPersonalizationEnabled, setPersonalizationEnabled } = usePersonalizationStore();
  const [showPersonalizationPanel, setShowPersonalizationPanel] = React.useState(false);
  
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
          <Link to="/games/hub/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
            <Gamepad2 className="w-4 h-4 text-blue-500" /> Games
          </Link>
          <Link to="/theater/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-red-500 transition-all uppercase tracking-widest">
            <Film className="w-4 h-4 text-red-500" /> Theater
          </Link>
          <Link to="/search/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
            <Search className="w-4 h-4 text-blue-500" /> Search
          </Link>
          <Link to="/social/feed/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-yellow-400 transition-all uppercase tracking-widest">
            <Radio className="w-4 h-4 text-yellow-400" /> Community
          </Link>
          <Link to="/latent-space/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
            <Box className="w-4 h-4 text-blue-500" /> {t('navbar.latent')}
          </Link>
          <Link to="/transparency/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-yellow-600 transition-all uppercase tracking-widest">
            <Shield className="w-4 h-4" /> {t('navbar.transparency')}
          </Link>
          <Link to="/explore/" className="flex items-center gap-2 no-underline text-xs font-black italic text-cyan-400 hover:scale-105 transition-all uppercase tracking-widest">
            <Search className="w-4 h-4" /> Explore
          </Link>
          
          <Link to="/lab/" className="flex items-center gap-2 no-underline text-xs font-black italic text-red-500 hover:scale-105 transition-all uppercase tracking-widest">
            <FlaskConical className="w-4 h-4" /> {t('navbar.lab', 'Laboratories')}
          </Link>

          {user && (
            <>
              <Link to="/clubs/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
                <Users className="w-4 h-4 text-blue-500" /> {t('navbar.clubs', 'Clubs')}
              </Link>
              <div className="relative">
                <div className="flex items-center bg-gray-50 dark:bg-navy-900 rounded-xl p-1 border border-gray-100 dark:border-white/5 shadow-inner">
                  <button 
                    onClick={() => setPersonalizationEnabled(!isPersonalizationEnabled)}
                    className={`p-1.5 rounded-lg transition-all ${!isPersonalizationEnabled ? 'text-gray-400 opacity-50' : 'text-brand-accent animate-pulse bg-white dark:bg-navy-800 shadow-sm'}`}
                    title={isPersonalizationEnabled ? 'Disable Hyper-Personalization' : 'Enable Hyper-Personalization'}
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setShowPersonalizationPanel(!showPersonalizationPanel)}
                    className={`p-1.5 rounded-lg transition-all ${showPersonalizationPanel ? 'text-blue-500 bg-white dark:bg-navy-800 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                    title="Personalization Settings"
                  >
                    <Sliders className="w-4 h-4" />
                  </button>
                </div>

                {showPersonalizationPanel && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowPersonalizationPanel(false)} />
                    <div className="absolute top-full right-0 mt-4 w-80 bg-white dark:bg-navy-950 rounded-2xl shadow-2xl border border-gray-100 dark:border-white/5 p-6 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                      <div className="flex items-center justify-between mb-6">
                        <h4 className="text-sm font-black italic uppercase tracking-widest">Hybrid Control</h4>
                        <button onClick={() => setShowPersonalizationPanel(false)} className="text-gray-400 hover:text-gray-600">
                          <Box className="w-4 h-4 rotate-45" />
                        </button>
                      </div>
                      <PersonalizationPanel />
                    </div>
                  </>
                )}
              </div>
              <DynamicAuraWrapper>
                <Link to={`/profile/${user.username}/`} className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-orange-500 transition-all uppercase tracking-widest px-2 py-1 rounded-lg">
                  <User className="w-4 h-4 text-orange-500" /> {user.username}
                </Link>
              </DynamicAuraWrapper>
              <button onClick={() => logout()} className="flex items-center gap-2 text-xs font-black italic text-red-500 opacity-60 hover:opacity-100 hover:text-red-500 transition-all uppercase tracking-widest">
                <LogOut className="w-4 h-4" />
              </button>
            </>
          )}

          {!user && (
            <div className="flex items-center gap-4 ml-4">
              <Link to="/login" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-blue-500 transition-all uppercase tracking-widest">
                <LogIn className="w-4 h-4 text-blue-500" /> Connexion
              </Link>
              <Link to="/register" className="flex items-center gap-2 no-underline text-xs font-black italic bg-brand-primary text-white hover:scale-105 transition-all uppercase tracking-widest px-4 py-2 rounded-xl">
                <UserPlus className="w-4 h-4" /> S'inscrire
              </Link>
            </div>
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
