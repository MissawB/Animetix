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
  CheckCircle2, Shield, User, Globe, Sparkles
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
        className={`fixed left-0 top-0 h-screen w-[300px] bg-white dark:bg-navy-800 z-[2000] flex flex-col p-8 overflow-y-auto transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[20px_0_50px_rgba(0,0,0,0.1)] border-r border-gray-100 dark:border-white/5 ${
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
          <div className="mb-10 bg-gray-50 dark:bg-navy-700 p-5 rounded-3xl shadow-xl border border-gray-100 dark:border-white/5">
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

        <nav className="flex-grow space-y-3">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Navigation</p>
          
          <Link 
            to="/" 
            onClick={() => toggleSidebar(true)}
            className={`nav-link-manga flex items-center gap-4 p-4 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${
              location.pathname === '/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black' : ''
            }`}
          >
            <Home className="w-5 h-5 text-xl" /> {t('nav.home', 'Accueil')}
          </Link>
          
          <Link 
            to="/daily-challenge/" 
            onClick={() => toggleSidebar(true)}
            className={`nav-link-manga flex items-center gap-4 p-4 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${
              location.pathname === '/daily-challenge/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black' : ''
            }`}
          >
            <Zap className="w-5 h-5 text-xl text-yellow-400 fill-current animate-pulse" /> {t('nav.daily', 'Défi Quotidien')}
          </Link>
          
          <Link 
            to="/leaderboard/" 
            onClick={() => toggleSidebar(true)}
            className={`nav-link-manga flex items-center gap-4 p-4 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${
              location.pathname === '/leaderboard/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black' : ''
            }`}
          >
            <Trophy className="w-5 h-5 text-xl text-orange-400 fill-current" /> {t('nav.leaderboard', 'Classement')}
          </Link>
          
          <Link 
            to="/achievements/" 
            onClick={() => toggleSidebar(true)}
            className={`nav-link-manga flex items-center gap-4 p-4 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${
              location.pathname === '/achievements/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black' : ''
            }`}
          >
            <BookOpen className="w-5 h-5 text-xl text-blue-400" /> {t('nav.grimoire', 'Grimoire')}
          </Link>

          <Link 
            to="/forge-hub/" 
            onClick={() => toggleSidebar(true)}
            className={`nav-link-manga flex items-center gap-4 p-4 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${
              location.pathname === '/forge-hub/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black' : ''
            }`}
          >
            <Sparkles className="w-5 h-5 text-xl text-purple-400" /> Forge Créative
          </Link>
          
          <div className="pt-8">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('nav.univers', 'Univers')}</p>
            <div className="grid grid-cols-3 gap-2 p-1 bg-gray-100 dark:bg-navy-900 rounded-2xl border border-gray-100 dark:border-white/5">
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
            <div className="grid grid-cols-5 gap-2 bg-gray-50 dark:bg-navy-900/50 p-2 rounded-2xl border border-gray-100 dark:border-white/5">
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
               className="w-full py-3 rounded-2xl bg-gray-100 dark:bg-navy-700 flex items-center justify-center gap-3 no-underline text-black dark:text-white font-black italic text-xs hover:bg-yellow-400 dark:hover:bg-yellow-400 hover:text-black dark:hover:text-black transition-all"
             >
                <Shield className="w-4 h-4" /> {t('nav.admin', 'ADMINISTRATION')}
             </Link>
          </div>
        )}
      </aside>

      {/* SETTINGS DRAWER (RIGHT) */}
      <aside 
        id="settings-drawer" 
        className={`fixed right-0 top-0 h-screen w-80 bg-white dark:bg-navy-800 z-[2000] flex flex-col p-8 overflow-y-auto transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[-20px_0_50px_rgba(0,0,0,0.1)] border-l border-gray-100 dark:border-white/5 ${
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
                    className={`flex flex-col items-center gap-2 p-3 rounded-2xl bg-gray-50 dark:bg-navy-700 border-2 transition-all ${
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
                  className="w-full flex items-center justify-between p-4 rounded-2xl text-black dark:text-white hover:bg-gray-50 dark:hover:bg-navy-700 transition-all text-left"
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
        className="fixed bottom-10 right-10 w-16 h-16 bg-black text-yellow-400 dark:bg-white dark:text-black rounded-2xl shadow-2xl flex items-center justify-center text-3xl rotate-45 hover:rotate-0 transition-all duration-500 z-[800] group border border-yellow-400/10" 
        onClick={() => toggleSettings()}
      >
        <Settings className="w-6 h-6 -rotate-45 group-hover:rotate-90 transition-transform duration-700" />
      </button>

      {/* NAVBAR (HIDDEN ON HOME PAGE ONLY) */}
      {location.pathname !== '/' && <Navbar />}

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
