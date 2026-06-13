import { create } from 'zustand';

export interface Segment {
  id: string;
  start: number;
  end: number;
  description: string;
  type: 'emotion' | 'action' | 'dialogue';
  video_id?: string;
}

interface VideoRagState {
  segments: Segment[];
  selectedSegmentId: string | null;
  favorites: string[];
  setSegments: (segments: Segment[]) => void;
  selectSegment: (id: string | null) => void;
  toggleFavorite: (id: string) => void;
}

export const useVideoRagStore = create<VideoRagState>((set) => ({
  segments: [],
  selectedSegmentId: null,
  favorites: [],
  setSegments: (segments) => set({ segments }),
  selectSegment: (id) => set({ selectedSegmentId: id }),
  toggleFavorite: (id) => set((state) => ({
    favorites: state.favorites.includes(id)
      ? state.favorites.filter((favId) => favId !== id)
      : [...state.favorites, id],
  })),
}));
