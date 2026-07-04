import { describe, it, expect, beforeEach } from 'vitest';
import { useAdPreferenceStore } from '../adPreferenceStore';

describe('useAdPreferenceStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAdPreferenceStore.setState({ adsEnabled: true });
  });

  it('defaults to ads enabled', () => {
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(true);
  });

  it('setAdsEnabled(false) disables ads and persists "false"', () => {
    useAdPreferenceStore.getState().setAdsEnabled(false);
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(false);
    expect(localStorage.getItem('ads_enabled')).toBe('false');
  });

  it('setAdsEnabled(true) re-enables ads and persists "true"', () => {
    useAdPreferenceStore.getState().setAdsEnabled(false);
    useAdPreferenceStore.getState().setAdsEnabled(true);
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(true);
    expect(localStorage.getItem('ads_enabled')).toBe('true');
  });
});
