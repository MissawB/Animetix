import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

/**
 * SoundManager synthesizes its blips with the Web Audio API (it used to hotlink
 * MP3s from mixkit.co, which now answers 403). jsdom has no AudioContext, so we
 * stub one and assert on the oscillators it wires up.
 */

const started: { type: string; freq: number }[] = [];

const makeOscillator = () => {
  const osc = {
    type: 'sine',
    frequency: {
      value: 0,
      setValueAtTime: vi.fn(function (this: unknown, v: number) {
        osc.frequency.value = v;
      }),
      exponentialRampToValueAtTime: vi.fn(),
    },
    connect: vi.fn(() => ({ connect: vi.fn() })),
    start: vi.fn(() => started.push({ type: osc.type, freq: osc.frequency.value })),
    stop: vi.fn(),
  };
  return osc;
};

const makeGain = () => ({
  gain: {
    setValueAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
    exponentialRampToValueAtTime: vi.fn(),
  },
  connect: vi.fn(() => ({ connect: vi.fn() })),
});

const resume = vi.fn();
const ctxState = { value: 'running' as AudioContextState };

const AudioContextMock = vi.fn(function AudioContextCtor(this: Record<string, unknown>) {
  this.currentTime = 0;
  Object.defineProperty(this, 'state', { get: () => ctxState.value });
  this.destination = {};
  this.resume = resume;
  this.createOscillator = makeOscillator;
  this.createGain = makeGain;
});

const importSoundManager = async () => {
  vi.resetModules();
  const mod = await import('../SoundManager');
  return mod.default;
};

describe('SoundManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    started.length = 0;
    ctxState.value = 'running';
    localStorage.clear();
    vi.stubGlobal('AudioContext', AudioContextMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('does not open an AudioContext before the first play', async () => {
    await importSoundManager();
    // Browsers refuse (and warn) when a context is created without a user gesture.
    expect(AudioContextMock).not.toHaveBeenCalled();
  });

  it('synthesizes the requested sound when not muted', async () => {
    const sm = await importSoundManager();
    sm.play('click');

    expect(AudioContextMock).toHaveBeenCalledTimes(1);
    expect(started).toHaveLength(1);
    expect(started[0].freq).toBeGreaterThan(0);
  });

  it('plays the win fanfare as a rising sequence', async () => {
    const sm = await importSoundManager();
    sm.play('win');

    const freqs = started.map((s) => s.freq);
    expect(freqs.length).toBeGreaterThan(1);
    // Each note is higher than the one before it — that is what makes it a reward.
    expect([...freqs].sort((a, b) => a - b)).toEqual(freqs);
  });

  it('reuses a single AudioContext across plays', async () => {
    const sm = await importSoundManager();
    sm.play('click');
    sm.play('reveal');
    expect(AudioContextMock).toHaveBeenCalledTimes(1);
  });

  it('resumes a suspended context (autoplay policy)', async () => {
    ctxState.value = 'suspended';
    const sm = await importSoundManager();
    sm.play('click');
    expect(resume).toHaveBeenCalled();
  });

  it('does not play when muted (persisted in localStorage)', async () => {
    localStorage.setItem('sound_muted', 'true');
    const sm = await importSoundManager();
    sm.play('win');
    expect(AudioContextMock).not.toHaveBeenCalled();
    expect(started).toHaveLength(0);
  });

  it('stays silent instead of throwing when audio is unavailable', async () => {
    // No AudioContext at all (old browser, hardened environment): a missing blip
    // must never take a game down.
    vi.stubGlobal('AudioContext', undefined);
    const sm = await importSoundManager();
    expect(() => sm.play('error')).not.toThrow();
  });

  it('stays silent instead of throwing when the context refuses to start', async () => {
    vi.stubGlobal(
      'AudioContext',
      vi.fn(() => {
        throw new Error('audio hardware unavailable');
      }),
    );
    const sm = await importSoundManager();
    expect(() => sm.play('click')).not.toThrow();
  });

  it('toggle() flips mute state and persists it', async () => {
    const sm = await importSoundManager();

    const muted = sm.toggle();
    expect(muted).toBe(true);
    expect(localStorage.getItem('sound_muted')).toBe('true');

    sm.play('click');
    expect(started).toHaveLength(0);

    const unmuted = sm.toggle();
    expect(unmuted).toBe(false);
    expect(localStorage.getItem('sound_muted')).toBe('false');

    sm.play('click');
    expect(started).toHaveLength(1);
  });

  it('triggers vibration patterns for relevant sound types', async () => {
    const vibrate = vi.fn();
    vi.stubGlobal('navigator', { vibrate });
    const sm = await importSoundManager();

    sm.play('win');
    expect(vibrate).toHaveBeenCalledWith([100, 30, 100, 30, 200]);

    sm.play('error');
    expect(vibrate).toHaveBeenCalledWith(200);

    sm.play('click');
    expect(vibrate).toHaveBeenCalledWith(10);
  });
});
