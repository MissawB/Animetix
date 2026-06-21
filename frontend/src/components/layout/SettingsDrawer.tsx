import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, Sun, Moon, Monitor, CheckCircle2 } from 'lucide-react';

interface SettingsDrawerProps {
  isSettingsOpen: boolean;
  theme: string;
  currentLang: 'Français' | 'English';
  toggleSettings: (forceClose?: boolean) => void;
  setTheme: (theme: string) => void;
  setCurrentLang: (lang: 'Français' | 'English') => void;
}

const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  isSettingsOpen, theme, currentLang, toggleSettings, setTheme, setCurrentLang
}) => {
  const { t } = useTranslation();

  return (
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
          aria-label="Fermer les paramètres"
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
  );
};

export default React.memo(SettingsDrawer);
