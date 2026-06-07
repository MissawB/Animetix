import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '../../../../store/uiStore';
import { useAuthStore } from '../../../../store/authStore';
import { Menu } from 'lucide-react';

export const HomeNav: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user, isAuthenticated } = useAuthStore();

  return (
    <div className="max-w-[1600px] mx-auto px-6 md:px-12 py-8 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <button 
          className="bg-black text-white p-3 rounded-2xl hover:scale-110 active:scale-95 transition shadow-lg" 
          onClick={() => toggleSidebar()}
        >
          <Menu className="w-6 h-6" />
        </button>
        <Link to="/" className="flex items-center no-underline">
          <img src="/static/img/logo/white_logo.png" alt="Logo" className="h-8 dark:hidden" />
          <img src="/static/img/logo/logo.png" alt="Logo" className="h-8 hidden dark:block" />
        </Link>
      </div>
      
      <div className="hidden lg:flex items-center gap-8">
        <Link 
          to="/daily-challenge/" 
          className="bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font text-[10px] py-2.5 px-6 rounded-xl shadow-lg hover:scale-105 transition-all no-underline"
        >
          {t('nav.daily', 'Défi Quotidien')}
        </Link>
        <Link 
          to="/leaderboard/" 
          className="manga-font text-xs hover:text-yellow-400 transition-colors no-underline text-black dark:text-white uppercase font-black italic"
        >
          {t('nav.leaderboard', 'Classement')}
        </Link>
        <Link 
          to="/latent-space/" 
          className="manga-font text-xs hover:text-yellow-400 transition-colors no-underline text-black dark:text-white uppercase font-black italic"
        >
          {t('navbar.latent', 'Latent Space')}
        </Link>
      </div>

      <div className="flex items-center gap-4 pointer-events-auto">
        {isAuthenticated && user && (
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-[10px] font-bold uppercase text-yellow-600 dark:text-yellow-400 tracking-widest">
              {user.tier === 'premium' ? 'Premium' : 'Explorateur'}
            </span>
            <span className="text-xs font-black italic manga-font text-black dark:text-white">{user.username}</span>
          </div>
        )}
      </div>
    </div>
  );
};
