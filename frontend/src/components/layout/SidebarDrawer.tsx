import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  X, Home, Zap, Trophy, Shield, Sparkles, Gamepad2, Search, Compass,
  Network, Film, Users, UserPlus, FlaskConical, BrainCircuit, Eye, LogIn, Microscope, Mic,
  Database, MessageSquare, Share2, Globe, Download, Monitor, BookOpen
} from 'lucide-react';
import { SimulatedAdBanner } from '../../features/billing/components/SimulatedAdBanner';
import { User } from '../../types';

interface SidebarDrawerProps {
  isSidebarOpen: boolean;
  isAuthenticated: boolean;
  user: User | null;
  pathname: string;
  mediaType: 'Anime' | 'Manga' | 'Character';
  difficulty: 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Custom';
  toggleSidebar: (forceClose?: boolean) => void;
  setMediaType: (mode: 'Anime' | 'Manga' | 'Character') => void;
  setDifficulty: (diff: 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Custom') => void;
}

const SidebarDrawer: React.FC<SidebarDrawerProps> = ({
  isSidebarOpen, isAuthenticated, user, pathname, mediaType, difficulty,
  toggleSidebar, setMediaType, setDifficulty
}) => {
  const { t } = useTranslation();
  const location = { pathname };

  return (
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
          aria-label="Fermer le menu"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {isAuthenticated && user && (
        <Link
          to={`/profile/${user.username}/`}
          onClick={() => toggleSidebar(true)}
          className="block mb-10 bg-white/50 dark:bg-black/20 p-5 rounded-3xl shadow-xl border border-gray-100 dark:border-white/5 no-underline group hover:scale-[1.02] active:scale-95 transition-all"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-yellow-400 text-black rounded-2xl flex items-center justify-center font-black italic border-2 border-black transform rotate-3 group-hover:rotate-0 text-xl shadow-md transition-transform">
              {user.username?.[0]?.toUpperCase()}
            </div>
            <div>
              <p className="manga-font text-sm m-0 text-black dark:text-white">{user.username}</p>
              <p className="text-[10px] font-bold text-yellow-600 dark:text-yellow-400 uppercase m-0">
                {user.tier === 'premium' ? 'Boosté' : 'Standard'}
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
        </Link>
      )}

      <nav className="flex-grow space-y-1 pb-10">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-4">{t('nav.main', 'Principal')}</p>
        <Link to="/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Home className="w-4 h-4" /> {t('nav.home', 'Accueil')}
        </Link>
        <Link to="/daily-challenge/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/daily-challenge/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Zap className="w-4 h-4 text-yellow-400 fill-current animate-pulse" /> {t('nav.daily', 'Défi Quotidien')}
        </Link>
        <Link to="/games/hub/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/games/hub/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Gamepad2 className="w-4 h-4" /> {t('nav.games', 'Jeux')}
        </Link>
        <Link to="/theater/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/theater/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Film className="w-4 h-4" /> {t('nav.theater', 'Cinéma')}
        </Link>

        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">{t('nav.exploration', 'Exploration')}</p>
        <Link to="/search/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/search/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Search className="w-4 h-4 text-cyan-400" /> {t('nav.search', 'Recherche')}
        </Link>
        <Link to="/explore/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Compass className="w-4 h-4 text-emerald-400" /> {t('nav.explore', 'Explorer')}
        </Link>
        <Link to="/explore/tachidesk/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/explore/tachidesk/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Globe className="w-4 h-4 text-blue-400" /> {t('nav.tachidesk', 'Tachidesk Explorer')}
        </Link>
        <Link to="/media/manga/library/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/media/manga/library/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <BookOpen className="w-4 h-4 text-pink-400" /> {t('nav.library', 'Ma Bibliothèque')}
        </Link>
        <Link to="/media/manga/offline/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/media/manga/offline/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Download className="w-4 h-4 text-orange-400" /> {t('nav.offline_manga', 'Manga Hors-ligne')}
        </Link>
        <Link to="/lab/latent-space/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/lab/latent-space/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Network className="w-4 h-4 text-indigo-400" /> {t('navbar.latent', 'Espace Latent')}
        </Link>

        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">{t('nav.community_section', 'Communauté')}</p>
        <Link to="/social/dashboard/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/dashboard/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Users className="w-4 h-4 text-orange-400" /> {t('nav.community', 'Communauté')}
        </Link>
        {isAuthenticated && (
          <>
            <Link to="/social/friends/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/friends/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
              <UserPlus className="w-4 h-4 text-pink-400" /> {t('nav.friends', 'Amis')}
            </Link>
            <Link to="/social/sync/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/sync/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
              <Database className="w-4 h-4 text-yellow-400" /> {t('nav.offline_sync', 'Sync Hors-ligne')}
            </Link>
            <Link to="/social/ai-feedback-history/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/ai-feedback-history/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
              <MessageSquare className="w-4 h-4 text-purple-400" /> {t('nav.ai_feedback_history', 'Feedbacks IA')}
            </Link>
          </>
        )}
        <Link to="/leaderboard/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/leaderboard/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Trophy className="w-4 h-4 text-yellow-500" /> {t('nav.leaderboard', 'Classement')}
        </Link>

        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">{t('nav.labs', 'Labs & Création')}</p>
        <Link to="/lab/forge-hub/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/lab/forge-hub/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Sparkles className="w-4 h-4 text-purple-400" /> {t('nav.forge', 'Forge Créative')}
        </Link>
        <Link to="/lab/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/lab/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <FlaskConical className="w-4 h-4 text-green-400" /> {t('nav.betalab', 'Labo Bêta')}
        </Link>
        <Link to="/research/papers/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/research/papers/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Microscope className="w-4 h-4 text-cyan-500" /> {t('nav.research', 'Labo de Recherche')}
        </Link>

        {/* Ghost Labs Links */}
        <Link to="/lab/audio/seiyuu/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-emerald-400/10 dark:hover:bg-emerald-400/5 ${location.pathname === '/lab/audio/seiyuu/' ? 'bg-gradient-to-r from-emerald-400 to-teal-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Mic className="w-4 h-4 text-emerald-500" /> {t('nav.seiyuu', 'Seiyuu Discovery')}
        </Link>
        <Link to="/lab/compiler/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-blue-400/10 dark:hover:bg-blue-400/5 ${location.pathname === '/lab/compiler/' ? 'bg-gradient-to-r from-blue-400 to-cyan-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Monitor className="w-4 h-4 text-blue-500" /> {t('nav.compiler', 'Compilateur IA')}
        </Link>
        <Link to="/lab/video-rag/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-red-400/10 dark:hover:bg-red-400/5 ${location.pathname === '/lab/video-rag/' ? 'bg-gradient-to-r from-red-400 to-rose-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Film className="w-4 h-4 text-red-500" /> {t('nav.video_rag', 'Video RAG')}
        </Link>
        <Link to="/lab/cove-oracle/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-indigo-400/10 dark:hover:bg-indigo-400/5 ${location.pathname === '/lab/cove-oracle/' ? 'bg-gradient-to-r from-indigo-400 to-violet-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Shield className="w-4 h-4 text-indigo-500" /> {t('nav.cove', 'Oracle CoVe')}
        </Link>

        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">Système & Diagnostics</p>
        <Link to="/social/nexus/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/nexus/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <BrainCircuit className="w-4 h-4 text-fuchsia-400" /> {t('nav.nexus', 'Nexus Pro')}
        </Link>
        <Link to="/social/transparency/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/transparency/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Eye className="w-4 h-4 text-slate-400" /> {t('navbar.transparency', 'Transparence')}
        </Link>
        <Link to="/social/open-data/" onClick={() => toggleSidebar(true)} className={`nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-yellow-400/10 dark:hover:bg-yellow-400/5 ${location.pathname === '/social/open-data/' ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg scale-105 border-l-4 border-black font-bold' : ''}`}>
          <Share2 className="w-4 h-4 text-teal-400" /> {t('nav.open_data', 'Portail Open Data')}
        </Link>

        {!isAuthenticated && (
          <>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2 mt-6">{t('nav.account', 'Compte')}</p>
            <Link to="/auth/login/" onClick={() => toggleSidebar(true)} className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-blue-500/10 dark:hover:bg-blue-500/20">
              <LogIn className="w-4 h-4 text-blue-500" /> {t('auth.login', 'Connexion')}
            </Link>
            <Link to="/auth/register/" onClick={() => toggleSidebar(true)} className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-green-500/10 dark:hover:bg-green-500/20">
              <UserPlus className="w-4 h-4 text-green-500" /> {t('auth.register', "S'inscrire")}
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
        {user && user.tier === 'free' && (
          <div className="pt-8 px-2">
            <SimulatedAdBanner />
          </div>
        )}
      </nav>

      {user?.is_staff && (
        <div className="mt-10 pt-8 border-t border-black/5 dark:border-white/5">
           <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Outils Admin & Monitoring</p>
           <div className="space-y-1">
             <Link
               to="/admin/safety-audit/"
               onClick={() => toggleSidebar(true)}
               className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-red-500/10 dark:hover:bg-red-500/5 text-xs"
             >
                <Shield className="w-4 h-4 text-red-500" /> Audit Sécurité IA
             </Link>
             <Link
               to="/admin/ttc-monitoring/"
               onClick={() => toggleSidebar(true)}
               className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-blue-500/10 dark:hover:bg-blue-500/5 text-xs"
             >
                <Zap className="w-4 h-4 text-blue-500" /> Monitoring TTC
             </Link>
             <Link
               to="/admin/financials/"
               onClick={() => toggleSidebar(true)}
               className="nav-link-manga flex items-center gap-4 p-3 rounded-2xl no-underline text-black dark:text-white hover:bg-green-500/10 dark:hover:bg-green-500/5 text-xs"
             >
                <Trophy className="w-4 h-4 text-green-500" /> Gestion Financière
             </Link>
             <Link
               to="/admin/dashboard/"
               onClick={() => toggleSidebar(true)}
               className="w-full mt-4 py-3 rounded-2xl bg-white/50 dark:bg-black/20 flex items-center justify-center gap-3 no-underline text-black dark:text-white font-black italic text-xs hover:bg-yellow-400 dark:hover:bg-yellow-400 hover:text-black dark:hover:text-black transition-all"
             >
                <Shield className="w-4 h-4" /> {t('nav.admin', 'ADMINISTRATION')}
             </Link>
           </div>
        </div>
      )}
    </aside>
  );
};

export default React.memo(SidebarDrawer);
