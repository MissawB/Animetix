import React from 'react';
import { useTranslation } from 'react-i18next';
import { usePersonalizationStore } from '../../store/personalizationStore';
import { Sparkles, Sliders, Type, Palette, Zap, Info } from 'lucide-react';

const ARCHETYPES = [
  'shonen_hero',
  'seinen_mystery',
  'cyberpunk',
  'tsundere',
  'kuudere',
  'yandere',
  'shonen',
  'seinen',
  'mahou_shoujo',
  'isekai',
  'slice_of_life',
  'mecha',
  'horror',
  'fantasy',
  'romance',
  'psychological',
  'sports',
];

export const PersonalizationPanel: React.FC = () => {
  const { t } = useTranslation();
  const { settings, updateSettings, isPersonalizationEnabled, setPersonalizationEnabled } =
    usePersonalizationStore();

  if (!isPersonalizationEnabled) {
    return (
      <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 bg-[#0B0C10] p-6 text-center text-[#F4F1E8]">
        <Sparkles className="mx-auto mb-3 h-8 w-8 text-[#8F94A5]/50" />
        <p className="mb-6 text-sm font-medium italic text-[#8F94A5]">
          {t('personalization.disabled_text', 'Hyper-Personalization is currently disabled.')}
        </p>
        <button
          onClick={() => setPersonalizationEnabled(true)}
          className="w-full rounded-xl bg-[#E8442B] py-3 text-xs font-black uppercase italic tracking-widest text-[#F4F1E8] transition-colors hover:bg-[#c93a24]"
        >
          {t('personalization.enable_button', 'Enable System')}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 text-[#F4F1E8]">
      {/* Mode Selection */}
      <div className="flex flex-col gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
        <div className="flex items-center gap-3">
          <Zap
            className={`h-5 w-5 shrink-0 ${settings.mode === 'auto' ? 'animate-pulse text-[#FDB913]' : 'text-[#8F94A5]'}`}
          />
          <div className="min-w-0">
            <p className="truncate text-xs font-black uppercase italic tracking-tighter">
              {t('personalization.mode_title', 'Personalization Mode')}
            </p>
            <p className="mt-1 truncate text-[9px] font-bold uppercase leading-none tracking-widest text-[#8F94A5]">
              {settings.mode === 'auto'
                ? t('personalization.mode_auto', 'Autonomous Evolution')
                : t('personalization.mode_manual', 'Manual Selection')}
            </p>
          </div>
        </div>
        <div className="flex w-full rounded-xl bg-[#0F1016] p-1">
          <button
            onClick={() => updateSettings({ mode: 'auto' })}
            className={`flex-1 rounded-lg px-2 py-1.5 text-[10px] font-black uppercase transition-all ${
              settings.mode === 'auto'
                ? 'bg-[#E8442B] text-[#F4F1E8]'
                : 'text-[#8F94A5] hover:text-[#F4F1E8]'
            }`}
          >
            {t('personalization.btn_auto', 'Auto')}
          </button>
          <button
            onClick={() => updateSettings({ mode: 'manual' })}
            className={`flex-1 rounded-lg px-2 py-1.5 text-[10px] font-black uppercase transition-all ${
              settings.mode === 'manual'
                ? 'bg-[#E8442B] text-[#F4F1E8]'
                : 'text-[#8F94A5] hover:text-[#F4F1E8]'
            }`}
          >
            {t('personalization.btn_manual', 'Manual')}
          </button>
        </div>
      </div>

      {/* Manual Selection Grid */}
      {settings.mode === 'manual' && (
        <div className="custom-scrollbar grid max-h-48 grid-cols-2 gap-2 overflow-y-auto pr-2">
          {ARCHETYPES.map((arch) => (
            <button
              key={arch}
              onClick={() => updateSettings({ manual_archetype: arch })}
              className={`rounded-lg border p-2 text-[9px] font-black uppercase tracking-widest transition-all ${
                settings.manual_archetype === arch
                  ? 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]'
                  : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
              }`}
            >
              {arch.replace('_', ' ')}
            </button>
          ))}
        </div>
      )}

      {/* Intensity Slider */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#8F94A5]">
            <Sliders className="h-4 w-4" />
            <p className="text-xs font-black uppercase tracking-widest">
              {t('personalization.intensity_title', 'Aura Intensity')}
            </p>
          </div>
          <span className="rounded-lg border border-[#FDB913]/20 bg-[#FDB913]/10 px-2 py-0.5 font-mono text-xs font-black italic text-[#FDB913]">
            {Math.round(settings.intensity_multiplier * 100)}%
          </span>
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
            className="h-2 w-full cursor-pointer appearance-none rounded-full bg-[#F4F1E8]/10 accent-[#FDB913]"
          />
        </div>
        <div className="flex justify-between px-1 text-[8px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
          <span>{t('personalization.intensity_subtle', 'Subtle')}</span>
          <span>{t('personalization.intensity_normal', 'Normal')}</span>
          <span>{t('personalization.intensity_overdrive', 'Overdrive')}</span>
        </div>
      </div>

      {/* Feature Toggles — trois encres : aura (shu), fonts (or), accent (indigo) */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={() =>
            updateSettings({ features: { ...settings.features, aura: !settings.features.aura } })
          }
          className={`flex flex-col items-center gap-2 rounded-2xl border p-4 transition-all ${
            settings.features.aura
              ? 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]'
              : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] opacity-60 hover:opacity-100'
          }`}
        >
          <Sparkles className="h-5 w-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">
            {t('personalization.feature_aura', 'Aura')}
          </span>
        </button>
        <button
          onClick={() =>
            updateSettings({ features: { ...settings.features, font: !settings.features.font } })
          }
          className={`flex flex-col items-center gap-2 rounded-2xl border p-4 transition-all ${
            settings.features.font
              ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]'
              : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] opacity-60 hover:opacity-100'
          }`}
        >
          <Type className="h-5 w-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">
            {t('personalization.feature_fonts', 'Fonts')}
          </span>
        </button>
        <button
          onClick={() =>
            updateSettings({
              features: { ...settings.features, accent: !settings.features.accent },
            })
          }
          className={`flex flex-col items-center gap-2 rounded-2xl border p-4 transition-all ${
            settings.features.accent
              ? 'border-[#5D7FD3] bg-[#5D7FD3]/10 text-[#5D7FD3]'
              : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] opacity-60 hover:opacity-100'
          }`}
        >
          <Palette className="h-5 w-5" />
          <span className="text-[9px] font-black uppercase tracking-widest">
            {t('personalization.feature_accent', 'Accent')}
          </span>
        </button>
      </div>

      <div className="flex gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-[#E8442B]" />
        <p className="text-[10px] font-medium uppercase leading-relaxed tracking-wider text-[#8F94A5]">
          {t(
            'personalization.info_text',
            'Your UI evolves dynamically based on your behavior. Manual mode allows you to "lock" a specific archetype, while Auto mode lets the system drift naturally.',
          )}
        </p>
      </div>
    </div>
  );
};
