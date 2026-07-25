import React, { useState, useEffect, useRef } from 'react';
import { Save, Moon, Sun, Bot, Award, Sparkles } from 'lucide-react';
import { useCustomConfig } from '../../features/utils/hooks/useCustomConfig';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { UserConfig } from '../../types';

const CustomConfigPage: React.FC = () => {
  const { t } = useTranslation();
  const { config: serverConfig, isLoading, saveConfig, isSaving } = useCustomConfig();
  const [localConfig, setLocalConfig] = useState<UserConfig | null>(null);
  const isInitialized = useRef(false);

  // Synchronize local state with server data once on load
  useEffect(() => {
    if (serverConfig && !isInitialized.current) {
      setLocalConfig(serverConfig);
      isInitialized.current = true;
    }
  }, [serverConfig]);

  // Appliquer le thème visuel dynamiquement pour l'aperçu
  useEffect(() => {
    const visualTheme = localConfig?.visual_theme;
    if (visualTheme) {
      const themes = ['theme-naruto', 'theme-manga-classic'];
      document.documentElement.classList.remove(...themes);
      if (visualTheme !== 'default') {
        document.documentElement.classList.add(`theme-${visualTheme}`);
      }
    }
  }, [localConfig?.visual_theme]);

  if (isLoading || !localConfig)
    return (
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10]">
        <div className="max-w-4xl mx-auto px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );

  const updateConfig = (updates: Partial<UserConfig>) => {
    setLocalConfig((prev) => (prev ? { ...prev, ...updates } : null));
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="mb-6 flex items-center gap-3">
          <span className="explore-stamp -rotate-2" aria-hidden>
            調
          </span>
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
            Réglages · Personnalisation
          </span>
        </div>
        <h1 className="text-5xl font-black italic font-manga mb-12 tracking-tighter uppercase text-center md:text-left">
          CUSTOM <span className="text-[#E8442B]">CONFIG</span>
        </h1>

        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] overflow-hidden">
          <div className="p-8 sm:p-10 space-y-10">
            {/* Section Thème Visuel */}
            <section>
              <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-6 tracking-[0.2em] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#FDB913]" /> Univers Visuel
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { id: 'default', label: 'Standard', color: 'bg-[#E8442B]' },
                  { id: 'naruto', label: 'Naruto (Orange)', color: 'bg-orange-500' },
                  { id: 'manga-classic', label: 'Manga (N&B)', color: 'bg-[#F4F1E8]' },
                ].map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => updateConfig({ visual_theme: theme.id })}
                    className={`p-4 rounded-xl flex flex-col items-center gap-2 border transition-colors ${localConfig.visual_theme === theme.id || (!localConfig.visual_theme && theme.id === 'default') ? 'border-[#E8442B] bg-[#E8442B]/[0.06]' : 'border-[#F4F1E8]/10 bg-[#0B0C10] hover:border-[#FDB913]/40'}`}
                  >
                    <div className={`w-8 h-8 rounded-full ${theme.color}`}></div>
                    <span className="font-bold text-xs">{theme.label}</span>
                  </button>
                ))}
              </div>
            </section>

            {/* Section Niveau de Défi */}
            <section>
              <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-6 tracking-[0.2em] flex items-center gap-2">
                <Award className="w-4 h-4" /> Niveau de Défi
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {['easy', 'normal', 'hard'].map((d) => (
                  <button
                    key={d}
                    onClick={() => updateConfig({ difficulty: d })}
                    className={`py-4 rounded-xl font-black italic uppercase transition-colors ${localConfig.difficulty === d ? 'bg-[#FDB913] text-[#0B0C10]' : 'bg-[#0B0C10] border border-[#F4F1E8]/10 text-[#8F94A5] hover:text-[#F4F1E8]'}`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </section>

            {/* Section Interface */}
            <section>
              <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-6 tracking-[0.2em] flex items-center gap-2">
                <Sun className="w-4 h-4" /> Interface
              </h3>
              <div className="flex gap-4">
                <button
                  onClick={() => updateConfig({ theme: 'light' })}
                  className={`flex-1 p-6 rounded-xl border flex flex-col items-center gap-3 transition-colors ${localConfig.theme === 'light' ? 'border-[#FDB913] bg-[#FDB913]/[0.06]' : 'border-[#F4F1E8]/10 bg-[#0B0C10] hover:border-[#FDB913]/40'}`}
                >
                  <Sun
                    className={
                      localConfig.theme === 'light' ? 'text-[#FDB913]' : 'text-[#8F94A5]/40'
                    }
                  />
                  <span className="font-bold text-sm">Clair</span>
                </button>
                <button
                  onClick={() => updateConfig({ theme: 'dark' })}
                  className={`flex-1 p-6 rounded-xl border flex flex-col items-center gap-3 transition-colors ${localConfig.theme === 'dark' ? 'border-[#FDB913] bg-[#FDB913]/[0.06]' : 'border-[#F4F1E8]/10 bg-[#0B0C10] hover:border-[#FDB913]/40'}`}
                >
                  <Moon
                    className={
                      localConfig.theme === 'dark' ? 'text-[#FDB913]' : 'text-[#8F94A5]/40'
                    }
                  />
                  <span className="font-bold text-sm">Sombre</span>
                </button>
              </div>
            </section>

            {/* Section IA */}
            <section>
              <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-6 tracking-[0.2em] flex items-center gap-2">
                <Bot className="w-4 h-4" /> Personnalité de l'IA
              </h3>
              <select
                value={localConfig.ai_personality}
                onChange={(e) => updateConfig({ ai_personality: e.target.value })}
                className="w-full p-5 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] appearance-none cursor-pointer transition-colors"
              >
                <option value="helpful">Serviable & Précis</option>
                <option value="chaotic">Chaotique & Imprévisible</option>
                <option value="expert">Expert & Technique</option>
              </select>
            </section>

            <button
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-5 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              onClick={() => saveConfig(localConfig)}
              disabled={isSaving}
            >
              {isSaving ? (
                t('common.loading')
              ) : (
                <>
                  <Save className="w-6 h-6" /> SAUVEGARDER LES PARAMÈTRES
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomConfigPage;
