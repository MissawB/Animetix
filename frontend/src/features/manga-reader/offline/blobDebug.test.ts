import 'fake-indexeddb/auto';
import { describe, it } from 'vitest';
import { createStore, set as idbSet, get as idbGet } from 'idb-keyval';

const store = createStore('debug-db', 'kv');

// Helper to store as { buffer, type } and restore as Blob
interface StoredBlob { buffer: ArrayBuffer; type: string }

describe('blob debug', () => {
  it('ArrayBuffer round-trips correctly in jsdom', async () => {
    const blob = new Blob(['hello'], { type: 'image/jpeg' });
    const buffer = await blob.arrayBuffer();
    const stored: StoredBlob = { buffer, type: blob.type };

    await idbSet('k2', stored, store);
    const retrieved = await idbGet<StoredBlob>('k2', store);

    console.log('RETRIEVED stored blob obj:', retrieved);
    const restoredBlob = new Blob([retrieved!.buffer], { type: retrieved!.type });
    console.log('RESTORED instanceof Blob:', restoredBlob instanceof Blob);
    console.log('RESTORED text:', await restoredBlob.text());
    console.log('RESTORED type:', restoredBlob.type);
  });
});
