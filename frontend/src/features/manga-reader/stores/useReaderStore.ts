import { create } from 'zustand';

type ReaderMode = 'webtoon' | 'traditional' | 'interactive';

interface ReaderStore {
  mode: ReaderMode;
  setMode: (mode: ReaderMode) => void;
}

export const useReaderStore = create<ReaderStore>((set) => ({
  mode: 'traditional',
  setMode: (mode) => set({ mode }),
}));
