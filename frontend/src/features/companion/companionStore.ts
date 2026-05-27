import { create } from 'zustand';
import { interactWithCompanion } from '../../api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface CompanionState {
  activeMentor: string;
  isOpen: boolean;
  history: Message[];
  isLoading: boolean;
  error: string | null;
  toggleOpen: () => void;
  setMentor: (mentorId: string) => void;
  sendMessage: (message: string, contextUrl?: string) => Promise<void>;
  clearHistory: () => void;
}

export const useCompanionStore = create<CompanionState>((set, get) => ({
  activeMentor: 'sensei',
  isOpen: false,
  history: [],
  isLoading: false,
  error: null,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),

  setMentor: (mentorId) => set({ activeMentor: mentorId }),

  sendMessage: async (message, contextUrl) => {
    const { activeMentor } = get();
    
    // Automatically capture current URL and Title if not provided
    const effectiveContextUrl = contextUrl || `${window.location.href} (Page: ${document.title})`;
    
    // Add user message to history immediately
    const newUserMessage: Message = { role: 'user', content: message };
    set((state) => ({ 
      history: [...state.history, newUserMessage],
      isLoading: true,
      error: null 
    }));

    try {
      const response = await interactWithCompanion(activeMentor, message, effectiveContextUrl);
      
      // Update history with the full history returned by the API
      // (or just append the response if the API only returns the new history)
      // The API we saw returns the full history (last 5 entries)
      set({ 
        history: response.history as Message[],
        isLoading: false 
      });
    } catch (err: any) {
      set({ 
        isLoading: false, 
        error: err.message || 'Failed to get response from companion' 
      });
    }
  },

  clearHistory: () => set({ history: [] }),
}));
