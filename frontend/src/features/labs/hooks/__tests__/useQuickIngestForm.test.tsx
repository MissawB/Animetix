import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import type { FormEvent } from 'react';
import { useQuickIngestForm } from '../useQuickIngestForm';
import type { VoiceProfile } from '../../../../types';
import type { IngestVoicePayload } from '../../services/audioLabService';

const profile = { id: 7, name: 'Kana' } as unknown as VoiceProfile;
const fakeEvent = () => ({ preventDefault: vi.fn() }) as unknown as FormEvent;

describe('useQuickIngestForm', () => {
  let ingestVoice: Mock<(p: IngestVoicePayload) => Promise<{ message: string; profile: VoiceProfile }>>;
  let onIngested: Mock<(p: VoiceProfile) => void>;

  beforeEach(() => {
    ingestVoice = vi.fn<(p: IngestVoicePayload) => Promise<{ message: string; profile: VoiceProfile }>>();
    ingestVoice.mockResolvedValue({ message: 'ok', profile });
    onIngested = vi.fn<(p: VoiceProfile) => void>();
  });

  const setup = () => renderHook(() => useQuickIngestForm({ ingestVoice, onIngested }));

  it('toggles and closes the panel', () => {
    const { result } = setup();
    expect(result.current.isOpen).toBe(false);
    act(() => result.current.toggle());
    expect(result.current.isOpen).toBe(true);
    act(() => result.current.close());
    expect(result.current.isOpen).toBe(false);
  });

  it('rejects an empty form without calling ingestVoice', async () => {
    const { result } = setup();
    await act(async () => {
      await result.current.submit(fakeEvent());
    });
    expect(ingestVoice).not.toHaveBeenCalled();
    expect(result.current.error).toBe('Le nom et la source sont requis.');
  });

  it('ingests, notifies, and resets on a valid submit', async () => {
    const { result } = setup();
    act(() => {
      result.current.toggle();
      result.current.setName('Kana');
      result.current.setLanguage('french');
      result.current.setSource('https://youtu.be/x');
    });

    await act(async () => {
      await result.current.submit(fakeEvent());
    });

    expect(ingestVoice).toHaveBeenCalledWith({ name: 'Kana', language: 'french', query: 'https://youtu.be/x' });
    expect(onIngested).toHaveBeenCalledWith(profile);
    expect(result.current.isOpen).toBe(false);
    expect(result.current.name).toBe('');
    expect(result.current.source).toBe('');
    expect(result.current.error).toBe('');
  });

  it('surfaces the error message when ingestVoice throws', async () => {
    ingestVoice.mockRejectedValue(new Error('Quota dépassé'));
    const { result } = setup();
    act(() => {
      result.current.setName('Kana');
      result.current.setSource('query');
    });

    await act(async () => {
      await result.current.submit(fakeEvent());
    });

    expect(result.current.error).toBe('Quota dépassé');
    expect(onIngested).not.toHaveBeenCalled();
  });
});
