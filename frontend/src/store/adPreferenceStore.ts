import { create } from 'zustand';

interface AdPreferenceState {
  // Whether ads are shown. Disabling ads also pauses passive Bx mining, because
  // AdSlot renders nothing when this is false (no ad mounted -> adSlotsVisible 0).
  adsEnabled: boolean;
  setAdsEnabled: (enabled: boolean) => void;
}

export const useAdPreferenceStore = create<AdPreferenceState>((set) => ({
  adsEnabled: localStorage.getItem('ads_enabled') !== 'false',
  setAdsEnabled: (enabled) => {
    localStorage.setItem('ads_enabled', String(enabled));
    set({ adsEnabled: enabled });
  },
}));
