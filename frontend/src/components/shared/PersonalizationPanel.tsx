import React from 'react';
import { useTranslation } from 'react-i18next';
import { usePersonalizationStore } from '../../store/personalizationStore';
import { Sparkles, Sliders, Type, Palette, Zap, Info } from 'lucide-react';

const ARCHETYPES = [
  "shonen_hero", "seinen_mystery", "cyberpunk", "tsundere", "kuudere", "yandere",
  "shonen", "seinen", "mahou_shoujo", "isekai", "slice_of_life", "mecha",
  "horror", "fantasy", "romance", "psychological", "sports"
];

export const PersonalizationPanel: React.FC = () => {
  const { t } = useTranslation();
  const { settings, updateSettings, isPersonalizationEnabled, setPersonalizationEnabled } = usePersonalizationStore();

  if (!isPersonalizationEnabled) {
    return (
      <div className="p-6 bg-gray-50 dark:bg-black/20 rounded-2xl border-2 border-dashed border-black/5 dark:border-white/5 text-center text-black dark:text-white transition-colors duration-500">
        <Sparkles className="w-8 h-8 text-gray-400 mx-auto mb-3 opacity-50" />
        <p className="text-sm font-bold italic mb-6">{t('personalization.disabled_text', 'Hyper-Personalization is currently disabled.')}</p>
        <button 
          onClick={() => setPersonalizationEnabled(true)}
          className="w-full py-3 bg-blue-500 text-white text-xs font-black italic uppercase tracking-widest rounded-xl hover:bg-blue-600 transition shadow-lg"
        >
          {t('personalization.enable_button', 'Enable System')}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 text-black dark:text-white transition-colors duration-500">
      {/* Mode Selection */}
      <div className="flex flex-col gap-4 p-4 bg-gray-50 dark:bg-black/20 rounded-2xl border border-black/5 dark:border-white/5 shadow-inner">
        <div className="flex items-center gap-3">
          <Zap className={`w-5 h-5 shrink-0 ${settings.mode === 'auto' ? 'text-yellow-400 animate-pulse' : 'text-gray-400'}`} />
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-tighter italic truncate">{t('personalization.mode_title', 'Personalization Mode')}</p>
            <p className="text-[9px] text-gray-500 dark:text-gray-400 uppercase font-bold tracking-widest leading-none mt-1 truncate">
              {settings.mode === 'auto' ? t('personalization.mode_auto', 'Autonomous Evolution') : t('personalization.mode_manual', 'Manual Selection')}
            </p>
          </div>
        </div>
        <div className="flex bg-gray-200 dark:bg-black/40 p-1 rounded-xl w-full">
          <button 
            onClick={() => updateSettings({ mode: 'auto' })}
            className={`flex-1 px-2 py-1.5 text-[10px] font-black uppercase rounded-lg transition-all ${settings.mode === 'auto' ? 'bg-white dark:bg-white/10 shadow-md text-blue-500' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
          >
            {t('personalization.btn_auto', 'Auto')}
          </button>
          <button 
            onClick={() => updateSettings({ mode: 'manual' })}
            className={`flex-1 px-2 py-1.5 text-[10px] font-black uppercase rounded-lg transition-all ${settings.mode === 'manual' ? 'bg-white dark:bg-white/10 shadow-md text-orange-500' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
          >
            {t('personalization.btn_manual', 'Manual')}
          </button>
        </div>
      </div>

      {/* Manual Selection Grid */}
      {settings.mode === 'manual' && (
        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
          {ARCHETYPES.map(arch => (
            <button
              key={arch}
              onClick={() => updateSettings({ manual_archetype: arch })}
              className={`p-2 text-[9px] font-black uppercase tracking-widest rounded-lg border-2 transition-all ${settings.manual_archetype === arch ? 'bg-orange-500/10 border-orange-500 text-orange-500' : 'bg-gray-50 dark:bg-black/20 border-transparent text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'}`}
            >
              {arch.replace('_', ' ')}
            </button>
          ))}
        </div>
      )}

      {/* Intensity Slider */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-500">
            <Sliders className="w-4 h-4" />
            <p className="text-xs font-black uppercase tracking-widest">{t('personalization.intensity_title', 'Aura Intensity')}</p>
          </div>
          <span className="text-xs font-mono font-black italic text-blue-500 bg-blue-500/5 px-2 py-0.5 rounded-lg border border-blue-500/10">{Math.round(settings.intensity_multiplier * 100)}%</span>
        </div>
        <div className="px-1">
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={settings.intensity_multiplier}
            onChange={(e) => updateSettings({ intensity_multiplier: parseFloat(e.target.value) })}
            aria-label={t('personalization.intensity_title', 'Aura Intensity')}
            className="w-full h-2 bg-gray-200 dark:bg-black/40 rounded-full appearance-none cursor-pointer accent-blue-500"
          />
        </div>
        <div className="flex justify-between text-[8px] font-black text-gray-400 dark:text-gray-500 uppercase tracking-[0.2em] px-1">
          <span>{t('personalization.intensity_subtle', 'Subtle')}</span>
          <span>{t('personalization.intensity_normal', 'Normal')}</span>
          <span>{t('personalization.intensity_overdrive', 'Overdrive')}</span>
        </div>
      </div>

      {/* Feature Toggles */}
      <div className="grid grid-cols-3 gap-3">
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, aura: !settings.features.aura } })}
          className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${settings.features.aura ? 'bg-brand-accent/10 border-brand-accent text-brand-accent shadow-lg shadow-brand-accent/5' : 'bg-gray-50 dark:bg-black/20 border-transparent text-gray-400 opacity-50 hover:opacity-80'}`}
        >
          <Sparkles className="w-5 h-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">{t('personalization.feature_aura', 'Aura')}</span>
        </button>
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, font: !settings.features.font } })}
          className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${settings.features.font ? 'bg-blue-500/10 border-blue-500 text-blue-500 shadow-lg shadow-blue-500/5' : 'bg-gray-50 dark:bg-black/20 border-transparent text-gray-400 opacity-50 hover:opacity-80'}`}
        >
          <Type className="w-5 h-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">{t('personalization.feature_fonts', 'Fonts')}</span>
        </button>
        <button 
          onClick={() => updateSettings({ features: { ...settings.features, accent: !settings.features.accent } })}
          className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${settings.features.accent ? 'bg-purple-500/10 border-purple-500 text-purple-500 shadow-lg shadow-purple-500/5' : 'bg-gray-50 dark:bg-black/20 border-transparent text-gray-400 opacity-50 hover:opacity-80'}`}
        >
          <Palette className="w-5 h-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">{t('personalization.feature_accent', 'Accent')}</span>
        </button>
      </div>

      <div className="p-4 bg-blue-500/5 dark:bg-blue-500/10 rounded-2xl border border-blue-500/10 flex gap-4">
        <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
        <p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold leading-relaxed italic uppercase tracking-wider">
          {t('personalization.info_text', 'Your UI evolves dynamically based on your behavior. Manual mode allows you to "lock" a specific archetype, while Auto mode lets the system drift naturally.')}
        </p>
      </div>
    </div>
  );
};
