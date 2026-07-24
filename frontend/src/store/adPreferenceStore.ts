import { create } from 'zustand';

interface AdPreferenceState {
  // Whether ads are shown. AdSlot renders nothing when this is false.
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
