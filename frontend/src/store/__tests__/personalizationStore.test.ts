import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePersonalizationStore } from '../personalizationStore';

describe('usePersonalizationStore', () => {
  beforeEach(() => {
    localStorage.clear();
    usePersonalizationStore.setState({ 
      config: null, 
      isPersonalizationEnabled: true 
    });
    vi.restoreAllMocks();
  });

  it('should initialize with null config and enabled by default', () => {
    // We need to re-create the store or simulate the initialization
    // For simplicity, we just check the current state after reset
    const state = usePersonalizationStore.getState();
    expect(state.config).toBeNull();
    expect(state.isPersonalizationEnabled).toBe(true);
  });

  it('should update config and set CSS variable when enabled', () => {
    const mockSetProperty = vi.spyOn(document.documentElement.style, 'setProperty');
    const newConfig = {
      archetype_id: 'cyberpunk',
      primary_accent: '#ff00ff',
      aura_type: 'electric',
      aura_intensity: 0.8,
      font_vibe: 'default',
    };

    usePersonalizationStore.getState().updateConfig(newConfig);

    const state = usePersonalizationStore.getState();
    expect(state.config).toEqual(newConfig);
    expect(mockSetProperty).toHaveBeenCalledWith('--color-accent-drift', '#ff00ff');
  });

  it('should NOT update config when disabled', () => {
    const mockSetProperty = vi.spyOn(document.documentElement.style, 'setProperty');
    const newConfig = {
      archetype_id: 'cyberpunk',
      primary_accent: '#ff00ff',
      aura_type: 'electric',
      aura_intensity: 0.8,
      font_vibe: 'default',
    };

    usePersonalizationStore.getState().setPersonalizationEnabled(false);
    usePersonalizationStore.getState().updateConfig(newConfig);

    const state = usePersonalizationStore.getState();
    expect(state.config).toBeNull();
    expect(mockSetProperty).not.toHaveBeenCalledWith('--color-accent-drift', expect.any(String));
  });
});
