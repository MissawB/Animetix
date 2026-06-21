import { describe, it, expect, vi, beforeEach } from 'vitest';

// SoundManager wraps `howler`'s Howl. Mock it so no real audio loads and we can
// assert play() is invoked. `play` resolves to mimic the real (async) call.
const playSpy = vi.fn().mockResolvedValue(undefined);
// `Howl` is invoked with `new`, so the mock must be a real (non-arrow)
// constructable function returning the instance shape we assert on.
const HowlMock = vi.fn(function HowlCtor(this: { play: typeof playSpy }) {
  this.play = playSpy;
});

vi.mock('howler', () => ({
  Howl: HowlMock,
}));

const importSoundManager = async () => {
  vi.resetModules();
  const mod = await import('../SoundManager');
  return mod.default;
};

describe('SoundManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('constructs one Howl instance per sound type', async () => {
    await importSoundManager();
    // click, win, loss, unlock, reveal, error
    expect(HowlMock).toHaveBeenCalledTimes(6);
  });

  it('plays the requested sound when not muted', async () => {
    const sm = await importSoundManager();
    sm.play('click');
    expect(playSpy).toHaveBeenCalledTimes(1);
  });

  it('does not play when muted (persisted in localStorage)', async () => {
    localStorage.setItem('sound_muted', 'true');
    const sm = await importSoundManager();
    sm.play('win');
    expect(playSpy).not.toHaveBeenCalled();
  });

  it('tolerates play() rejections without throwing', async () => {
    playSpy.mockRejectedValueOnce(new Error('autoplay blocked'));
    const sm = await importSoundManager();
    expect(() => sm.play('error')).not.toThrow();
  });

  it('toggle() flips mute state and persists it', async () => {
    const sm = await importSoundManager();

    const muted = sm.toggle();
    expect(muted).toBe(true);
    expect(localStorage.getItem('sound_muted')).toBe('true');

    // While muted, play is suppressed.
    sm.play('click');
    expect(playSpy).not.toHaveBeenCalled();

    const unmuted = sm.toggle();
    expect(unmuted).toBe(false);
    expect(localStorage.getItem('sound_muted')).toBe('false');

    sm.play('click');
    expect(playSpy).toHaveBeenCalledTimes(1);
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

    vi.unstubAllGlobals();
  });
});
