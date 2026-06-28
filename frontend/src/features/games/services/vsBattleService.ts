import { apiClient } from '../../../utils/apiClient';
import type { ArenaCharacter } from '../../../types';

export const vsBattleService = {
  getArenaFeed: async () => {
    return apiClient('/api/v1/game/vs_battle/arena/');
  },
  getCharacters: async (): Promise<ArenaCharacter[]> => {
    const data = (await apiClient('/api/v1/game/vs_battle/characters/', { skipToast: true })) as {
      characters?: ArenaCharacter[];
    };
    return data?.characters ?? [];
  },
  runBattle: async (charA: string, charB: string, franchiseA?: string, franchiseB?: string) => {
    return apiClient('/api/v1/game/vs_battle/run/', {
        method: 'POST',
        body: JSON.stringify({ char_a: charA, char_b: charB, char_a_franchise: franchiseA, char_b_franchise: franchiseB }),
        headers: { 'Content-Type': 'application/json' }
    });
  },
  likeBattle: async (id: number) => {
    return apiClient(`/api/v1/game/vs_battle/${id}/like/`, { method: 'POST' });
  }
};
