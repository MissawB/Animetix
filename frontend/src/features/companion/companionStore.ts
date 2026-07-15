import { create } from 'zustand';
import { companionService } from './services/companionService';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface CompanionState {
  activeMentor: string;
  customPersona: string;
  isOpen: boolean;
  history: Message[];
  isLoading: boolean;
  error: string | null;
  toggleOpen: () => void;
  setMentor: (mentorId: string) => void;
  setCustomPersona: (persona: string) => void;
  sendMessage: (message: string, contextUrl?: string) => Promise<void>;
  clearHistory: () => void;
}

export const useCompanionStore = create<CompanionState>((set, get) => ({
  activeMentor: 'sensei',
  customPersona: '',
  isOpen: false,
  history: [],
  isLoading: false,
  error: null,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),

  setMentor: (mentorId) => set({ activeMentor: mentorId }),

  setCustomPersona: (persona) => set({ customPersona: persona }),

  sendMessage: async (message, contextUrl) => {
    const { activeMentor, customPersona } = get();

    // Automatically capture current URL and Title if not provided
    const effectiveContextUrl = contextUrl || `${window.location.href} (Page: ${document.title})`;

    // Add user message to history immediately
    const newUserMessage: Message = { role: 'user', content: message };
    set((state) => ({
      history: [...state.history, newUserMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await companionService.interact(
        activeMentor,
        message,
        effectiveContextUrl,
        activeMentor === 'custom' ? customPersona : undefined,
      );

      // Update history with the full history returned by the API
      // (or just append the response if the API only returns the new history)
      // The API we saw returns the full history (last 5 entries)
      set({
        history: response.history as Message[],
        isLoading: false,
      });
    } catch (err) {
      const error = err as Error;
      set({
        isLoading: false,
        error: error.message || 'Failed to get response from companion',
      });
    }
  },

  clearHistory: () => set({ history: [] }),
}));
