import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { 
  Menu, Shield, Sparkles, Box, Network, Users, Search, 
  Gamepad2, User, Sliders, LogOut, LogIn, UserPlus, Bell,
  HelpCircle, Zap
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
    <nav className="px-6 md:px-12 py-4 flex items-center justify-between sticky top-0 bg-[#fffcf0] dark:bg-[#1a1a2e] z-[1000] border-b border-black/5 dark:border-white/5 transition-colors duration-500">
      <div className="flex items-center gap-6">
        <button 
          className="bg-black text-white p-3 rounded-2xl hover:scale-110 active:scale-95 transition shadow-lg" 
          onClick={() => toggleSidebar()}
          aria-label={t('nav.toggle_sidebar', 'Toggle Sidebar')}
        >
          <Menu className="w-6 h-6" />
        </button>
        <Link to="/" className="flex items-center no-underline">
          <img src="/static/img/logo/white_logo.png" alt="Logo" className="h-8 dark:hidden" />
          <img src="/static/img/logo/logo.png" alt="Logo" className="h-8 hidden dark:block" />
        </Link>
      </div>

      <div className="hidden lg:flex flex-wrap items-center justify-center gap-x-8 gap-y-2 flex-grow mx-8">
          <Link to="/games/hub/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 transition-all uppercase tracking-widest">
            <Gamepad2 className="w-4 h-4" /> {t('nav.games', 'Jeux')}
          </Link>
          <Link to="/search/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-cyan-500 dark:hover:text-cyan-400 transition-all uppercase tracking-widest">
            <Search className="w-4 h-4" /> {t('nav.search', 'Recherche')}
          </Link>
          <Link to="/social/dashboard/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-orange-500 dark:hover:text-orange-400 transition-all uppercase tracking-widest">
            <Users className="w-4 h-4" /> {t('nav.community', 'Communauté')}
          </Link>
          <Link to="/lab/latent-space/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-indigo-500 dark:hover:text-indigo-400 transition-all uppercase tracking-widest">
            <Network className="w-4 h-4" /> {t('navbar.latent', 'Espace Latent')}
          </Link>
          <Link to="/lab/forge-hub/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-purple-500 dark:hover:text-purple-400 transition-all uppercase tracking-widest">
            <Sparkles className="w-4 h-4" /> {t('nav.forge', 'Forge Créative')}
          </Link>
      </div>

      <div className="flex items-center gap-4 shrink-0">
          {user ? (
            <>
              {/* Solde de Berrix (Bx) */}
              <Link to="/power-station/" className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-xl transition-all no-underline group shadow-sm">
                <Zap className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform fill-current" />
                <span className="text-[11px] font-black italic manga-font text-blue-500">
                  {user.wallet_balance?.toLocaleString() || 0} <span className="text-[8px] opacity-70">Bx</span>
                </span>
              </Link>

              <div className="hidden md:flex items-center bg-gray-50 dark:bg-black/20 rounded-xl p-1 border border-black/5 dark:border-white/5 shadow-inner">
                <button 
                  onClick={() => setPersonalizationEnabled(!isPersonalizationEnabled)}
                  className={`p-1.5 rounded-lg transition-all ${!isPersonalizationEnabled ? 'text-gray-400 opacity-50' : 'text-brand-accent animate-pulse bg-white dark:bg-white/10 shadow-sm'}`}
                  title={isPersonalizationEnabled ? 'Disable Hyper-Personalization' : 'Enable Hyper-Personalization'}
                  aria-label={isPersonalizationEnabled ? 'Disable Hyper-Personalization' : 'Enable Hyper-Personalization'}
                >
                  <Sparkles className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => setShowPersonalizationPanel(!showPersonalizationPanel)}
                  className={`p-1.5 rounded-lg transition-all ${showPersonalizationPanel ? 'text-blue-500 bg-white dark:bg-white/10 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                  title="Personalization Settings"
                  aria-label="Personalization Settings"
                >
                  <Sliders className="w-4 h-4" />
                </button>
              </div>

              {showPersonalizationPanel && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowPersonalizationPanel(false)}
                    onKeyDown={(e) => { if (e.key === 'Escape' || e.key === 'Enter') setShowPersonalizationPanel(false); }}
                    role="button"
                    tabIndex={-1}
                    aria-label="Close personalization panel"
                  />
                  <div className="absolute top-full right-0 mt-4 w-80 bg-white dark:bg-[#0f0f1a] rounded-2xl shadow-2xl border border-black/5 dark:border-white/5 p-6 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="flex items-center justify-between mb-6">
                      <h4 className="text-sm font-black italic uppercase tracking-widest text-black dark:text-white">{t('personalization.title', 'Hybrid Control')}</h4>
                      <button 
                        onClick={() => setShowPersonalizationPanel(false)} 
                        className="text-gray-400 hover:text-blue-500 transition-colors"
                        aria-label="Close"
                      >
                        <Box className="w-4 h-4 rotate-45" />
                      </button>
                    </div>
                    <PersonalizationPanel />
                  </div>
                </>
              )}

              <Link to="/notifications" className="relative text-gray-400 hover:text-blue-500 transition-colors hidden sm:block" aria-label="Notifications">
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>

              <Link to="/support" className="text-gray-400 hover:text-cyan-500 transition-colors hidden sm:block" title="Support Technique" aria-label="Support Technique">
                <HelpCircle className="w-5 h-5" />
              </Link>

              {user?.is_staff && (
                <Link to="/admin/dashboard/" className="flex items-center gap-2 no-underline text-[10px] font-black italic text-cyan-500 hover:scale-105 transition-all uppercase tracking-widest px-3 py-1.5 bg-cyan-500/10 rounded-xl border border-cyan-500/20">
                  <Shield className="w-4 h-4" /> Admin
                </Link>
              )}
              
              <DynamicAuraWrapper>
                <Link to={`/profile/${user.username}/`} className="flex items-center gap-2 no-underline text-xs font-black italic text-black dark:text-white hover:text-orange-500 transition-all uppercase tracking-widest px-3 py-1.5 bg-gray-50 dark:bg-white/5 rounded-xl shadow-sm border border-gray-100 dark:border-white/5">
                  <User className="w-4 h-4 text-orange-500" /> <span className="hidden sm:inline">{user.username}</span>
                </Link>
              </DynamicAuraWrapper>
              
              <button 
                onClick={() => logout()} 
                className="flex items-center gap-2 text-xs font-black italic text-red-500 opacity-60 hover:opacity-100 hover:text-red-500 transition-all uppercase tracking-widest p-2 bg-red-500/10 rounded-xl"
                aria-label={t('auth.logout', 'Logout')}
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/auth/login/" className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 dark:text-gray-400 hover:text-blue-500 transition-all uppercase tracking-widest">
                <LogIn className="w-4 h-4 text-blue-500" /> <span className="hidden sm:inline">{t('auth.login', 'Connexion')}</span>
              </Link>
              <Link to="/auth/register/" className="flex items-center gap-2 no-underline text-[10px] sm:text-xs font-black italic bg-black dark:bg-white text-white dark:text-black hover:scale-105 active:scale-95 transition-all uppercase tracking-widest px-4 py-2 rounded-xl shadow-lg border-b-2 border-gray-800 dark:border-gray-300">
                <UserPlus className="w-4 h-4" /> <span className="hidden sm:inline">{t('auth.register', "S'inscrire")}</span>
              </Link>
            </div>
          )}
      </div>
    </nav>
  );
};

export default Navbar;
