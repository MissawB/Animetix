import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { Menu, LogIn, UserPlus, Bell, HelpCircle, Zap, ChevronDown, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { usePersonalizationStore } from '../store/personalizationStore';
import { useNotificationStore } from '../store/notificationStore';
import { PersonalizationPanel } from './shared/PersonalizationPanel';
import { Avatar } from './ui/Avatar';

const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user, logout } = useAuthStore();
  const { isPersonalizationEnabled, setPersonalizationEnabled } = usePersonalizationStore();
  const { unreadCount } = useNotificationStore();
  const [showMenu, setShowMenu] = React.useState(false);
  const [showPersonalizationPanel, setShowPersonalizationPanel] = React.useState(false);

  const closeMenu = () => setShowMenu(false);

  const menuItem =
    'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl no-underline text-sm font-medium text-[#8F94A5] hover:bg-[#F4F1E8]/[0.06] hover:text-[#F4F1E8] transition-colors text-left';

  return (
    <nav className="sticky top-0 z-[1000] flex items-center justify-between border-b border-[#F4F1E8]/10 bg-[#0B0C10]/90 px-6 py-3.5 text-[#F4F1E8] backdrop-blur-md md:px-10">
      {/* Filet éditorial shu, signature de l'édition de nuit */}
      <span
        className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-[#E8442B] via-[#E8442B]/20 to-transparent"
        aria-hidden
      />

      {/* Left: menu + brand */}
      <div className="flex items-center gap-4">
        <button
          className="grid h-11 w-11 place-items-center rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] text-[#F4F1E8] transition-all hover:border-[#E8442B] hover:text-[#E8442B] active:scale-95"
          onClick={() => toggleSidebar()}
          aria-label={t('nav.toggle_sidebar', 'Ouvrir le menu')}
        >
          <Menu className="h-5 w-5" />
        </button>
        <Link to="/" className="group flex items-center gap-2.5 no-underline">
          <img src="/static/img/logo/white_logo.png" alt="" className="h-7" />
          <span className="font-manga hidden text-lg font-black uppercase italic tracking-tighter text-[#F4F1E8] sm:block">
            ANIME<span className="text-[#E8442B]">TIX</span>
          </span>
        </Link>
      </div>

      {/* Right: essentials + account menu */}
      <div className="flex shrink-0 items-center gap-2.5">
        {user ? (
          <>
            {/* Solde Berrix — voix données (or) */}
            <Link
              to="/power-station/"
              className="group flex items-center gap-2 rounded-xl border border-[#FDB913]/20 bg-[#FDB913]/10 px-3 py-2 no-underline transition-all hover:border-[#FDB913]/40"
            >
              <Zap className="h-3.5 w-3.5 fill-current text-[#FDB913] transition-transform group-hover:scale-110" />
              <span className="font-manga text-[11px] font-black italic text-[#FDB913]">
                {user.wallet_balance?.toLocaleString() || 0}{' '}
                <span className="text-[8px] opacity-70">Bx</span>
              </span>
            </Link>

            {/* Notifications */}
            <Link
              to="/notifications"
              className="relative grid h-10 w-10 place-items-center rounded-xl text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/[0.06] hover:text-[#F4F1E8]"
              aria-label={t('nav.notifications', 'Notifications')}
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#E8442B] text-[9px] font-black text-[#F4F1E8]">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </Link>

            {/* Account menu */}
            <div className="relative">
              <button
                onClick={() => setShowMenu((v) => !v)}
                className="flex items-center gap-2 rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] py-1.5 pl-1.5 pr-2.5 transition-all hover:border-[#FDB913]/50"
                aria-haspopup="menu"
                aria-expanded={showMenu}
                aria-label={t('nav.account_menu', 'Menu du compte')}
              >
                <Avatar
                  src={user.avatar}
                  name={user.username ?? '?'}
                  className="h-7 w-7 shrink-0 rounded-lg text-sm font-black italic"
                  fallbackClassName="bg-[#FDB913] text-[#0B0C10]"
                />
                <span className="font-manga hidden max-w-[100px] truncate text-xs font-black italic text-[#F4F1E8] sm:block">
                  {user.username}
                </span>
                <ChevronDown
                  className={`h-4 w-4 text-[#8F94A5] transition-transform ${showMenu ? 'rotate-180' : ''}`}
                />
              </button>

              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={closeMenu}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') closeMenu();
                    }}
                    role="button"
                    tabIndex={-1}
                    aria-label={t('nav.close_menu', 'Fermer le menu')}
                  />
                  <div
                    className="absolute right-0 top-full z-50 mt-3 w-64 animate-in fade-in slide-in-from-top-2 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-2 shadow-2xl duration-200"
                    role="menu"
                  >
                    <div className="mb-1 border-b border-[#F4F1E8]/10 px-3 pb-3 pt-2">
                      <p className="font-manga m-0 truncate text-sm font-black italic text-[#F4F1E8]">
                        {user.username}
                      </p>
                      <p className="m-0 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                        {user.tier === 'premium'
                          ? t('nav.tier_boosted', 'Boosté')
                          : t('nav.tier_standard', 'Standard')}
                      </p>
                    </div>

                    <Link
                      to={`/profile/${user.username}/`}
                      onClick={closeMenu}
                      className={menuItem}
                      role="menuitem"
                    >
                      <span
                        className="w-4 text-center text-base font-black leading-none"
                        aria-hidden
                      >
                        印
                      </span>{' '}
                      {t('nav.my_profile', 'Mon profil')}
                    </Link>

                    <button
                      onClick={() => setPersonalizationEnabled(!isPersonalizationEnabled)}
                      className={menuItem}
                      role="menuitemcheckbox"
                      aria-checked={isPersonalizationEnabled}
                    >
                      <span
                        className={`w-4 text-center text-base font-black leading-none ${isPersonalizationEnabled ? 'text-[#FDB913]' : ''}`}
                        aria-hidden
                      >
                        彩
                      </span>
                      <span className="flex-1">
                        {t('nav.hyper_perso', 'Hyper-personnalisation')}
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[9px] font-black uppercase ${
                          isPersonalizationEnabled
                            ? 'bg-[#FDB913]/15 text-[#FDB913]'
                            : 'bg-[#F4F1E8]/10 text-[#8F94A5]'
                        }`}
                      >
                        {isPersonalizationEnabled ? 'ON' : 'OFF'}
                      </span>
                    </button>

                    <button
                      onClick={() => {
                        closeMenu();
                        setShowPersonalizationPanel(true);
                      }}
                      className={menuItem}
                      role="menuitem"
                    >
                      <span
                        className="w-4 text-center text-base font-black leading-none"
                        aria-hidden
                      >
                        調
                      </span>{' '}
                      {t('nav.perso_settings', 'Personnalisation avancée')}
                    </button>

                    <Link to="/support" onClick={closeMenu} className={menuItem} role="menuitem">
                      <HelpCircle className="h-4 w-4" /> {t('nav.support', 'Support technique')}
                    </Link>

                    {user?.is_staff && (
                      <Link
                        to="/admin/dashboard/"
                        onClick={closeMenu}
                        className={menuItem}
                        role="menuitem"
                      >
                        <span
                          className="w-4 text-center text-base font-black leading-none text-[#E8442B]"
                          aria-hidden
                        >
                          管
                        </span>{' '}
                        {t('nav.admin', 'Administration')}
                      </Link>
                    )}

                    <div className="my-1 border-t border-[#F4F1E8]/10" />
                    <button
                      onClick={() => {
                        closeMenu();
                        logout();
                      }}
                      className={`${menuItem} !text-[#E8442B] hover:!bg-[#E8442B]/10`}
                      role="menuitem"
                    >
                      <span
                        className="w-4 text-center text-base font-black leading-none"
                        aria-hidden
                      >
                        出
                      </span>{' '}
                      {t('auth.logout', 'Déconnexion')}
                    </button>
                  </div>
                </>
              )}
            </div>
          </>
        ) : (
          <>
            <Link
              to="/auth/login/"
              className="flex items-center gap-2 px-3 py-2 text-xs font-black uppercase italic tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
            >
              <LogIn className="h-4 w-4" />{' '}
              <span className="hidden sm:inline">{t('auth.login.link', 'Connexion')}</span>
            </Link>
            <Link
              to="/auth/register/"
              className="flex items-center gap-2 rounded-xl border-none bg-[#E8442B] px-4 py-2.5 text-xs font-black uppercase italic tracking-widest text-[#F4F1E8] no-underline transition-all hover:scale-105 hover:bg-[#c93a24] active:scale-95"
            >
              <UserPlus className="h-4 w-4" />{' '}
              <span className="hidden sm:inline">{t('auth.register.link', "S'inscrire")}</span>
            </Link>
          </>
        )}
      </div>

      {/* Advanced personalization panel */}
      {showPersonalizationPanel && (
        <>
          <div
            className="fixed inset-0 z-[1090] bg-black/60 backdrop-blur-sm"
            onClick={() => setShowPersonalizationPanel(false)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') setShowPersonalizationPanel(false);
            }}
            role="button"
            tabIndex={-1}
            aria-label={t('nav.close_panel', 'Fermer le panneau')}
          />
          <div className="fixed left-1/2 top-1/2 z-[1100] w-[90vw] max-w-md -translate-x-1/2 -translate-y-1/2 animate-in fade-in zoom-in-95 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 shadow-2xl duration-200">
            <div className="mb-6 flex items-center justify-between">
              <h4 className="font-manga text-sm font-black uppercase italic tracking-widest text-[#F4F1E8]">
                {t('personalization.title', 'Personnalisation')}
              </h4>
              <button
                onClick={() => setShowPersonalizationPanel(false)}
                className="grid h-8 w-8 place-items-center rounded-lg text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/10 hover:text-[#F4F1E8]"
                aria-label={t('nav.close', 'Fermer')}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <PersonalizationPanel />
          </div>
        </>
      )}
    </nav>
  );
};

export default Navbar;
