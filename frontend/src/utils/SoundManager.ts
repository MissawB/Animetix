/**
 * UI sound effects, synthesized in the browser.
 *
 * These used to be MP3s hotlinked from assets.mixkit.co. Mixkit now blocks
 * hotlinking, so every sound 404'd — in prod the console filled with
 * "GET https://assets.mixkit.co/... 403 (Forbidden)" and the app was silent.
 * Six short UI blips do not justify shipping (or hotlinking, or licensing)
 * audio files: the Web Audio API renders them from an oscillator, so there is
 * no network request, no CSP media-src to open, and no third party to depend on.
 */

type SoundType = 'click' | 'win' | 'loss' | 'unlock' | 'reveal' | 'error';

interface Tone {
  /** Frequency in Hz. A pair sweeps from the first value to the second. */
  freq: number | [number, number];
  /** Seconds from the start of the sound. */
  at: number;
  duration: number;
  type: OscillatorType;
  gain: number;
}

const VOICES: Record<SoundType, Tone[]> = {
  // A dry, short blip — it fires on every click, so it must never linger.
  click: [{ freq: 1180, at: 0, duration: 0.04, type: 'triangle', gain: 0.16 }],
  // A rising major arpeggio: the only sound allowed to feel like a reward.
  win: [
    { freq: 523.25, at: 0, duration: 0.12, type: 'sine', gain: 0.3 },
    { freq: 659.25, at: 0.1, duration: 0.12, type: 'sine', gain: 0.3 },
    { freq: 783.99, at: 0.2, duration: 0.12, type: 'sine', gain: 0.3 },
    { freq: 1046.5, at: 0.3, duration: 0.26, type: 'sine', gain: 0.34 },
  ],
  // Falling minor third: defeat, stated once, without drama.
  loss: [
    { freq: 329.63, at: 0, duration: 0.16, type: 'triangle', gain: 0.24 },
    { freq: 196, at: 0.14, duration: 0.3, type: 'triangle', gain: 0.24 },
  ],
  unlock: [
    { freq: 783.99, at: 0, duration: 0.1, type: 'sine', gain: 0.28 },
    { freq: 1318.51, at: 0.09, duration: 0.22, type: 'sine', gain: 0.3 },
  ],
  // A soft upward sweep as the card turns over.
  reveal: [{ freq: [420, 900], at: 0, duration: 0.24, type: 'sine', gain: 0.22 }],
  // Low and square: unmistakably a refusal, and distinct from `loss`.
  error: [{ freq: 150, at: 0, duration: 0.2, type: 'square', gain: 0.18 }],
};

type AudioCtor = typeof AudioContext;

const audioContextCtor = (): AudioCtor | undefined =>
  typeof window === 'undefined'
    ? undefined
    : (window.AudioContext ??
      (window as unknown as { webkitAudioContext?: AudioCtor }).webkitAudioContext);

class SoundManager {
  private muted: boolean;
  private ctx: AudioContext | null = null;

  constructor() {
    this.muted =
      typeof localStorage !== 'undefined' && localStorage.getItem('sound_muted') === 'true';
  }

  /** Created on the first play, never in the constructor: browsers refuse to
   *  start an AudioContext before a user gesture and log a warning if you try. */
  private context(): AudioContext | null {
    if (this.ctx) return this.ctx;
    const Ctor = audioContextCtor();
    if (!Ctor) return null;
    this.ctx = new Ctor();
    return this.ctx;
  }

  private ring(ctx: AudioContext, tone: Tone, startAt: number): void {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    const t0 = startAt + tone.at;
    const t1 = t0 + tone.duration;

    osc.type = tone.type;
    if (Array.isArray(tone.freq)) {
      osc.frequency.setValueAtTime(tone.freq[0], t0);
      osc.frequency.exponentialRampToValueAtTime(tone.freq[1], t1);
    } else {
      osc.frequency.setValueAtTime(tone.freq, t0);
    }

    // Ramp both ends: a raw start or stop on a gain node clicks audibly.
    gain.gain.setValueAtTime(0, t0);
    gain.gain.linearRampToValueAtTime(tone.gain, t0 + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, t1);

    osc.connect(gain).connect(ctx.destination);
    osc.start(t0);
    osc.stop(t1 + 0.02);
  }

  play(type: SoundType): void {
    if (this.muted || !VOICES[type]) return;

    // Audio is a garnish: a browser that refuses to play must never break a game.
    try {
      const ctx = this.context();
      if (ctx) {
        if (ctx.state === 'suspended') void ctx.resume();
        const now = ctx.currentTime;
        VOICES[type].forEach((tone) => this.ring(ctx, tone, now));
      }
    } catch {
      /* no audio device, autoplay blocked, context exhausted — stay silent */
    }

    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      if (type === 'win') navigator.vibrate([100, 30, 100, 30, 200]);
      else if (type === 'error' || type === 'loss') navigator.vibrate(200);
      else if (type === 'click') navigator.vibrate(10);
    }
  }

  toggle(): boolean {
    this.muted = !this.muted;
    localStorage.setItem('sound_muted', this.muted.toString());
    return this.muted;
  }
}

const soundManager = new SoundManager();
export default soundManager;
