import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock, beforeEach } from 'vitest';
import { useVoiceCloning } from './useVoiceCloning';
import { cloneVoice } from '../../../api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('../../../api');

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
    mutations: {
      retry: false,
    }
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>
);

describe('useVoiceCloning Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call cloneVoice and return the result', async () => {
    const mockResult = { audio_data: 'mock-audio-base64' };
    (cloneVoice as Mock).mockResolvedValue(mockResult);

    const { result } = renderHook(() => useVoiceCloning(), { wrapper });

    const text = 'Hello world';
    const audioFile = new File([''], 'test.wav', { type: 'audio/wav' });
    const pitch = 1.0;

    await result.current.clone({ text, audioFile, pitch });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(cloneVoice).toHaveBeenCalledWith(text, audioFile, pitch);
  });

  it('should handle errors', async () => {
    const errorMessage = 'API Error';
    (cloneVoice as Mock).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useVoiceCloning(), { wrapper });

    const text = 'Hello world';
    const audioFile = new File([''], 'test.wav', { type: 'audio/wav' });
    const pitch = 1.0;

    try {
      await result.current.clone({ text, audioFile, pitch });
    } catch (e) {
      // expected
    }

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe(errorMessage);
  });
});
