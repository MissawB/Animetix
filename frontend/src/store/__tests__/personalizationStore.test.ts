import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePersonalizationStore } from '../personalizationStore';

describe('usePersonalizationStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with null config', () => {
    const state = usePersonalizationStore.getState();
    expect(state.config).toBeNull();
  });

  it('should update config and set CSS variable', () => {
    const mockSetProperty = vi.spyOn(document.documentElement.style, 'setProperty');
    const newConfig = {
      archetype_id: 'cyberpunk',
      primary_accent: '#ff00ff',
      aura_type: 'glitch',
      aura_intensity: 0.8,
      font_vibe: 'tech',
    };

    usePersonalizationStore.getState().updateConfig(newConfig);

    const state = usePersonalizationStore.getState();
    expect(state.config).toEqual(newConfig);
    expect(mockSetProperty).toHaveBeenCalledWith('--color-primary-drift', '#ff00ff');
  });
});
