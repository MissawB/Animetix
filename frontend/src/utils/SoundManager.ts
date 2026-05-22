import { Howl } from 'howler';

type SoundType = 'click' | 'win' | 'loss' | 'unlock' | 'reveal' | 'error';

class SoundManager {
    private muted: boolean;
    private sounds: Record<SoundType, Howl>;

    constructor() {
        this.muted = localStorage.getItem('sound_muted') === 'true';
        this.sounds = {
            'click': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3'], volume: 0.2 }),
            'win': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3'], volume: 0.4 }),
            'loss': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/2513/2513-preview.mp3'], volume: 0.3 }),
            'unlock': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/2019/2019-preview.mp3'], volume: 0.5 }),
            'reveal': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/2568/2571-preview.mp3'], volume: 0.3 }),
            'error': new Howl({ src: ['https://assets.mixkit.co/active_storage/sfx/2513/2513-preview.mp3'], volume: 0.4 }),
        };
    }

    play(type: SoundType): void {
        if (this.muted || !this.sounds[type]) return;
        this.sounds[type].play();
        
        if ("vibrate" in navigator) {
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
