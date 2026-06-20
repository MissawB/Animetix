import { create } from 'zustand';

export type ReaderMode = 'webtoon' | 'traditional' | 'interactive';
export type ReadingDirection = 'rtl' | 'ltr';
export type PageLayout = 'single' | 'double';
export type GapSize = 'none' | 'small' | 'medium';
export type ImageWidth = 'scale-80' | 'scale-100' | 'scale-xl' | 'scale-2xl' | 'scale-full';

export interface MangaPage {
  url: string;
  index: number;
}

interface PageDimension {
  width: number;
  height: number;
  isWide: boolean;
}

interface ReaderStore {
  mode: ReaderMode;
  pages: MangaPage[];
  currentPageIndex: number;
  
  // Configurations
  readingDirection: ReadingDirection;
  pageLayout: PageLayout;
  splitWidePages: boolean;
  imageWidth: ImageWidth;
  gapSize: GapSize;
  brightness: number; // 20 to 100

  // Client-side detected dimensions and local step
  pageDimensions: Record<string, PageDimension>;
  panningStep: 0 | 1;

  // Setters
  setMode: (mode: ReaderMode) => void;
  setPages: (pages: MangaPage[]) => void;
  setCurrentPageIndex: (index: number) => void;
  setReadingDirection: (direction: ReadingDirection) => void;
  setPageLayout: (layout: PageLayout) => void;
  setSplitWidePages: (split: boolean) => void;
  setImageWidth: (width: ImageWidth) => void;
  setGapSize: (size: GapSize) => void;
  setBrightness: (brightness: number) => void;
  
  // Custom navigation & layout actions
  setPageDimensions: (url: string, width: number, height: number) => void;
  setPanningStep: (step: 0 | 1) => void;
  goToNextPage: () => void;
  goToPrevPage: () => void;
}

export const useReaderStore = create<ReaderStore>((set, get) => ({
  mode: 'traditional',
  pages: [],
  currentPageIndex: 0,
  
  // Defaults
  readingDirection: 'rtl',
  pageLayout: 'single',
  splitWidePages: true,
  imageWidth: 'scale-xl',
  gapSize: 'none',
  brightness: 100,

  pageDimensions: {},
  panningStep: 0,

  setMode: (mode) => set({ mode, panningStep: 0 }),
  setPages: (pages) => set({ pages, currentPageIndex: 0, panningStep: 0 }),
  setCurrentPageIndex: (currentPageIndex) => set({ currentPageIndex, panningStep: 0 }),
  setReadingDirection: (readingDirection) => set({ readingDirection }),
  setPageLayout: (pageLayout) => set({ pageLayout, panningStep: 0 }),
  setSplitWidePages: (splitWidePages) => set({ splitWidePages, panningStep: 0 }),
  setImageWidth: (imageWidth) => set({ imageWidth }),
  setGapSize: (gapSize) => set({ gapSize }),
  setBrightness: (brightness) => set({ brightness: Math.max(20, Math.min(100, brightness)) }),

  setPageDimensions: (url, width, height) => set((state) => ({
    pageDimensions: {
      ...state.pageDimensions,
      [url]: { width, height, isWide: width / height > 1.2 }
    }
  })),
  
  setPanningStep: (panningStep) => set({ panningStep }),

  goToNextPage: () => {
    const { pages, currentPageIndex, panningStep, splitWidePages, pageDimensions, pageLayout } = get();
    if (pages.length === 0) return;

    const currentPage = pages[currentPageIndex];
    const isCurrentWide = pageDimensions[currentPage.url]?.isWide ?? false;

    // Case 1: Wide page splitting is active and current page is wide
    if (splitWidePages && isCurrentWide) {
      if (panningStep === 0) {
        set({ panningStep: 1 });
        return;
      }
    }

    // Case 2: Double page layout is active, we check if we are displaying a double page
    const nextPageIndex = currentPageIndex + 1;
    const isDoublePossible = 
      pageLayout === 'double' && 
      nextPageIndex < pages.length && 
      !isCurrentWide && 
      !(pageDimensions[pages[nextPageIndex].url]?.isWide ?? false);

    if (isDoublePossible) {
      const targetIndex = Math.min(pages.length - 1, currentPageIndex + 2);
      set({ currentPageIndex: targetIndex, panningStep: 0 });
    } else {
      // Case 3: Regular single page progression
      const targetIndex = Math.min(pages.length - 1, currentPageIndex + 1);
      set({ currentPageIndex: targetIndex, panningStep: 0 });
    }
  },

  goToPrevPage: () => {
    const { pages, currentPageIndex, panningStep, splitWidePages, pageDimensions, pageLayout } = get();
    if (pages.length === 0) return;

    const currentPage = pages[currentPageIndex];
    const isCurrentWide = pageDimensions[currentPage.url]?.isWide ?? false;

    // Case 1: Wide page splitting is active, current is wide, and we are on step 1 (left half for RTL, right half for LTR)
    if (splitWidePages && isCurrentWide && panningStep === 1) {
      set({ panningStep: 0 });
      return;
    }

    // Determine target page index when moving backwards
    let prevIndex = currentPageIndex - 1;

    if (prevIndex < 0) return; // Already at the beginning

    // Check if we were in a double page layout
    if (pageLayout === 'double' && currentPageIndex - 2 >= 0) {
      const prevPrevPage = pages[currentPageIndex - 2];
      const prevPage = pages[currentPageIndex - 1];
      const isPrevPrevWide = pageDimensions[prevPrevPage.url]?.isWide ?? false;
      const isPrevWide = pageDimensions[prevPage.url]?.isWide ?? false;

      // If the previous two pages could form a double page layout, jump back by 2
      if (!isPrevPrevWide && !isPrevWide) {
        prevIndex = currentPageIndex - 2;
      }
    }

    const prevPage = pages[prevIndex];
    const isPrevWide = pageDimensions[prevPage.url]?.isWide ?? false;

    if (splitWidePages && isPrevWide) {
      // If the previous page is wide, we land on its second half (step 1)
      set({ currentPageIndex: prevIndex, panningStep: 1 });
    } else {
      set({ currentPageIndex: prevIndex, panningStep: 0 });
    }
  }
}));

