/**
 * Animetix Core UI & Engine (SOTA 2026)
 * Handles Sound, Themes, PWA, and Real-time notifications.
 */

// --- 🔊 SOUND & HAPTIC MANAGER (Howler.js + Vibration API) ---
class SoundManager {
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
    play(type) {
        if (this.muted || !this.sounds[type]) return;
        this.sounds[type].play();
        
        // HAPTIC FEEDBACK (Mobile)
        if ("vibrate" in navigator) {
            if (type === 'win') navigator.vibrate([100, 30, 100, 30, 200]);
            else if (type === 'error' || type === 'loss') navigator.vibrate(200);
            else if (type === 'click') navigator.vibrate(10);
        }
    }
    toggle() {
        this.muted = !this.muted;
        localStorage.setItem('sound_muted', this.muted);
        return this.muted;
    }
}

window.soundManager = new SoundManager();
window.sounds = { play: (type) => window.soundManager.play(type) };

// --- 🚀 THEME MANAGER ---
function applyTheme(theme) {
    const html = document.documentElement;
    let actualTheme = theme;
    
    if (theme === 'auto') {
        actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    html.setAttribute('data-bs-theme', actualTheme);
    
    // Sync Tailwind 'class' strategy
    if (actualTheme === 'dark') {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }
    
    // Update UI buttons in settings
    ['light', 'dark', 'auto'].forEach(t => {
        const btn = document.getElementById(`theme-${t}`);
        if (btn) {
            if (t === theme) {
                btn.classList.add('border-yellow-400', 'bg-yellow-400/10');
            } else {
                btn.classList.remove('border-yellow-400', 'bg-yellow-400/10');
            }
        }
    });
}

function updateTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme);
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'auto';
    let nextTheme;
    if (currentTheme === 'auto') {
        nextTheme = 'light';
    } else if (currentTheme === 'light') {
        nextTheme = 'dark';
    } else {
        nextTheme = 'auto';
    }
    updateTheme(nextTheme);
}

// --- 🌐 PWA & OFFLINE ---
function initPWA(swPath) {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register(swPath)
                .then(reg => console.log('🚀 Animetix SW Active:', reg.scope))
                .catch(err => console.log('❌ SW Registration failed:', err));
        });
        
        navigator.serviceWorker.addEventListener('message', async event => {
            if (event.data && event.data.type === 'REQUEST_OFFLINE_DATA_SYNC') {
                syncOfflineData();
            }
        });
    }
}

async function syncOfflineData() {
    const scores = JSON.parse(localStorage.getItem('offlineScores') || '[]');
    if (scores.length > 0) {
        try {
            const response = await fetch('/sync_offline/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scores)
            });
            if (response.ok) {
                console.log('✅ Offline scores synchronized!');
                localStorage.removeItem('offlineScores');
            }
        } catch (err) {
            console.error('❌ Sync failed:', err);
        }
    }
}

// --- 🔔 NOTIFICATIONS & TOASTS ---
function initNotifications(isAuthenticated) {
    if (!isAuthenticated) return;

    const notificationSocket = new WebSocket(
        (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
        window.location.host + '/ws/notifications/'
    );

    notificationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        // Update counter if badge exists
        const badge = document.querySelector('.nav-link-manga .badge.bg-danger');
        if (badge) {
            const currentCount = parseInt(badge.innerText) || 0;
            badge.innerText = currentCount + 1;
            badge.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => badge.classList.remove('animate__animated', 'animate__pulse'), 1000);
        } else {
            // If badge doesn't exist, we might need to create it or just ignore for now
            // (Assumes the page is reloaded or the badge is present in base.html)
        }

        if (data.type === 'achievement_unlocked') {
            showAchievementToast(data.achievement);
        } else if (data.type === 'friend_achievement' || data.type === 'boss_alert') {
            showSocialToast(data);
        } else if (['info', 'duel', 'system', 'social'].includes(data.type)) {
            showGenericToast(data);
        }
    };
}

function showGenericToast(data) {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    
    const icons = { 'info': 'ℹ️', 'duel': '⚔️', 'system': '⚙️', 'social': '👤' };
    const colors = { 'info': '#3b82f6', 'duel': '#ef4444', 'system': '#64748b', 'social': '#a855f7' };
    
    const icon = icons[data.type] || '🔔';
    const color = colors[data.type] || '#fdb913';
    
    // Check for DPO data (if sent from backend)
    let feedbackHtml = '';
    if (data.dpo_context && data.dpo_output) {
        feedbackHtml = `
            <div class="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <span class="text-[8px] font-black opacity-40 italic uppercase">Qualité IA ?</span>
                <div class="flex gap-2">
                    <button onclick="submitRLHF('toast', '${data.dpo_context}', '${data.dpo_output}', true, this)" class="btn btn-xs btn-link text-success p-0"><i class="bi bi-hand-thumbs-up"></i></button>
                    <button onclick="submitRLHF('toast', '${data.dpo_context}', '${data.dpo_output}', false, this)" class="btn btn-xs btn-link text-danger p-0"><i class="bi bi-hand-thumbs-down"></i></button>
                </div>
            </div>
        `;
    }

    const toastHtml = `
        <div class="toast show animate__animated animate__fadeInRight shadow-2xl" role="alert" style="background: rgba(15,15,26,0.95); border: 2px solid ${color}; border-radius: 1rem; margin-bottom: 10px; min-width: 300px;">
            <div class="toast-header bg-transparent text-white border-b border-white/5 p-3">
                <span class="text-xl me-3">${icon}</span>
                <strong class="me-auto manga-font tracking-tighter" style="color: ${color}">${data.title || 'NOTIFICATION'}</strong>
                <small class="text-white opacity-50">${data.created_at || ''}</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body p-4 text-white">
                <p class="mb-2 text-sm opacity-90">${data.message}</p>
                ${data.link ? `<a href="${data.link}" class="btn btn-sm w-100 mt-2 fw-black italic text-[10px]" style="background: ${color}; color: white;">VOIR PLUS</a>` : ''}
                ${feedbackHtml}
            </div>
        </div>
    `;
    const div = document.createElement('div');
    div.innerHTML = toastHtml;
    container.appendChild(div.firstChild);
    window.sounds.play('reveal');
    
    // Auto-remove unless it's a critical system message or has DPO
    if (!data.dpo_context) {
        setTimeout(() => {
            const toast = Array.from(container.querySelectorAll('.toast')).find(t => t.innerText.includes(data.message));
            if (toast) toast.remove();
        }, 8000);
    }
}

// Global HLHF submitter
window.submitRLHF = function(type, context, output, isPositive, element) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const body = new FormData();
    body.append('type', type);
    body.append('context', context);
    body.append('output', output);
    body.append('is_positive', isPositive);
    if (csrftoken) body.append('csrfmiddlewaretoken', csrftoken);

    fetch('/feedback/ai/', {
        method: 'POST',
        body: body,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }).then(res => {
        if (res.ok) {
            if (element) {
                const parent = element.parentElement;
                parent.innerHTML = '<span class="text-[10px] text-success manga-font animate__animated animate__pulse">MERCI !</span>';
            }
        }
    });
};

function showSocialToast(data) {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    const icon = data.type === 'boss_alert' ? '🔥' : '🤝';
    const title = data.type === 'boss_alert' ? 'WORLD BOSS' : 'ACTIVITÉ AMIS';
    
    const toastHtml = `
        <div class="toast show animate__animated animate__fadeInRight shadow-2xl" role="alert" style="background: rgba(15,15,26,0.95); border: 2px solid #3b82f6; border-radius: 1rem; margin-bottom: 10px; min-width: 300px;">
            <div class="toast-header bg-transparent text-white border-b border-white/5 p-3">
                <span class="text-xl me-3">${icon}</span>
                <strong class="me-auto manga-font tracking-tighter text-blue-400">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body p-4 text-white">
                <p class="mb-0 text-sm opacity-90">${data.message}</p>
            </div>
        </div>
    `;
    const div = document.createElement('div');
    div.innerHTML = toastHtml;
    container.appendChild(div.firstChild);
    window.sounds.play('reveal');
    
    setTimeout(() => {
        const toast = container.querySelector('.toast');
        if (toast) toast.remove();
    }, 6000);
}

function showAchievementToast(ach) {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    const toastHtml = `
        <div class="toast show animate__animated animate__bounceInRight shadow-2xl" role="alert" aria-live="assertive" aria-atomic="true" style="background: rgba(0,0,0,0.9); border: 2px solid #FFD700; border-radius: 1rem; margin-bottom: 10px;">
            <div class="toast-header bg-transparent text-white border-b border-white/10 p-3">
                <span class="text-2xl me-3">${ach.icon}</span>
                <strong class="me-auto manga-font tracking-tighter">SUCCÈS DÉBLOQUÉ !</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body p-4 text-white">
                <h6 class="manga-font text-lg mb-1">${ach.name}</h6>
                <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 bg-yellow-400 text-black text-[10px] font-black rounded-full">+${ach.xp} XP</span>
                </div>
            </div>
        </div>
    `;
    const div = document.createElement('div');
    div.innerHTML = toastHtml;
    container.appendChild(div.firstChild);
    window.sounds.play('win');
    
    setTimeout(() => {
        const toast = container.querySelector('.toast');
        if (toast) toast.remove();
    }, 5000);
}

// --- 🛠️ UTILS ---
function toggleSidebar() {
    window.sounds.play('click');
    document.body.classList.toggle('sidebar-open');
}

function toggleSettings(forceClose = false) {
    if (!forceClose) window.sounds.play('click');
    const drawer = document.getElementById('settings-drawer');
    const overlay = document.getElementById('sidebar-overlay');
    if (!drawer || !overlay) return;
    if (forceClose) {
        drawer.classList.add('translate-x-full');
        overlay.classList.add('hidden');
        return;
    }
    drawer.classList.toggle('translate-x-full');
    overlay.classList.toggle('hidden');
}

async function setDiff(val) {
    await fetch(`/switch_diff/${val}/`);
    window.location.reload();
}

// Event Listeners for System Theme
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (localStorage.getItem('theme') === 'auto') {
        applyTheme('auto');
    }
});

// HTMX Events
document.body.addEventListener('htmx:beforeOnLoad', () => {
    window.sounds.play('click');
});

document.body.addEventListener('htmx:afterSwap', () => {
    const toasts = document.querySelectorAll('.toast.show');
    if (toasts.length > 0) window.sounds.play('unlock');
});
