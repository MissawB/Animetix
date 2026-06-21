import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'idb-keyval';
import type { PersistedClient } from '@tanstack/react-query-persist-client';
import { createPersister } from '../persister';

function makeClient(overrides: Partial<PersistedClient> = {}): PersistedClient {
  return {
    timestamp: 1_700_000_000_000,
    buster: 'v1',
    clientState: {
      mutations: [],
      queries: [
        {
          queryKey: ['manga', 'list'],
          queryHash: '["manga","list"]',
          state: {
            data: [{ id: 1, title: 'One Piece' }],
            dataUpdateCount: 1,
            dataUpdatedAt: 1_700_000_000_000,
            error: null,
            errorUpdateCount: 0,
            errorUpdatedAt: 0,
            fetchFailureCount: 0,
            fetchFailureReason: null,
            fetchMeta: null,
            isInvalidated: false,
            status: 'success',
            fetchStatus: 'idle',
          },
        },
      ],
    },
    ...overrides,
  } as PersistedClient;
}

const DEFAULT_KEY = 'ANIMETIX_QUERY_OFFLINE_CACHE';

describe('createPersister', () => {
  beforeEach(async () => {
    // Wipe the idb-keyval default store between tests.
    const { clear } = await import('idb-keyval');
    await clear();
  });

  it('persists the client under the default key and stores the real payload', async () => {
    const persister = createPersister();
    const client = makeClient();

    await persister.persistClient(client);

    // Read straight from idb-keyval's default store to prove the real write.
    const raw = await get<PersistedClient>(DEFAULT_KEY);
    expect(raw).toEqual(client);
    expect(raw?.clientState.queries[0].state.data).toEqual([
      { id: 1, title: 'One Piece' },
    ]);
  });

  it('round-trips persist -> restore returning a deep-equal client', async () => {
    const persister = createPersister();
    const client = makeClient();

    await persister.persistClient(client);
    const restored = await persister.restoreClient();

    expect(restored).toEqual(client);
    expect(restored).not.toBe(client); // structured-clone copy, not same reference
  });

  it('restoreClient returns undefined when nothing has been persisted', async () => {
    const persister = createPersister();
    expect(await persister.restoreClient()).toBeUndefined();
  });

  it('removeClient deletes the persisted client', async () => {
    const persister = createPersister();
    const client = makeClient();

    await persister.persistClient(client);
    expect(await persister.restoreClient()).toBeTruthy();

    await persister.removeClient();

    expect(await persister.restoreClient()).toBeUndefined();
    expect(await get(DEFAULT_KEY)).toBeUndefined();
  });

  it('uses a custom key when provided and isolates it from the default key', async () => {
    const customKey = 'CUSTOM_CACHE_KEY';
    const persister = createPersister(customKey);
    const client = makeClient({ buster: 'custom' });

    await persister.persistClient(client);

    // Stored under the custom key...
    expect(await get<PersistedClient>(customKey)).toEqual(client);
    // ...and NOT under the default key.
    expect(await get(DEFAULT_KEY)).toBeUndefined();

    const restored = await persister.restoreClient();
    expect(restored?.buster).toBe('custom');
  });

  it('overwrites the previously persisted client on re-persist', async () => {
    const persister = createPersister();

    await persister.persistClient(makeClient({ timestamp: 1 }));
    await persister.persistClient(makeClient({ timestamp: 2 }));

    const restored = await persister.restoreClient();
    expect(restored?.timestamp).toBe(2);
  });

  it('two persisters with different keys do not collide', async () => {
    const a = createPersister('KEY_A');
    const b = createPersister('KEY_B');

    await a.persistClient(makeClient({ buster: 'A' }));
    await b.persistClient(makeClient({ buster: 'B' }));

    expect((await a.restoreClient())?.buster).toBe('A');
    expect((await b.restoreClient())?.buster).toBe('B');

    await a.removeClient();
    expect(await a.restoreClient()).toBeUndefined();
    // Removing A must not affect B.
    expect((await b.restoreClient())?.buster).toBe('B');
  });
});
