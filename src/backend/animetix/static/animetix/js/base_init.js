/**
 * base_init.js
 * Core initialization for Animetix base template.
 */

// Tailwind Configuration
if (window.tailwind) {
    tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                colors: {
                    yellow: {
                        400: '#fdb913',
                        600: '#d97706',
                    },
                    navy: {
                        700: '#1e1e2f',
                        800: '#1a1a2e',
                        900: '#0f0f1a',
                    }
                }
            }
        }
    }
}

/**
 * Initialize core engines and PWA features.
 */
function initBaseEngine() {
    const body = document.body;
    if (!body) return;

    const swPath = body.getAttribute('data-sw-path');
    const isAuthenticated = body.getAttribute('data-is-authenticated') === 'true';
    
    // Initialize Theme
    const savedTheme = localStorage.getItem('theme') || 'auto';
    if (typeof applyTheme === 'function') {
        applyTheme(savedTheme);
    }

    // Initialize PWA
    if (typeof initPWA === 'function' && swPath) {
        initPWA(swPath);
    }

    // Initialize Notifications
    if (typeof initNotifications === 'function') {
        initNotifications(isAuthenticated);
    }

    // Offline Engine Integration (if available)
    if (window.offlineEngine && typeof window.offlineEngine.init === 'function') {
        window.offlineEngine.init();
    }
}

// Execute initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBaseEngine);
} else {
    initBaseEngine();
}
