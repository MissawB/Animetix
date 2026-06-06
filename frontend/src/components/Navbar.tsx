import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { 
  Menu, Shield, Sparkles, Box, FlaskConical, Network, Users, Radio, Search, 
  Gamepad2, Film, User, Settings, Sliders, LogOut, LogIn, UserPlus, Bell, Zap,
  Compass, BrainCircuit, Eye
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DynamicAuraWrapper } from './shared/DynamicAuraWrapper';

import { usePersonalizationStore } from '../store/personalizationStore';
import { useNotificationStore } from '../store/notificationStore';
import { PersonalizationPanel } from './shared/PersonalizationPanel';

const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user, logout } = useAuthStore();
  const { isPersonalizationEnabled, setPersonalizationEnabled } = usePersonalizationStore();
  const { unreadCount } = useNotificationStore();
  const [showPersonalizationPanel, setShowPersonalizationPanel] = React.useState(false);
  
  return (
    <nav className="px-6 md:px-12 py-4 flex items-center justify-between sticky top-0 bg-white/80 dark:bg-navy-950/80 backdrop-blur-md z-50 border-b border-gray-100 dark:border-white/5">
      <div className="flex items-center gap-6">
        <button className="bg-black text-white p-2 rounded-xl hover:scale-110 active:scale-95 transition shadow-lg lg:hidden" onClick={() => toggleSidebar()}>
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/" className="flex items-center no-underline group">
          <span className="font-black text-2xl italic tracking-tighter manga-font text-black dark:text-white group-hover:text-blue-500 transition-colors">ANIMETIX</span>
        </Link>
      </div>

      <div className="hidden lg:flex flex-wrap items-center justify-center gap-x-6 gap-y-2 flex-grow mx-8">
          <Link to="/games/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 transition-all uppercase tracking-widest">
            <Gamepad2 className="w-4 h-4" /> Games
          </Link>
          <Link to="/theater/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-rose-500 dark:hover:text-rose-400 transition-all uppercase tracking-widest">
            <Film className="w-4 h-4" /> Theater
          </Link>
          <Link to="/search/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-cyan-500 dark:hover:text-cyan-400 transition-all uppercase tracking-widest">
            <Search className="w-4 h-4" /> Universal Search
          </Link>
          <Link to="/explore/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 transition-all uppercase tracking-widest">
            <Compass className="w-4 h-4" /> Explore
          </Link>
          <Link to="/social/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-orange-500 dark:hover:text-orange-400 transition-all uppercase tracking-widest">
            <Users className="w-4 h-4" /> Community
          </Link>
          {user && (
            <Link to="/social/friends/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-pink-500 dark:hover:text-pink-400 transition-all uppercase tracking-widest">
              <UserPlus className="w-4 h-4" /> Friends
            </Link>
          )}
          <Link to="/latent-space/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-indigo-500 dark:hover:text-indigo-400 transition-all uppercase tracking-widest">
            <Network className="w-4 h-4" /> Latent Space
          </Link>
          <Link to="/forge-hub/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-purple-500 dark:hover:text-purple-400 transition-all uppercase tracking-widest">
            <Sparkles className="w-4 h-4" /> Forge Créative
          </Link>
          <Link to="/lab/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-green-500 dark:hover:text-green-400 transition-all uppercase tracking-widest">
            <FlaskConical className="w-4 h-4" /> Beta Lab
          </Link>
          <Link to="/social/nexus/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-fuchsia-500 dark:hover:text-fuchsia-400 transition-all uppercase tracking-widest">
            <BrainCircuit className="w-4 h-4" /> Nexus Pro
          </Link>
          <Link to="/transparence/" className="flex items-center gap-2 no-underline text-[11px] font-black italic text-gray-500 dark:text-gray-400 hover:text-slate-500 dark:hover:text-slate-400 transition-all uppercase tracking-widest">
            <Eye className="w-4 h-4" /> Transparence
          </Link>
      </div>

      <div className="flex items-center gap-4 shrink-0">
          {user ? (
            <>
              <div className="hidden md:flex items-center bg-gray-50 dark:bg-navy-900 rounded-xl p-1 border border-gray-100 dark:border-white/5 shadow-inner">
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

              <Link to="/notifications" className="relative text-gray-400 hover:text-blue-500 transition-colors hidden sm:block">
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>
              
              <DynamicAuraWrapper>
                <Link to={`/profile/${user.username}/`} className="flex items-center gap-2 no-underline text-xs font-black italic text-black dark:text-white hover:text-orange-500 transition-all uppercase tracking-widest px-3 py-1.5 bg-gray-50 dark:bg-white/5 rounded-xl shadow-sm border border-gray-100 dark:border-white/5">
                  <User className="w-4 h-4 text-orange-500" /> <span className="hidden sm:inline">{user.username}</span>
                </Link>
              </DynamicAuraWrapper>
              
              <button onClick={() => logout()} className="flex items-center gap-2 text-xs font-black italic text-red-500 opacity-60 hover:opacity-100 hover:text-red-500 transition-all uppercase tracking-widest p-2 bg-red-500/10 rounded-xl">
                <LogOut className="w-4 h-4" />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/auth/login/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-blue-500 transition-all uppercase tracking-widest">
                <LogIn className="w-4 h-4 text-blue-500" /> <span className="hidden sm:inline">Connexion</span>
              </Link>
              <Link to="/auth/register/" className="flex items-center gap-2 no-underline text-[10px] sm:text-xs font-black italic bg-black dark:bg-white text-white dark:text-black hover:scale-105 active:scale-95 transition-all uppercase tracking-widest px-4 py-2 rounded-xl shadow-lg border-b-2 border-gray-800 dark:border-gray-300">
                <UserPlus className="w-4 h-4" /> <span className="hidden sm:inline">S'inscrire</span>
              </Link>
            </div>
          )}
      </div>
    </nav>
  );
};

export default Navbar;
