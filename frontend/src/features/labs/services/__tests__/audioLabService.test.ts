import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AudioLabState, VoiceProfile } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { audioLabService } from '../audioLabService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): AudioLabState => ({} as AudioLabState);
const makeProfile = (): VoiceProfile => ({} as VoiceProfile);

describe('audioLabService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState fetches the base endpoint', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await audioLabService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/audio/');
    expect(result).toBe(state);
  });

  it('process posts the payload', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);
    const payload = { media_id: 'm1', source_lang: 'ja', target_lang: 'en' };

    const result = await audioLabService.process(payload);

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/audio/process/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    expect(result).toBe(state);
  });

  it('searchSeiyuu encodes the query only', async () => {
    const res = { query: 'a b', results: [] as VoiceProfile[] };
    mocked.mockResolvedValue(res);

    const result = await audioLabService.searchSeiyuu('a b');

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/audio/seiyuu/?q=a%20b');
    expect(result).toBe(res);
  });

  it('searchSeiyuu appends language and origin when provided', async () => {
    mocked.mockResolvedValue({ query: 'k', results: [] as VoiceProfile[] });

    await audioLabService.searchSeiyuu('k', 'ja', 'JP');

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/audio/seiyuu/?q=k&language=ja&origin=JP');
  });

  it('ingestVoice posts the payload', async () => {
    const res = { message: 'ok', profile: makeProfile() };
    mocked.mockResolvedValue(res);
    const payload = { name: 'Voice', language: 'ja', query: 'q' };

    const result = await audioLabService.ingestVoice(payload);

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/audio/seiyuu/ingest/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    expect(result).toBe(res);
  });
});
