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
  isSafeMode: boolean;
  updateConfig: (config: VisualConfig) => void;
  setSafeMode: (enabled: boolean) => void;
}

export const usePersonalizationStore = create<PersonalizationState>((set, get) => ({
  config: null,
  isSafeMode: localStorage.getItem('personalization-safe-mode') === 'true',
  updateConfig: (config) => {
    if (get().isSafeMode) return;

    // Sync CSS variables
    document.documentElement.style.setProperty('--color-accent-drift', config.primary_accent);
    
    // Sync Font Vibe
    const body = document.body;
    body.classList.remove('font-vibe-manga', 'font-vibe-brush');
    if (config.font_vibe === 'manga') body.classList.add('font-vibe-manga');
    if (config.font_vibe === 'brush') body.classList.add('font-vibe-brush');

    set({ config });
  },
  setSafeMode: (enabled) => {
    localStorage.setItem('personalization-safe-mode', String(enabled));
    if (enabled) {
      document.documentElement.style.removeProperty('--color-accent-drift');
      document.body.classList.remove('font-vibe-manga', 'font-vibe-brush');
    }
    set({ isSafeMode: enabled });
  },
}));
