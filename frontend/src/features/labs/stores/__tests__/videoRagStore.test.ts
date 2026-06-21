import { describe, it, expect, beforeEach } from 'vitest';
import { useVideoRagStore, type Segment } from '../videoRagStore';

const seg = (id: string): Segment => ({
  id,
  start: 0,
  end: 10,
  description: `segment ${id}`,
  type: 'action',
});

describe('useVideoRagStore', () => {
  beforeEach(() => {
    useVideoRagStore.setState({ segments: [], selectedSegmentId: null, favorites: [] });
  });

  it('initializes empty', () => {
    const state = useVideoRagStore.getState();
    expect(state.segments).toEqual([]);
    expect(state.selectedSegmentId).toBeNull();
    expect(state.favorites).toEqual([]);
  });

  it('setSegments replaces the segments array', () => {
    const segments = [seg('a'), seg('b')];
    useVideoRagStore.getState().setSegments(segments);
    expect(useVideoRagStore.getState().segments).toEqual(segments);
  });

  it('selectSegment sets and clears the selected id', () => {
    useVideoRagStore.getState().selectSegment('a');
    expect(useVideoRagStore.getState().selectedSegmentId).toBe('a');

    useVideoRagStore.getState().selectSegment(null);
    expect(useVideoRagStore.getState().selectedSegmentId).toBeNull();
  });

  it('toggleFavorite adds an id when absent', () => {
    useVideoRagStore.getState().toggleFavorite('a');
    expect(useVideoRagStore.getState().favorites).toEqual(['a']);
  });

  it('toggleFavorite removes an id when already present', () => {
    useVideoRagStore.setState({ favorites: ['a', 'b'] });
    useVideoRagStore.getState().toggleFavorite('a');
    expect(useVideoRagStore.getState().favorites).toEqual(['b']);
  });

  it('toggleFavorite is idempotent across two toggles', () => {
    const { toggleFavorite } = useVideoRagStore.getState();
    toggleFavorite('x');
    toggleFavorite('x');
    expect(useVideoRagStore.getState().favorites).toEqual([]);
  });

  it('toggleFavorite preserves other favorites when adding', () => {
    useVideoRagStore.setState({ favorites: ['a'] });
    useVideoRagStore.getState().toggleFavorite('b');
    expect(useVideoRagStore.getState().favorites).toEqual(['a', 'b']);
  });
});
