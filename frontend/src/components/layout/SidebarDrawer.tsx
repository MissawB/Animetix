import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  X,
  Home,
  Zap,
  Trophy,
  Shield,
  Sparkles,
  Gamepad2,
  Search,
  Compass,
  Users,
  UserPlus,
  FlaskConical,
  BrainCircuit,
  Eye,
  LogIn,
  Microscope,
  Database,
  Share2,
  Download,
  BookOpen,
  type LucideIcon,
} from 'lucide-react';
import { AdSlot } from '../../features/billing/components/AdSlot';
import { User } from '../../types';

const SIDEBAR_AD_SLOT = import.meta.env.VITE_ADSENSE_SLOT_SIDEBAR as string | undefined;

interface SidebarDrawerProps {
  isSidebarOpen: boolean;
  isAuthenticated: boolean;
  user: User | null;
  pathname: string;
  toggleSidebar: (forceClose?: boolean) => void;
}

interface NavDef {
  to: string;
  icon: LucideIcon;
  label: string;
  color: string;
}

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex items-center gap-3 px-1 mt-6 mb-2 first:mt-0">
    <span className="text-[10px] font-black uppercase tracking-[0.22em] text-gray-400 dark:text-gray-500 whitespace-nowrap">
      {children}
    </span>
    <span className="flex-1 h-px bg-gradient-to-r from-gray-200 dark:from-white/10 to-transparent" />
  </div>
);

const NavItem: React.FC<{ item: NavDef; active: boolean; onClick: () => void }> = ({
  item,
  active,
  onClick,
}) => {
  const { icon: Icon, to, label, color } = item;
  return (
    <Link
      to={to}
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      className={`group relative flex items-center gap-3 pl-3 pr-2.5 py-2.5 rounded-xl no-underline transition-all duration-200 ${
        active
          ? 'bg-yellow-400 text-black shadow-[0_6px_22px_-6px_rgba(253,185,19,0.7)]'
          : 'text-gray-600 dark:text-gray-300 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] hover:translate-x-0.5'
      }`}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-7 w-1 rounded-r-full bg-black" />
      )}
      <span
        className={`grid place-items-center w-8 h-8 rounded-lg shrink-0 transition-colors ${
          active
            ? 'bg-black/10'
            : 'bg-black/[0.04] dark:bg-white/5 group-hover:bg-black/[0.07] dark:group-hover:bg-white/10'
        }`}
      >
        <Icon className={`w-[18px] h-[18px] ${active ? 'text-black' : color}`} />
      </span>
      <span className={`text-sm tracking-tight truncate ${active ? 'font-black' : 'font-bold'}`}>
        {label}
      </span>
    </Link>
  );
};

const SidebarDrawer: React.FC<SidebarDrawerProps> = ({
  isSidebarOpen,
  isAuthenticated,
  user,
  pathname,
  toggleSidebar,
}) => {
  const { t } = useTranslation();
  const close = () => toggleSidebar(true);

  const mainLinks: NavDef[] = [
    {
      to: '/',
      icon: Home,
      label: t('nav.home', 'Accueil'),
      color: 'text-gray-500 dark:text-gray-400',
    },
    {
      to: '/daily-challenge/',
      icon: Zap,
      label: t('nav.daily', 'Défi Quotidien'),
      color: 'text-yellow-400',
    },
    { to: '/games/hub/', icon: Gamepad2, label: t('nav.games', 'Jeux'), color: 'text-violet-400' },
  ];

  const exploreLinks: NavDef[] = [
    { to: '/search/', icon: Search, label: t('nav.search', 'Recherche'), color: 'text-cyan-400' },
    {
      to: '/explore/',
      icon: Compass,
      label: t('nav.explore', 'Explorer'),
      color: 'text-emerald-400',
    },
    {
      to: '/media/manga/library/',
      icon: BookOpen,
      label: t('nav.library', 'Ma Bibliothèque'),
      color: 'text-pink-400',
    },
    {
      to: '/media/manga/offline/',
      icon: Download,
      label: t('nav.offline_manga', 'Manga Hors-ligne'),
      color: 'text-orange-400',
    },
  ];

  const communityLinks: NavDef[] = [
    {
      to: '/social/dashboard/',
      icon: Users,
      label: t('nav.community', 'Communauté'),
      color: 'text-orange-400',
    },
    ...(isAuthenticated
      ? [
          {
            to: '/social/friends/',
            icon: UserPlus,
            label: t('nav.friends', 'Amis'),
            color: 'text-pink-400',
          },
          {
            to: '/social/sync/',
            icon: Database,
            label: t('nav.offline_sync', 'Sync Hors-ligne'),
            color: 'text-yellow-400',
          },
        ]
      : []),
    {
      to: '/leaderboard/',
      icon: Trophy,
      label: t('nav.leaderboard', 'Classement'),
      color: 'text-yellow-500',
    },
  ];

  // Labs is a hub (/lab/) that links to every experimental tool, so a single entry is enough.
  const creationLinks: NavDef[] = [
    {
      to: '/lab/forge-hub/',
      icon: Sparkles,
      label: t('nav.forge', 'Forge Créative'),
      color: 'text-purple-400',
    },
    { to: '/lab/', icon: FlaskConical, label: t('nav.labs_hub', 'Labs'), color: 'text-green-400' },
    {
      to: '/research/papers/',
      icon: Microscope,
      label: t('nav.research', 'Recherche IA'),
      color: 'text-cyan-500',
    },
  ];

  const systemLinks: NavDef[] = [
    {
      to: '/social/nexus/',
      icon: BrainCircuit,
      label: t('nav.nexus', 'Nexus Pro'),
      color: 'text-fuchsia-400',
    },
    {
      to: '/social/transparency/',
      icon: Eye,
      label: t('navbar.transparency', 'Transparence'),
      color: 'text-slate-400',
    },
    {
      to: '/social/open-data/',
      icon: Share2,
      label: t('nav.open_data', 'Portail Open Data'),
      color: 'text-teal-400',
    },
  ];

  const xp = user?.xp ?? 0;
  const level = Math.max(1, Math.floor(xp / 500));
  const xpProgress = ((xp % 500) / 500) * 100;

  return (
    <aside
      id="manga-sidebar"
      className={`fixed left-0 top-0 h-screen w-[310px] bg-[#fffcf0] dark:bg-[#15152a] z-[2000] flex flex-col overflow-y-auto transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[20px_0_60px_rgba(0,0,0,0.25)] border-r border-gray-100 dark:border-white/5 ${
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gradient-to-b from-[#fffcf0] dark:from-[#15152a] via-[#fffcf0] dark:via-[#15152a] to-transparent px-6 pt-6 pb-4 flex items-center justify-between">
        <Link to="/" onClick={close} className="flex items-center gap-2.5 no-underline group">
          <img
            src="/static/img/logo/white_logo.png"
            alt="Animetix"
            className="w-8 h-8 object-contain dark:invert transition-transform group-hover:rotate-6"
          />
          <span className="manga-font text-xl tracking-tighter text-black dark:text-white">
            ANIME<span className="text-yellow-700 dark:text-yellow-400">TIX</span>
          </span>
        </Link>
        <button
          className="grid place-items-center w-9 h-9 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-black/5 dark:hover:bg-white/10 hover:text-black dark:hover:text-white hover:rotate-90 transition-all duration-300"
          onClick={close}
          aria-label={t('nav.close_menu', 'Fermer le menu')}
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="px-6 pb-8">
        {/* User card */}
        {isAuthenticated && user && (
          <Link
            to={`/profile/${user.username}/`}
            onClick={close}
            className="block mb-5 p-4 rounded-2xl bg-gradient-to-br from-yellow-400/15 via-yellow-400/5 to-transparent border border-yellow-400/25 no-underline group hover:border-yellow-400/50 transition-all"
          >
            <div className="flex items-center gap-3 mb-3.5">
              <div className="w-12 h-12 bg-yellow-400 text-black rounded-2xl flex items-center justify-center font-black italic border-2 border-black/80 rotate-3 group-hover:rotate-0 text-xl shadow-md transition-transform shrink-0">
                {user.username?.[0]?.toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="manga-font text-base m-0 text-black dark:text-white truncate">
                  {user.username}
                </p>
                <p className="text-[10px] font-black text-yellow-600 dark:text-yellow-400 uppercase tracking-widest m-0">
                  {user.tier === 'premium'
                    ? t('nav.tier_boosted', 'Boosté')
                    : t('nav.tier_standard', 'Standard')}{' '}
                  · {t('nav.level_abbrev', { defaultValue: 'Niv. {{level}}', level })}
                </p>
              </div>
            </div>
            <div className="w-full bg-black/10 dark:bg-black/40 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-yellow-400 to-orange-500 h-full rounded-full shadow-[0_0_10px_#fdb913] transition-all"
                style={{ width: `${xpProgress}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-2 font-black text-[10px] text-black/40 dark:text-white/40">
              <span>{t('nav.xp_amount', { defaultValue: '{{xp}} XP', xp })}</span>
              <span>
                {t('nav.xp_to_next', {
                  defaultValue: '{{xp}} XP → NIV. {{level}}',
                  xp: 500 - (xp % 500),
                  level: level + 1,
                })}
              </span>
            </div>
          </Link>
        )}

        {/* Navigation */}
        <nav className="space-y-0.5">
          <SectionLabel>{t('nav.main', 'Principal')}</SectionLabel>
          {mainLinks.map((it) => (
            <NavItem key={it.to} item={it} active={pathname === it.to} onClick={close} />
          ))}

          <SectionLabel>{t('nav.exploration', 'Exploration')}</SectionLabel>
          {exploreLinks.map((it) => (
            <NavItem key={it.to} item={it} active={pathname === it.to} onClick={close} />
          ))}

          <SectionLabel>{t('nav.community_section', 'Communauté')}</SectionLabel>
          {communityLinks.map((it) => (
            <NavItem key={it.to} item={it} active={pathname === it.to} onClick={close} />
          ))}

          <SectionLabel>{t('nav.labs', 'Labs & Création')}</SectionLabel>
          {creationLinks.map((it) => (
            <NavItem key={it.to} item={it} active={pathname === it.to} onClick={close} />
          ))}

          <SectionLabel>{t('nav.system', 'Système')}</SectionLabel>
          {systemLinks.map((it) => (
            <NavItem key={it.to} item={it} active={pathname === it.to} onClick={close} />
          ))}

          {!isAuthenticated && (
            <>
              <SectionLabel>{t('nav.account', 'Compte')}</SectionLabel>
              <NavItem
                item={{
                  to: '/auth/login/',
                  icon: LogIn,
                  label: t('auth.login.link', 'Connexion'),
                  color: 'text-blue-500',
                }}
                active={pathname === '/auth/login/'}
                onClick={close}
              />
              <NavItem
                item={{
                  to: '/auth/register/',
                  icon: UserPlus,
                  label: t('auth.register.link', "S'inscrire"),
                  color: 'text-green-500',
                }}
                active={pathname === '/auth/register/'}
                onClick={close}
              />
            </>
          )}
        </nav>

        {user && user.tier === 'free' && (
          <div className="pt-7">
            <AdSlot slot={SIDEBAR_AD_SLOT} format="rectangle" />
          </div>
        )}

        {/* Admin — the dashboard hub gives access to every admin tool */}
        {user?.is_staff && (
          <div className="mt-8 pt-6 border-t border-black/5 dark:border-white/5">
            <SectionLabel>{t('nav.admin_tools', 'Admin')}</SectionLabel>
            <Link
              to="/admin/dashboard/"
              onClick={close}
              className="w-full py-3 rounded-2xl bg-black text-yellow-400 dark:bg-white/5 dark:text-white flex items-center justify-center gap-2.5 no-underline font-black italic text-xs hover:bg-yellow-400 hover:text-black dark:hover:bg-yellow-400 dark:hover:text-black transition-all"
            >
              <Shield className="w-4 h-4" /> {t('nav.admin', 'ADMINISTRATION')}
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
};

export default React.memo(SidebarDrawer);
