import React, { ReactNode, useEffect } from 'react';
import Navbar from './Navbar';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, Link } from 'react-router-dom';
import { queryClient } from '../utils/queryClient';
import { useCustomConfig } from '../features/utils/hooks/useCustomConfig';
import { pageVariants } from './ui/animations';
import CompanionOverlay from '../features/companion/CompanionOverlay';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { useTranslation } from 'react-i18next';
import { 
  Menu, X, Home, Zap, Trophy, BookOpen, Settings, Sun, Moon, Monitor, 
  CheckCircle2, Shield, User, Globe, Sparkles, Gamepad2, Search, Compass, 
  Network, Film, Users, UserPlus, FlaskConical, BrainCircuit, Eye, LogIn
} from 'lucide-react';

const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <footer className="p-12 text-center text-gray-500 dark:text-gray-400">
      <p className="manga-font text-[10px] tracking-[0.3em] mb-3">
        {t('footer.powered_by', 'Powered by Animetix IA & React 19')}
      </p>
      <p className="text-xs italic opacity-60">
        &copy; 2026 Animetix Team. All rights reserved.
      </p>
    </footer>
  );
};

interface LayoutProps {
  children: ReactNode;
}

const LayoutContent: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { config } = useCustomConfig();
  const location = useLocation();
  const { t } = useTranslation();
  
  const { 
    isSidebarOpen, isSettingsOpen, theme, mediaType, difficulty, currentLang,
    toggleSidebar, toggleSettings, setTheme, setMediaType, setDifficulty, setCurrentLang 
  } = useUIStore();
  
  const { user, isAuthenticated } = useAuthStore();

  // Sync theme
  useEffect(() => {
    const html = document.documentElement;
    const actualTheme = theme === 'auto' 
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;

    if (actualTheme === 'dark') {
      html.classList.add('dark');
      html.setAttribute('data-bs-theme', 'dark');
    } else {
      html.classList.remove('dark');
      html.setAttribute('data-bs-theme', 'light');
    }
  }, [theme]);

  // Sync visual themes from user custom config
  useEffect(() => {
    if (config?.visual_theme) {
      const themes = ['theme-naruto', 'theme-manga-classic'];
      document.documentElement.classList.remove(...themes);
      if (config.visual_theme !== 'default') {
        document.documentElement.classList.add(`theme-${config.visual_theme}`);
      }
    }
  }, [config?.visual_theme]);

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-500">
      
      {/* OVERLAY (Visible when sidebar or settings drawer is open) */}
      {(isSidebarOpen || isSettingsOpen) && (
        <div 
          id="sidebar-overlay" 
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1500]" 
          onClick={() => { toggleSidebar(true); toggleSettings(true); }}
        />
      )}

      {/* SIDEBAR (DRAWER - LEFT) */}
      <aside 
        id="manga-sidebar" 
        className={`fixed left-0 top-0 h-screen w-[300px] bg-[#fffcf0] dark:bg-[#1a1a2e] z-[2000] flex flex-col p-8 overflow-y-auto transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[20px_0_50px_rgba(0,0,0,0.1)] border-r border-gray-100 dark:border-white/5 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="mb-12 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="manga-font text-2xl tracking-tighter text-black dark:text-white">
              {t('nav.menu', 'MENU')}
            </span>
          </div>
          <button 
            className="text-3xl hover:rotate-90 transition-transform duration-300 text-black dark:text-white" 
            onClick={() => toggleSidebar(true)}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {isAuthenticated && user && (
          <div className="mb-10 bg-white/50 dark:bg-black/20 p-5 rounded-3xl shadow-xl border border-gray-100 dark:border-white/5">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-yellow-400 text-black rounded-2xl flex items-center justify-center font-black italic border-2 border-black transform rotate-3 text-xl shadow-md">
                {user.username?.[0]?.toUpperCase()}
              </div>
              <div>
                <p className="manga-font text-sm m-0 text-black dark:text-white">{user.username}</p>
                <p className="text-[10px] font-bold text-yellow-600 dark:text-yellow-400 uppercase m-0">
                  {user.tier === 'premium' ? 'Premium' : 'Explorateur'}
                </p>
              </div>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-yellow-400 h-full shadow-[0_0_10px_#fdb913]" 
                style={{ width: `${((user.xp ?? 0) % 500) / 500 * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-2 font-black text-[10px] opacity-40 text-black dark:text-white">
              <span>{user.xp ?? 0} XP</span>
              <span>NIV. {Math.max(1, Math.floor((user.xp ?? 0) / 500))}</span>
            </div>
          </div>
        )}

        <nav className="flex-grow space-y-1 pb-10">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-4">Principal</p>
          <Link to="/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Home className="w-4 h-4" /> Accueil
          </Link>
          <Link to="/daily-challenge/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/daily-challenge/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Zap className="w-4 h-4 text-yellow-400 fill-current animate-pulse" /> Défi Quotidien
          </Link>
          <Link to="/games/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname.startsWith('/game') ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Gamepad2 className="w-4 h-4 text-blue-400" /> Games
          </Link>
          <Link to="/theater/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/theater/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Film className="w-4 h-4 text-rose-400" /> Theater
          </Link>

          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">Exploration</p>
          <Link to="/search/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/search/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Search className="w-4 h-4 text-cyan-400" /> Universal Search
          </Link>
          <Link to="/explore/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Compass className="w-4 h-4 text-emerald-400" /> Explore
          </Link>
          <Link to="/latent-space/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/latent-space/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Network className="w-4 h-4 text-indigo-400" /> Latent Space
          </Link>

          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">Communauté</p>
          <Link to="/social/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Users className="w-4 h-4 text-orange-400" /> Community
          </Link>
          {isAuthenticated && (
            <Link to="/friends/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/friends/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
              <UserPlus className="w-4 h-4 text-pink-400" /> Friends
            </Link>
          )}
          <Link to="/leaderboard/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/leaderboard/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Trophy className="w-4 h-4 text-yellow-500" /> Classement
          </Link>

          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">Labs & Création</p>
          <Link to="/forge-hub/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/forge-hub/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Sparkles className="w-4 h-4 text-purple-400" /> Forge Créative
          </Link>
          <Link to="/lab/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname.startsWith('/lab') ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <FlaskConical className="w-4 h-4 text-green-400" /> Beta Lab
          </Link>
          <Link to="/social/nexus/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/nexus/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <BrainCircuit className="w-4 h-4 text-fuchsia-400" /> Nexus Pro
          </Link>
          <Link to="/transparence/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/transparence/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
            <Eye className="w-4 h-4 text-slate-400" /> Transparence
          </Link>

          {!isAuthenticated && (
            <>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">Compte</p>
              <Link to="/auth/login/" onClick={() => toggleSidebar(true)} className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-blue-500/10 dark:hover:bg-blue-500/20">
                <LogIn className="w-4 h-4 text-blue-500" /> Connexion
              </Link>
              <Link to="/auth/register/" onClick={() => toggleSidebar(true)} className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-green-500/10 dark:hover:bg-green-500/20">
                <UserPlus className="w-4 h-4 text-green-500" /> S'inscrire
              </Link>
            </>
          )}
          
          <div className="pt-8">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('nav.univers', 'Univers')}</p>
            <div className="grid grid-cols-3 gap-2 p-1 bg-white/50 dark:bg-black/20 rounded-2xl border border-gray-100 dark:border-white/5">
              {(['Anime', 'Manga', 'Character'] as const).map(mode => (
                <button 
                  key={mode} 
                  onClick={() => setMediaType(mode)}
                  className={`text-[10px] font-black italic p-3 rounded-xl text-center transition-all ${
                    mediaType === mode 
                      ? 'bg-yellow-400 text-black shadow-lg scale-105 font-bold' 
                      : 'text-gray-500 dark:text-gray-400 opacity-50 hover:opacity-100'
                  }`}
                >
                  {mode === 'Anime' ? t('nav.anime_full', 'Anime') : mode === 'Manga' ? t('nav.manga_full', 'Manga') : t('nav.perso_full', 'Perso')}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-8">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('nav.difficulty', 'Difficulté')}</p>
            <div className="grid grid-cols-5 gap-2 bg-white/50 dark:bg-black/20 p-2 rounded-2xl border border-gray-100 dark:border-white/5">
              {(['Easy', 'Normal', 'Hard', 'Impossible'] as const).map((diff, idx) => {
                const bgColors = {
                  Easy: 'bg-green-500',
                  Normal: 'bg-blue-500',
                  Hard: 'bg-orange-500',
                  Impossible: 'bg-red-600'
                };
                const textColors = {
                  Easy: 'text-green-600 dark:text-green-400',
                  Normal: 'text-blue-600 dark:text-blue-400',
                  Hard: 'text-orange-600 dark:text-orange-400',
                  Impossible: 'text-red-600 dark:text-red-400'
                };
                const letter = ['C', 'B', 'A', 'S'][idx];
                return (
                  <button 
                    key={diff}
                    onClick={() => setDifficulty(diff)}
                    className={`manga-font text-xs p-2 rounded-lg transition-all ${
                      difficulty === diff ? `${bgColors[diff]} text-white shadow-lg scale-110` : `${textColors[diff]} bg-white/5 hover:bg-white/10`
                    }`}
                  >
                    {letter}
                  </button>
                );
              })}
              <Link 
                to="/custom-config/" 
                onClick={() => toggleSidebar(true)}
                className={`manga-font text-xs p-2 rounded-lg flex items-center justify-center no-underline transition-all ${
                  difficulty === 'Custom' ? 'bg-purple-600 text-white shadow-lg scale-110' : 'bg-purple-600/10 text-purple-600 dark:text-purple-400 hover:bg-purple-600/20'
                }`}
              >
                P
              </Link>
            </div>
          </div>
        </nav>

        {user?.is_staff && (
          <div className="mt-10 pt-8 border-t border-black/5 dark:border-white/5">
             <Link 
               to="/admin/dashboard/" 
               onClick={() => toggleSidebar(true)}
               className="w-full py-3 rounded-2xl bg-white/50 dark:bg-black/20 flex items-center justify-center gap-3 no-underline text-black dark:text-white font-black italic text-xs hover:bg-yellow-400 dark:hover:bg-yellow-400 hover:text-black dark:hover:text-black transition-all"
             >
                <Shield className="w-4 h-4" /> {t('nav.admin', 'ADMINISTRATION')}
             </Link>
          </div>
        )}
      </aside>

      {/* SETTINGS DRAWER (RIGHT) */}
      <aside 
        id="settings-drawer" 
        className={`fixed right-0 top-0 h-screen w-80 bg-[#fffcf0] dark:bg-[#1a1a2e] z-[2000] flex flex-col p-8 overflow-y-auto transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[-20px_0_50px_rgba(0,0,0,0.1)] border-l border-gray-100 dark:border-white/5 ${
          isSettingsOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="mb-12 flex items-center justify-between">
          <span className="manga-font text-2xl tracking-tighter text-black dark:text-white">⚙️ {t('nav.settings', 'Paramètres')}</span>
          <button 
            className="text-3xl hover:rotate-90 transition-transform duration-300 text-black dark:text-white" 
            onClick={() => toggleSettings(true)}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-10">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-6">
              {t('nav.appearance', 'Apparence')}
            </p>
            <div className="grid grid-cols-3 gap-3">
              {(['light', 'dark', 'auto'] as const).map(tName => {
                const iconMap = {
                  light: <Sun className="w-5 h-5 text-yellow-500 fill-current" />,
                  dark: <Moon className="w-5 h-5 text-blue-500 fill-current" />,
                  auto: <Monitor className="w-5 h-5 text-gray-500" />
                };
                const labelMap = {
                  light: t('theme.light', 'Clair'),
                  dark: t('theme.dark', 'Sombre'),
                  auto: t('theme.auto', 'Auto')
                };
                return (
                  <button 
                    key={tName} 
                    onClick={() => setTheme(tName)}
                    className={`flex flex-col items-center gap-2 p-3 rounded-2xl bg-white/50 dark:bg-black/20 border-2 transition-all ${
                      theme === tName ? 'border-yellow-400 bg-yellow-400/10' : 'border-transparent hover:border-gray-200'
                    }`}
                  >
                    {iconMap[tName]}
                    <span className="manga-font text-[9px] text-black dark:text-white">{labelMap[tName]}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-6">
              {t('nav.lang', 'Langue')}
            </p>
            <div className="space-y-3">
              {(['Français', 'English'] as const).map(lang => (
                <button 
                  key={lang} 
                  onClick={() => setCurrentLang(lang)}
                  className="w-full flex items-center justify-between p-4 rounded-2xl text-black dark:text-white hover:bg-white/50 dark:hover:bg-black/20 transition-all text-left"
                >
                  <span className="manga-font text-xs">{lang}</span>
                  {currentLang === lang && <CheckCircle2 className="w-4 h-4 text-green-500 fill-current" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-auto opacity-30 text-center text-black dark:text-white">
          <p className="manga-font text-[8px] tracking-widest">Animetix v6.0.4</p>
        </div>
      </aside>

      {/* SETTINGS FLOATING BUTTON */}
      <button 
        className="fixed bottom-6 left-6 w-14 h-14 bg-black text-yellow-400 dark:bg-[#0f0f1a] dark:text-white rounded-2xl shadow-2xl flex items-center justify-center text-3xl rotate-45 hover:rotate-0 transition-all duration-500 z-[800] group border border-black/10 dark:border-white/10" 
        onClick={() => toggleSettings()}
      >
        <Settings className="w-6 h-6 -rotate-45 group-hover:rotate-90 transition-transform duration-700" />
      </button>

      {/* NAVBAR */}
      <Navbar />

      {/* CONTENT WRAPPER */}
      <main className="flex-grow">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer />
      <CompanionOverlay />
    </div>
  );
};

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <LayoutContent>{children}</LayoutContent>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
};

export default Layout;