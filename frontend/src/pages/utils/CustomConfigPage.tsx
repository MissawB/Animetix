import React, { useState, useEffect } from 'react';
import { Save, Moon, Sun, Bot, Award, Sparkles } from 'lucide-react';
import { useCustomConfig } from '../../features/utils/hooks/useCustomConfig';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from "../../components/ui/Skeleton";

const CustomConfigPage: React.FC = () => {
  const { t } = useTranslation();
  const { config: serverConfig, isLoading, saveConfig, isSaving } = useCustomConfig();
  const [localConfig, setLocalConfig] = useState<any>(null);

  useEffect(() => {
    if (serverConfig) setLocalConfig(serverConfig);
  }, [serverConfig]);

  // Appliquer le thème visuel dynamiquement pour l'aperçu
  useEffect(() => {
    if (localConfig?.visual_theme) {
      const themes = ['theme-naruto', 'theme-manga-classic'];
      document.documentElement.classList.remove(...themes);
      if (localConfig.visual_theme !== 'default') {
        document.documentElement.classList.add(`theme-${localConfig.visual_theme}`);
      }
    }
  }, [localConfig?.visual_theme]);

  if (isLoading || !localConfig) return (
    <div className="max-w-4xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-5xl font-black italic manga-font mb-12 tracking-tighter uppercase text-center md:text-left">
        CUSTOM <span className="text-yellow-400">CONFIG</span>
      </h1>

      <Card padding="none" className="overflow-hidden">
        <div className="p-10 space-y-10">

          {/* Section Thème Visuel */}
          <section>
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-500" /> Univers Visuel
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { id: 'default', label: 'Standard', color: 'bg-blue-500' },
                  { id: 'naruto', label: 'Naruto (Orange)', color: 'bg-orange-500' },
                  { id: 'manga-classic', label: 'Manga (N&B)', color: 'bg-black' }
                ].map((theme) => (
                    <button 
                        key={theme.id}
                        onClick={() => setLocalConfig({...localConfig, visual_theme: theme.id})}
                        className={`p-4 rounded-2xl flex flex-col items-center gap-2 border-2 transition-all ${localConfig.visual_theme === theme.id || (!localConfig.visual_theme && theme.id === 'default') ? 'border-brand-primary bg-brand-primary/5' : 'border-transparent bg-gray-50 dark:bg-navy-900'}`}
                    >
                        <div className={`w-8 h-8 rounded-full ${theme.color} shadow-inner`}></div>
                        <span className="font-bold text-xs">{theme.label}</span>
                    </button>
                ))}
            </div>
          </section>

          {/* Section Apparence */}
          <section>
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2">
                <Award className="w-4 h-4" /> Niveau de Défi
            </h3>
            <div className="grid grid-cols-3 gap-4">
                {['easy', 'normal', 'hard'].map((d) => (
                    <button 
                        key={d}
                        onClick={() => setLocalConfig({...localConfig, difficulty: d})}
                        className={`py-4 rounded-2xl font-black italic uppercase transition-all ${localConfig.difficulty === d ? 'bg-yellow-400 text-black shadow-lg scale-105' : 'bg-gray-50 dark:bg-navy-900 opacity-40 hover:opacity-100'}`}
                    >
                        {d}
                    </button>
                ))}
            </div>
          </section>

          {/* Section Apparence */}
          <section>
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2">
                <Sun className="w-4 h-4" /> Interface
            </h3>
            <div className="flex gap-4">
                <button 
                    onClick={() => setLocalConfig({...localConfig, theme: 'light'})}
                    className={`flex-1 p-6 rounded-3xl border-2 flex flex-col items-center gap-3 transition-all ${localConfig.theme === 'light' ? 'border-yellow-400 bg-yellow-400/5' : 'border-transparent bg-gray-50 dark:bg-navy-900 hover:border-gray-200 dark:hover:border-white/10'}`}
                >
                    <Sun className={localConfig.theme === 'light' ? 'text-yellow-500' : 'opacity-20'} />
                    <span className="font-bold text-sm">Clair</span>
                </button>
                <button 
                    onClick={() => setLocalConfig({...localConfig, theme: 'dark'})}
                    className={`flex-1 p-6 rounded-3xl border-2 flex flex-col items-center gap-3 transition-all ${localConfig.theme === 'dark' ? 'border-yellow-400 bg-yellow-400/5' : 'border-transparent bg-gray-50 dark:bg-navy-900 hover:border-gray-200 dark:hover:border-white/10'}`}
                >
                    <Moon className={localConfig.theme === 'dark' ? 'text-blue-500' : 'opacity-20'} />
                    <span className="font-bold text-sm">Sombre</span>
                </button>
            </div>
          </section>

          {/* Section IA */}
          <section>
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2">
                <Bot className="w-4 h-4" /> Personnalité de l'IA
            </h3>
            <select 
                value={localConfig.ai_personality}
                onChange={(e) => setLocalConfig({...localConfig, ai_personality: e.target.value})}
                className="w-full p-5 rounded-2xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold appearance-none cursor-pointer"
            >
                <option value="helpful">Serviable & Précis</option>
                <option value="chaotic">Chaotique & Imprévisible</option>
                <option value="expert">Expert & Technique</option>
            </select>
          </section>

          <Button 
            variant="primary" 
            fullWidth 
            size="lg"
            className="bg-black text-white hover:bg-gray-900 py-6"
            onClick={() => saveConfig(localConfig)}
            disabled={isSaving}
          >
            {isSaving ? t('common.loading') : <><Save className="w-6 h-6" /> SAUVEGARDER LES PARAMÈTRES</>}
          </Button>

        </div>
      </Card>
    </div>
  );
};

export default CustomConfigPage;


