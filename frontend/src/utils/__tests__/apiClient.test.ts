import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient } from '../apiClient';
import { useToastStore } from '../../store/toastStore';
import { usePersonalizationStore } from '../../store/personalizationStore';
import { auth } from '../firebase';

// firebase.ts runs real Firebase init at module load; replace it with a stub
// `auth` object whose currentUser we control per-test.
vi.mock('../firebase', () => ({
  auth: { currentUser: null as { getIdToken: () => Promise<string> } | null },
}));

const addToast = vi.fn();
vi.mock('../../store/toastStore', () => ({
  useToastStore: { getState: vi.fn(() => ({ addToast })) },
}));

const updateConfig = vi.fn();
vi.mock('../../store/personalizationStore', () => ({
  usePersonalizationStore: { getState: vi.fn(() => ({ updateConfig })) },
}));

type FetchResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

const mockFetch = (response: FetchResponse) => {
  const fn = vi.fn().mockResolvedValue(response as unknown as Response);
  global.fetch = fn as unknown as typeof fetch;
  return fn;
};

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (auth as { currentUser: unknown }).currentUser = null;
    // Reset cookies between tests.
    Object.defineProperty(document, 'cookie', {
      writable: true,
      configurable: true,
      value: '',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns parsed JSON on a successful response', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ id: 7 }) });
    const data = await apiClient('/api/thing');
    expect(data).toEqual({ id: 7 });
  });

  it('returns null for a 204 No Content response without parsing JSON', async () => {
    const json = vi.fn();
    mockFetch({ ok: true, status: 204, json });
    const data = await apiClient('/api/thing', { method: 'DELETE' });
    expect(data).toBeNull();
    expect(json).not.toHaveBeenCalled();
  });

  it('throws an Error with .status set and toasts on a non-ok response', async () => {
    mockFetch({
      ok: false,
      status: 403,
      json: async () => ({ message: 'Forbidden' }),
    });

    await expect(apiClient('/api/secret')).rejects.toMatchObject({
      message: 'Forbidden',
      status: 403,
    });
    expect(addToast).toHaveBeenCalledWith('Forbidden', 'error');
  });

  it('falls back to a generic message when error body has no message', async () => {
    mockFetch({ ok: false, status: 500, json: async () => null });

    await expect(apiClient('/api/boom')).rejects.toMatchObject({ status: 500 });
    expect(addToast).toHaveBeenCalledWith(
      'Erreur 500: Impossible de récupérer les données.',
      'error',
    );
  });

  it('does not toast on a non-ok response when skipToast is set', async () => {
    mockFetch({
      ok: false,
      status: 404,
      json: async () => ({ message: 'Not found' }),
    });

    await expect(
      apiClient('/api/missing', { skipToast: true }),
    ).rejects.toMatchObject({ status: 404 });
    expect(addToast).not.toHaveBeenCalled();
  });

  it('toasts and rethrows on a network TypeError', async () => {
    const netErr = new TypeError('Failed to fetch');
    global.fetch = vi.fn().mockRejectedValue(netErr) as unknown as typeof fetch;

    await expect(apiClient('/api/thing')).rejects.toBe(netErr);
    expect(addToast).toHaveBeenCalledWith(
      'Serveur injoignable. Vérifiez votre connexion.',
      'error',
    );
  });

  it('does not toast a network TypeError when skipToast is set', async () => {
    const netErr = new TypeError('Failed to fetch');
    global.fetch = vi.fn().mockRejectedValue(netErr) as unknown as typeof fetch;

    await expect(
      apiClient('/api/thing', { skipToast: true }),
    ).rejects.toBe(netErr);
    expect(addToast).not.toHaveBeenCalled();
  });

  it('sends the CSRF token from document.cookie as X-CSRFToken header', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      configurable: true,
      value: 'foo=bar; csrftoken=abc123; baz=qux',
    });
    const fetchFn = mockFetch({ ok: true, status: 200, json: async () => ({}) });

    await apiClient('/api/thing');

    const headers = (fetchFn.mock.calls[0][1] as RequestInit)
      .headers as Record<string, string>;
    expect(headers['X-CSRFToken']).toBe('abc123');
  });

  it('sets Content-Type application/json by default but not for FormData', async () => {
    const fetchFn = mockFetch({ ok: true, status: 200, json: async () => ({}) });

    await apiClient('/api/a');
    let headers = (fetchFn.mock.calls[0][1] as RequestInit).headers as Record<
      string,
      string
    >;
    expect(headers['Content-Type']).toBe('application/json');

    await apiClient('/api/b', { isFormData: true });
    headers = (fetchFn.mock.calls[1][1] as RequestInit).headers as Record<
      string,
      string
    >;
    expect(headers['Content-Type']).toBeUndefined();
  });

  it('attaches a Firebase bearer token when a user is signed in', async () => {
    (auth as { currentUser: unknown }).currentUser = {
      getIdToken: vi.fn().mockResolvedValue('fb-token'),
    };
    const fetchFn = mockFetch({ ok: true, status: 200, json: async () => ({}) });

    await apiClient('/api/thing');

    const headers = (fetchFn.mock.calls[0][1] as RequestInit)
      .headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer fb-token');
  });

  it('applies personalization visual_config from the response meta', async () => {
    const visualConfig = { theme: 'dark' };
    mockFetch({
      ok: true,
      status: 200,
      json: async () => ({ meta: { visual_config: visualConfig } }),
    });

    await apiClient('/api/thing');

    expect(usePersonalizationStore.getState().updateConfig).toHaveBeenCalledWith(
      visualConfig,
    );
  });

  it('does not call updateConfig when no visual_config is present', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ data: 1 }) });
    await apiClient('/api/thing');
    expect(useToastStore.getState().addToast).not.toHaveBeenCalled();
    expect(updateConfig).not.toHaveBeenCalled();
  });
});
