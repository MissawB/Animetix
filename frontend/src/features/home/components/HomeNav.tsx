import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '../../../store/uiStore';
import { useAuthStore } from '../../../store/authStore';
import { Menu } from 'lucide-react';

export const HomeNav: React.FC = () => {
  const { t } = useTranslation();
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const { user, isAuthenticated } = useAuthStore();

  return (
    <div className="max-w-[1600px] mx-auto px-6 md:px-12 py-8 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <button
          className="bg-[#0F1016] text-[#F4F1E8] p-3 rounded-2xl border border-[#F4F1E8]/10 hover:border-[#E8442B]/60 hover:scale-110 active:scale-95 transition"
          onClick={() => toggleSidebar()}
        >
          <Menu className="w-6 h-6" />
        </button>
        <Link to="/" className="flex items-center no-underline">
          <img src="/static/img/logo/logo.png" alt="Logo" className="h-8" />
        </Link>
      </div>

      <div className="hidden lg:flex items-center gap-8">
        <Link
          to="/daily-challenge/"
          className="bg-[#E8442B] hover:bg-[#c9391f] text-[#F4F1E8] font-manga font-black italic uppercase text-[10px] py-2.5 px-6 rounded-xl hover:scale-105 transition-all no-underline"
        >
          {t('nav.daily', 'Défi Quotidien')}
        </Link>
        <Link
          to="/leaderboard/"
          className="font-manga text-xs hover:text-[#FDB913] transition-colors no-underline text-[#F4F1E8] uppercase font-black italic"
        >
          {t('nav.leaderboard', 'Classement')}
        </Link>
        <Link
          to="/latent-space/"
          className="font-manga text-xs hover:text-[#FDB913] transition-colors no-underline text-[#F4F1E8] uppercase font-black italic"
        >
          {t('navbar.latent', 'Latent Space')}
        </Link>
      </div>

      <div className="flex items-center gap-4 pointer-events-auto">
        {isAuthenticated && user && (
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-[10px] font-bold uppercase text-[#FDB913] tracking-widest">
              {user.tier === 'premium'
                ? t('nav.tier_boosted', 'Boosté')
                : t('nav.tier_standard', 'Standard')}
            </span>
            <span className="text-xs font-black italic font-manga text-[#F4F1E8]">
              {user.username}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
