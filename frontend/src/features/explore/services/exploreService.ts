import { apiClient } from '../../../utils/apiClient';

export interface SuwayomiSource {
  id: string;
  name: string;
  lang: string;
  iconUrl?: string;
  supportsLatest: boolean;
  isConfigurable: boolean;
}

export interface SuwayomiExtension {
  name: string;
  pkgName: string;
  versionName: string;
  versionCode: number;
  lang: string;
  isNsfw: boolean;
  installed: boolean;
  hasUpdate: boolean;
  iconUrl?: string;
}

export const exploreService = {
  getSuwayomiSources: async (): Promise<SuwayomiSource[]> => {
    return apiClient('/api/v1/explore/suwayomi/sources/', { skipToast: true });
  },

  getSuwayomiExtensions: async (): Promise<SuwayomiExtension[]> => {
    return apiClient('/api/v1/explore/suwayomi/extensions/', { skipToast: true });
  },

  importSuwayomiManga: async (data: { sourceId: string; mangaUrl: string }) => {
    return apiClient('/api/v1/explore/suwayomi/import/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  triggerSuwayomiExtensionAction: async (data: { action: string; pkgName: string }) => {
    return apiClient('/api/v1/explore/suwayomi/extensions/action/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getSeichijunreiMap: async () => {
    return apiClient('/api/v1/explore/seichijunrei/');
  },

  getMarketWiki: async () => {
    return apiClient('/api/v1/market/wiki/');
  },
};
