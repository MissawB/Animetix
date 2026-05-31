import { create } from 'zustand';

interface VisualConfig {
  archetype_id: string;
  primary_accent: string;
  aura_type: string;
  aura_intensity: number;
  font_vibe: string;
}

interface PersonalizationState {
  config: VisualConfig | null;
  updateConfig: (config: VisualConfig) => void;
}

export const usePersonalizationStore = create<PersonalizationState>((set) => ({
  config: null,
  updateConfig: (config) => {
    // Sync CSS variables
    document.documentElement.style.setProperty('--color-primary-drift', config.primary_accent);
    set({ config });
  },
}));
