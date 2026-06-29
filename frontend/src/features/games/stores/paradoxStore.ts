import { create } from 'zustand';
import { ParadoxState } from '../../../types';
import { paradoxService } from '../services/paradoxService';
import { apiClient } from '../../../utils/apiClient';

export type ParadoxErrorKind = 'auth' | 'payment' | 'generic';

interface ParadoxStore {
  gameState: ParadoxState | null;
  isLoading: boolean;
  error: string | null;
  errorKind: ParadoxErrorKind | null;
  loadGame: () => Promise<void>;
  submitGuess: (itemId: number) => Promise<void>;
}

const classifyError = (err: unknown): { kind: ParadoxErrorKind; message: string } => {
  const status = (err as { status?: number } | undefined)?.status;
  if (status === 401 || status === 403) {
    return {
      kind: 'auth',
      message:
        "Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour générer un paradoxe.",
    };
  }
  if (status === 402) {
    return {
      kind: 'payment',
      message:
        "Solde de Berrix insuffisant. Recharge tes Bx (ou mine-en) pour lancer un paradoxe.",
    };
  }
  const message = err instanceof Error ? err.message : 'Failed to start game';
  return { kind: 'generic', message };
};

export const useParadoxStore = create<ParadoxStore>((set) => ({
  gameState: null,
  isLoading: true,
  error: null,
  errorKind: null,

  loadGame: async () => {
    set({ isLoading: true, error: null, errorKind: null });
    try {
      const state = await paradoxService.getState();
      set({ gameState: state, isLoading: false });
    } catch {
      try {
        // Fallback pour démarrer si pas d'état actif. skipToast: la page affiche
        // un message dédié (connexion / Bx) plutôt qu'un toast brut.
        const state = await apiClient('/api/v1/game/paradox/start/', {
          method: 'POST',
          skipToast: true,
        });
        set({ gameState: state, isLoading: false });
      } catch (err) {
        const { kind, message } = classifyError(err);
        set({ error: message, errorKind: kind, isLoading: false });
      }
    }
  },

  submitGuess: async (itemId: number) => {
    set({ isLoading: true, error: null, errorKind: null });
    try {
      const state = await paradoxService.submit({ intruder_id: itemId });
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const { kind, message } = classifyError(err);
      set({ error: message, errorKind: kind, isLoading: false });
    }
  }
}));
