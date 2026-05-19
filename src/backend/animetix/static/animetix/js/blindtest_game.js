/**
 * Blind Test Game Logic
 * Manages the vinyl player, visualizer, and video/audio playback.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Logic to pick the active video element
    const videoHint = document.getElementById('blindVideo');
    const videoFallback = document.getElementById('blindVideoFallback');
    const video = videoHint || videoFallback;
    
    const playBtn = document.getElementById('playBtn');
    const playIcon = document.getElementById('playIcon');
    const vinyl = document.getElementById('vinylDisk');
    const bars = document.querySelectorAll('.visualizer-bar');
    
    let visualizerInterval;

    function startVisualizer() {
        if (!bars.length) return;
        visualizerInterval = setInterval(() => {
            bars.forEach(bar => {
                const height = Math.random() * 40 + 10;
                bar.style.height = `${height}px`;
                bar.style.opacity = Math.random() * 0.5 + 0.5;
            });
        }, 100);
    }

    function stopVisualizer() {
        if (visualizerInterval) {
            clearInterval(visualizerInterval);
        }
        bars.forEach(bar => {
            bar.style.height = `20px`;
            bar.style.opacity = 0.3;
        });
    }

    const volumeSlider = document.getElementById('volumeSlider');
    if (volumeSlider && video) {
        video.volume = volumeSlider.value;
        volumeSlider.addEventListener('input', (e) => {
            video.volume = e.target.value;
        });
    }

    if (playBtn && video) {
        playBtn.addEventListener('click', () => {
            if (video.paused) {
                video.play();
                playIcon.className = 'bi bi-pause-fill text-4xl';
                if (vinyl) vinyl.classList.add('vinyl-playing');
                startVisualizer();
            } else {
                video.pause();
                playIcon.className = 'bi bi-play-fill text-4xl';
                if (vinyl) vinyl.classList.remove('vinyl-playing');
                stopVisualizer();
            }
        });
        
        // Reset when video ends
        video.addEventListener('ended', () => {
            playIcon.className = 'bi bi-play-fill text-4xl';
            if (vinyl) vinyl.classList.remove('vinyl-playing');
            stopVisualizer();
        });
    }
});
