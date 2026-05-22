import { del, get, set } from 'idb-keyval';
import {
  PersistedClient,
  Persister,
} from '@tanstack/react-query-persist-client';

/**
 * Crée un persister utilisant IndexedDB (via idb-keyval)
 * Plus robuste et performant que le LocalStorage pour de gros volumes de données
 */
export function createPersister(key = 'ANIMETIX_QUERY_OFFLINE_CACHE'): Persister {
  return {
    persistClient: async (client: PersistedClient) => {
      await set(key, client);
    },
    restoreClient: async () => {
      return await get<PersistedClient>(key);
    },
    removeClient: async () => {
      await del(key);
    },
  };
}
