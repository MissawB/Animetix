import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import { AdSlot } from '../../features/billing/components/AdSlot';
import { Avatar } from '../ui/Avatar';
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
  glyph: string;
  label: string;
}

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="mt-6 mb-2 flex items-center gap-2 px-1 first:mt-0">
    <span className="h-3 w-0.5 flex-none bg-[#E8442B]" aria-hidden />
    <span className="whitespace-nowrap text-[10px] font-black uppercase tracking-[0.22em] text-[#8F94A5]">
      {children}
    </span>
    <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
  </div>
);

const NavItem: React.FC<{ item: NavDef; active: boolean; onClick: () => void }> = ({
  item,
  active,
  onClick,
}) => {
  const { glyph, to, label } = item;
  return (
    <Link
      to={to}
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      className={`group relative flex items-center gap-3 rounded-xl py-2.5 pl-3 pr-2.5 no-underline transition-all duration-200 ${
        active
          ? 'bg-[#E8442B] text-[#F4F1E8]'
          : 'text-[#8F94A5] hover:translate-x-0.5 hover:bg-[#F4F1E8]/[0.05] hover:text-[#F4F1E8]'
      }`}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full bg-[#F4F1E8]" />
      )}
      <span
        className={`grid h-8 w-8 shrink-0 place-items-center text-xl font-black leading-none ${
          active ? 'text-[#F4F1E8]' : 'text-[#8F94A5] group-hover:text-[#F4F1E8]'
        }`}
        aria-hidden
      >
        {glyph}
      </span>
      <span
        className={`truncate text-sm tracking-tight ${active ? 'font-black italic' : 'font-bold'}`}
      >
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
    { to: '/', glyph: '家', label: t('nav.home', 'Accueil') },
    { to: '/daily-challenge/', glyph: '日', label: t('nav.daily', 'Défi Quotidien') },
    { to: '/games/hub/', glyph: '遊', label: t('nav.games', 'Jeux') },
  ];

  const exploreLinks: NavDef[] = [
    { to: '/search/', glyph: '探', label: t('nav.search', 'Recherche') },
    { to: '/explore/', glyph: '冒', label: t('nav.explore', 'Explorer') },
    { to: '/media/manga/library/', glyph: '蔵', label: t('nav.library', 'Ma Bibliothèque') },
    { to: '/media/manga/offline/', glyph: '冊', label: t('nav.offline_manga', 'Manga Hors-ligne') },
  ];

  const communityLinks: NavDef[] = [
    { to: '/social/dashboard/', glyph: '会', label: t('nav.community', 'Communauté') },
    ...(isAuthenticated
      ? [
          { to: '/social/friends/', glyph: '友', label: t('nav.friends', 'Amis') },
          { to: '/social/sync/', glyph: '同', label: t('nav.offline_sync', 'Sync Hors-ligne') },
        ]
      : []),
    { to: '/leaderboard/', glyph: '位', label: t('nav.leaderboard', 'Classement') },
  ];

  // Labs is a hub (/lab/) that links to every experimental tool, so a single entry is enough.
  const creationLinks: NavDef[] = [
    { to: '/lab/forge-hub/', glyph: '鍛', label: t('nav.forge', 'Forge Créative') },
    { to: '/lab/', glyph: '実', label: t('nav.labs_hub', 'Labs') },
    { to: '/research/papers/', glyph: '究', label: t('nav.research', 'Recherche IA') },
  ];

  const systemLinks: NavDef[] = [
    { to: '/social/nexus/', glyph: '絆', label: t('nav.nexus', 'Nexus Pro') },
    { to: '/social/transparency/', glyph: '透', label: t('navbar.transparency', 'Transparence') },
    { to: '/social/open-data/', glyph: '開', label: t('nav.open_data', 'Portail Open Data') },
  ];

  const xp = user?.xp ?? 0;
  const level = Math.max(1, Math.floor(xp / 500));
  const xpProgress = ((xp % 500) / 500) * 100;

  return (
    <aside
      id="manga-sidebar"
      className={`fixed left-0 top-0 z-[2000] flex h-screen w-[310px] flex-col overflow-y-auto border-r border-[#F4F1E8]/10 bg-[#0B0C10] text-[#F4F1E8] shadow-[20px_0_60px_rgba(0,0,0,0.5)] transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-gradient-to-b from-[#0B0C10] via-[#0B0C10] to-transparent px-6 pb-4 pt-6">
        <Link to="/" onClick={close} className="group flex items-center gap-2.5 no-underline">
          <img
            src="/static/img/logo/white_logo.png"
            alt="Animetix"
            className="h-8 w-8 object-contain transition-transform group-hover:rotate-6"
          />
          <span className="font-manga text-xl font-black uppercase italic tracking-tighter text-[#F4F1E8]">
            ANIME<span className="text-[#E8442B]">TIX</span>
          </span>
        </Link>
        <button
          className="grid h-9 w-9 place-items-center rounded-xl text-[#8F94A5] transition-all duration-300 hover:rotate-90 hover:bg-[#F4F1E8]/10 hover:text-[#F4F1E8]"
          onClick={close}
          aria-label={t('nav.close_menu', 'Fermer le menu')}
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="px-6 pb-8">
        {/* User card */}
        {isAuthenticated && user && (
          <Link
            to={`/profile/${user.username}/`}
            onClick={close}
            className="group mb-5 block rounded-2xl border border-[#FDB913]/25 bg-[#0F1016] p-4 no-underline transition-all hover:border-[#FDB913]/60"
          >
            <div className="mb-3.5 flex items-center gap-3">
              <Avatar
                src={user.avatar}
                name={user.username ?? '?'}
                className="h-12 w-12 shrink-0 rotate-3 rounded-2xl border-2 border-[#0B0C10] text-xl font-black italic shadow-md transition-transform group-hover:rotate-0"
                fallbackClassName="bg-[#FDB913] text-[#0B0C10]"
              />
              <div className="min-w-0">
                <p className="font-manga m-0 truncate text-base font-black uppercase italic text-[#F4F1E8]">
                  {user.username}
                </p>
                <p className="m-0 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                  {user.tier === 'premium'
                    ? t('nav.tier_boosted', 'Boosté')
                    : t('nav.tier_standard', 'Standard')}{' '}
                  · {t('nav.level_abbrev', { defaultValue: 'Niv. {{level}}', level })}
                </p>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
              <div
                className="h-full rounded-full bg-[#FDB913] transition-all"
                style={{ width: `${xpProgress}%` }}
              ></div>
            </div>
            <div className="mt-2 flex justify-between text-[10px] font-black text-[#8F94A5]">
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
                item={{ to: '/auth/login/', glyph: '入', label: t('auth.login.link', 'Connexion') }}
                active={pathname === '/auth/login/'}
                onClick={close}
              />
              <NavItem
                item={{
                  to: '/auth/register/',
                  glyph: '参',
                  label: t('auth.register.link', "S'inscrire"),
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
          <div className="mt-8 border-t border-[#F4F1E8]/10 pt-6">
            <SectionLabel>{t('nav.admin_tools', 'Admin')}</SectionLabel>
            <Link
              to="/admin/dashboard/"
              onClick={close}
              className="flex w-full items-center justify-center gap-2.5 rounded-2xl bg-[#E8442B] py-3 text-xs font-black italic uppercase text-[#F4F1E8] no-underline transition-all hover:bg-[#c93a24]"
            >
              <span className="text-base font-black leading-none" aria-hidden>
                管
              </span>{' '}
              {t('nav.admin', 'ADMINISTRATION')}
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
};

export default React.memo(SidebarDrawer);
