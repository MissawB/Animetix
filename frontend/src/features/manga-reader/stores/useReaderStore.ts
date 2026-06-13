import { create } from 'zustand';

type ReaderMode = 'webtoon' | 'traditional' | 'interactive';

interface MangaPage {
  url: string;
  index: number;
}

interface ReaderStore {
  mode: ReaderMode;
  pages: MangaPage[];
  currentPageIndex: number;
  setMode: (mode: ReaderMode) => void;
  setPages: (pages: MangaPage[]) => void;
  setCurrentPageIndex: (index: number) => void;
}

export const useReaderStore = create<ReaderStore>((set) => ({
  mode: 'traditional',
  pages: [],
  currentPageIndex: 0,
  setMode: (mode) => set({ mode }),
  setPages: (pages) => set({ pages }),
  setCurrentPageIndex: (index) => set({ currentPageIndex: index }),
}));
