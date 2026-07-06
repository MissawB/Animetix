import React from 'react';
import { Link } from 'react-router-dom';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import {
  Menu, Shield, Sparkles, Sliders, User, LogOut, LogIn, UserPlus, Bell,
  HelpCircle, Zap, ChevronDown, X
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { usePersonalizationStore } from '../store/personalizationStore';
import { useNotificationStore } from '../store/notificationStore';
import { PersonalizationPanel } from './shared/PersonalizationPanel';

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
    'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl no-underline text-sm font-bold text-gray-700 dark:text-gray-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-left';

  return (
    <nav className="px-6 md:px-10 py-3.5 flex items-center justify-between sticky top-0 bg-[#fffcf0]/90 dark:bg-[#1a1a2e]/90 backdrop-blur-md z-[1000] border-b border-black/5 dark:border-white/5 transition-colors duration-500">
      {/* Left: menu + brand */}
      <div className="flex items-center gap-4">
        <button
          className="grid place-items-center w-11 h-11 bg-black dark:bg-white/10 text-white rounded-xl hover:bg-yellow-400 hover:text-black dark:hover:bg-yellow-400 dark:hover:text-black active:scale-95 transition-all"
          onClick={() => toggleSidebar()}
          aria-label={t('nav.toggle_sidebar', 'Ouvrir le menu')}
        >
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/" className="flex items-center gap-2.5 no-underline group">
          <img src="/static/img/logo/white_logo.png" alt="" className="h-7 dark:hidden" />
          <img src="/static/img/logo/logo.png" alt="" className="h-7 hidden dark:block" />
          <span className="manga-font text-lg tracking-tighter text-black dark:text-white hidden sm:block">
            ANIME<span className="text-yellow-700 dark:text-yellow-400">TIX</span>
          </span>
        </Link>
      </div>

      {/* Right: essentials + account menu */}
      <div className="flex items-center gap-2.5 shrink-0">
        {user ? (
          <>
            {/* Berrix balance */}
            <Link
              to="/power-station/"
              className="flex items-center gap-2 px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-xl transition-all no-underline group"
            >
              <Zap className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform fill-current" />
              <span className="text-[11px] font-black italic manga-font text-blue-500">
                {user.wallet_balance?.toLocaleString() || 0} <span className="text-[8px] opacity-70">Bx</span>
              </span>
            </Link>

            {/* Notifications */}
            <Link
              to="/notifications"
              className="relative grid place-items-center w-10 h-10 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-black/5 dark:hover:bg-white/10 hover:text-blue-500 transition-colors"
              aria-label={t('nav.notifications', 'Notifications')}
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </Link>

            {/* Account menu */}
            <div className="relative">
              <button
                onClick={() => setShowMenu((v) => !v)}
                className="flex items-center gap-2 pl-1.5 pr-2.5 py-1.5 rounded-xl bg-gray-50 dark:bg-white/5 border border-black/5 dark:border-white/5 hover:border-yellow-400/50 transition-all"
                aria-haspopup="menu"
                aria-expanded={showMenu}
                aria-label={t('nav.account_menu', 'Menu du compte')}
              >
                <span className="w-7 h-7 rounded-lg bg-yellow-400 text-black flex items-center justify-center font-black italic text-sm shrink-0">
                  {user.username?.[0]?.toUpperCase()}
                </span>
                <span className="hidden sm:block text-xs font-black italic manga-font text-black dark:text-white max-w-[100px] truncate">
                  {user.username}
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showMenu ? 'rotate-180' : ''}`} />
              </button>

              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={closeMenu}
                    onKeyDown={(e) => { if (e.key === 'Escape') closeMenu(); }}
                    role="button"
                    tabIndex={-1}
                    aria-label={t('nav.close_menu', 'Fermer le menu')}
                  />
                  <div
                    className="absolute top-full right-0 mt-3 w-64 bg-white dark:bg-[#0f0f1a] rounded-2xl shadow-2xl border border-black/5 dark:border-white/10 p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200"
                    role="menu"
                  >
                    <div className="px-3 pt-2 pb-3 mb-1 border-b border-black/5 dark:border-white/10">
                      <p className="manga-font text-sm text-black dark:text-white m-0 truncate">{user.username}</p>
                      <p className="text-[10px] font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400 m-0">
                        {user.tier === 'premium' ? t('nav.tier_boosted', 'Boosté') : t('nav.tier_standard', 'Standard')}
                      </p>
                    </div>

                    <Link to={`/profile/${user.username}/`} onClick={closeMenu} className={menuItem} role="menuitem">
                      <User className="w-4 h-4 text-orange-500" /> {t('nav.my_profile', 'Mon profil')}
                    </Link>

                    <button
                      onClick={() => setPersonalizationEnabled(!isPersonalizationEnabled)}
                      className={menuItem}
                      role="menuitemcheckbox"
                      aria-checked={isPersonalizationEnabled}
                    >
                      <Sparkles className={`w-4 h-4 ${isPersonalizationEnabled ? 'text-brand-accent' : 'text-gray-400'}`} />
                      <span className="flex-1">{t('nav.hyper_perso', 'Hyper-personnalisation')}</span>
                      <span className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded ${isPersonalizationEnabled ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'bg-gray-400/15 text-gray-500'}`}>
                        {isPersonalizationEnabled ? 'ON' : 'OFF'}
                      </span>
                    </button>

                    <button
                      onClick={() => { closeMenu(); setShowPersonalizationPanel(true); }}
                      className={menuItem}
                      role="menuitem"
                    >
                      <Sliders className="w-4 h-4 text-blue-500" /> {t('nav.perso_settings', 'Personnalisation avancée')}
                    </button>

                    <Link to="/support" onClick={closeMenu} className={menuItem} role="menuitem">
                      <HelpCircle className="w-4 h-4 text-cyan-500" /> {t('nav.support', 'Support technique')}
                    </Link>

                    {user?.is_staff && (
                      <Link to="/admin/dashboard/" onClick={closeMenu} className={menuItem} role="menuitem">
                        <Shield className="w-4 h-4 text-fuchsia-500" /> {t('nav.admin', 'Administration')}
                      </Link>
                    )}

                    <div className="my-1 border-t border-black/5 dark:border-white/10" />
                    <button onClick={() => { closeMenu(); logout(); }} className={`${menuItem} !text-red-500`} role="menuitem">
                      <LogOut className="w-4 h-4" /> {t('auth.logout', 'Déconnexion')}
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
              className="flex items-center gap-2 no-underline text-xs font-black italic text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white transition-all uppercase tracking-widest px-3 py-2"
            >
              <LogIn className="w-4 h-4" /> <span className="hidden sm:inline">{t('auth.login.link', 'Connexion')}</span>
            </Link>
            <Link
              to="/auth/register/"
              className="flex items-center gap-2 no-underline text-xs font-black italic bg-yellow-400 text-black hover:bg-yellow-500 hover:scale-105 active:scale-95 transition-all uppercase tracking-widest px-4 py-2.5 rounded-xl shadow-lg border-2 border-black/10"
            >
              <UserPlus className="w-4 h-4" /> <span className="hidden sm:inline">{t('auth.register.link', "S'inscrire")}</span>
            </Link>
          </>
        )}
      </div>

      {/* Advanced personalization panel */}
      {showPersonalizationPanel && (
        <>
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1090]"
            onClick={() => setShowPersonalizationPanel(false)}
            onKeyDown={(e) => { if (e.key === 'Escape') setShowPersonalizationPanel(false); }}
            role="button"
            tabIndex={-1}
            aria-label={t('nav.close_panel', 'Fermer le panneau')}
          />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-md bg-white dark:bg-[#0f0f1a] rounded-2xl shadow-2xl border border-black/5 dark:border-white/10 p-6 z-[1100] animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-sm font-black italic uppercase tracking-widest text-black dark:text-white">
                {t('personalization.title', 'Personnalisation')}
              </h4>
              <button
                onClick={() => setShowPersonalizationPanel(false)}
                className="grid place-items-center w-8 h-8 rounded-lg text-gray-400 hover:bg-black/5 dark:hover:bg-white/10 hover:text-black dark:hover:text-white transition-colors"
                aria-label={t('nav.close', 'Fermer')}
              >
                <X className="w-4 h-4" />
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
