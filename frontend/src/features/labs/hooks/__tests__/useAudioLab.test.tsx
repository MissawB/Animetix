import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAudioLab } from '../useAudioLab';
import { audioLabService } from '../../services/audioLabService';
import { AudioLabState, VoiceProfile } from '../../../../types';

vi.mock('../../services/audioLabService');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const mockState = (overrides: Partial<AudioLabState> = {}): AudioLabState =>
  ({ status: 'idle', ...overrides } as unknown as AudioLabState);

const mockProfile = (): VoiceProfile => ({ name: 'Mamoru Miyano' } as unknown as VoiceProfile);

describe('useAudioLab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the audio lab state', async () => {
    const state = mockState();
    (audioLabService.getState as Mock).mockResolvedValue(state);

    const { result } = renderHook(() => useAudioLab(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(state);
  });

  it('processAudio updates the cached state', async () => {
    const initial = mockState();
    const next = mockState({ status: 'done' } as Partial<AudioLabState>);
    (audioLabService.getState as Mock).mockResolvedValue(initial);
    (audioLabService.process as Mock).mockResolvedValue(next);

    const { result } = renderHook(() => useAudioLab(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    const payload = { media_id: 'm1', source_lang: 'ja', target_lang: 'en' };
    await act(async () => {
      await result.current.processAudio(payload);
    });

    expect((audioLabService.process as Mock).mock.calls[0][0]).toEqual(payload);
    await waitFor(() => expect(result.current.data).toEqual(next));
  });

  it('searchSeiyuu forwards args and exposes results', async () => {
    (audioLabService.getState as Mock).mockResolvedValue(mockState());
    const profiles = [mockProfile()];
    (audioLabService.searchSeiyuu as Mock).mockResolvedValue({ query: 'miyano', results: profiles });

    const { result } = renderHook(() => useAudioLab(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.searchSeiyuu('miyano', 'ja', 'jp');
    });

    expect(audioLabService.searchSeiyuu).toHaveBeenCalledWith('miyano', 'ja', 'jp');
    await waitFor(() => expect(result.current.seiyuuResults).toEqual(profiles));
  });

  it('ingestVoice calls the service', async () => {
    (audioLabService.getState as Mock).mockResolvedValue(mockState());
    const response = { message: 'ok', profile: mockProfile() };
    (audioLabService.ingestVoice as Mock).mockResolvedValue(response);

    const { result } = renderHook(() => useAudioLab(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    const payload = { name: 'Miyano', language: 'ja', query: 'miyano' };
    await act(async () => {
      const res = await result.current.ingestVoice(payload);
      expect(res).toEqual(response);
    });

    expect((audioLabService.ingestVoice as Mock).mock.calls[0][0]).toEqual(payload);
  });
});
