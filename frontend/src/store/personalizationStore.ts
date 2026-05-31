import { create } from 'zustand';
import { apiClient } from '../utils/apiClient';

interface VisualConfig {
  archetype_id: string;
  primary_accent: string;
  aura_type: string;
  aura_intensity: number;
  font_vibe: string;
}

interface PersonalizationSettings {
  mode: 'auto' | 'manual';
  manual_archetype?: string;
  intensity_multiplier: number;
  features: {
    aura: boolean;
    font: boolean;
    accent: boolean;
  };
}

interface PersonalizationState {
  config: VisualConfig | null;
  settings: PersonalizationSettings;
  isPersonalizationEnabled: boolean;
  updateConfig: (config: VisualConfig) => void;
  setPersonalizationEnabled: (enabled: boolean) => void;
  updateSettings: (settings: Partial<PersonalizationSettings>) => Promise<void>;
  fetchSettings: () => Promise<void>;
}

const DEFAULT_SETTINGS: PersonalizationSettings = {
  mode: 'auto',
  intensity_multiplier: 1.0,
  features: {
    aura: true,
    font: true,
    accent: true,
  },
};

export const usePersonalizationStore = create<PersonalizationState>((set, get) => ({
  config: null,
  settings: DEFAULT_SETTINGS,
  isPersonalizationEnabled: localStorage.getItem('personalization-enabled') !== 'false',
  
  updateConfig: (config) => {
    if (!get().isPersonalizationEnabled) return;

    // Sync CSS variables
    document.documentElement.style.setProperty('--color-accent-drift', config.primary_accent);
    
    // Sync Font Vibe
    const body = document.body;
    body.classList.remove('font-vibe-manga', 'font-vibe-brush');
    if (config.font_vibe === 'manga') body.classList.add('font-vibe-manga');
    if (config.font_vibe === 'brush') body.classList.add('font-vibe-brush');

    set({ config });
  },

  setPersonalizationEnabled: (enabled) => {
    localStorage.setItem('personalization-enabled', String(enabled));
    if (!enabled) {
      document.documentElement.style.removeProperty('--color-accent-drift');
      document.body.classList.remove('font-vibe-manga', 'font-vibe-brush');
      set({ config: null });
    }
    set({ isPersonalizationEnabled: enabled });
  },

  updateSettings: async (newSettings) => {
    const updated = { ...get().settings, ...newSettings };
    set({ settings: updated });
    
    try {
      await apiClient('/api/v1/profiles/update_personalization/', {
        method: 'POST',
        body: JSON.stringify(updated),
      });
    } catch (error) {
      console.error('Failed to sync personalization settings', error);
    }
  },

  fetchSettings: async () => {
    try {
      const data = await apiClient('/api/v1/profiles/me/');
      if (data?.personalization_settings) {
        set({ settings: { ...DEFAULT_SETTINGS, ...data.personalization_settings } });
      }
    } catch (error) {
      console.error('Failed to fetch personalization settings', error);
    }
  },
}));
