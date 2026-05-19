/**
 * search_bar.js
 * Handles autocomplete and search bar interactions.
 */

(function() {
    /**
     * Initialize autocomplete for a specific search input.
     * @param {HTMLElement} input - The search input element.
     */
    function initAutocomplete(input) {
        if (input.dataset.autocompleteInitialized) return;
        
        const inputId = input.getAttribute('data-input-id');
        const mediaType = input.getAttribute('data-media-type') || '';
        const searchUrl = input.getAttribute('data-search-url') || '/api/search/';
        const results = document.getElementById('autocomplete-results-' + inputId);
        
        if (!results) return;

        let debounceTimer;

        input.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const val = this.value.trim();
            
            if (val.length < 2) {
                results.innerHTML = '';
                results.style.display = 'none';
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`${searchUrl}?q=${encodeURIComponent(val)}&media_type=${mediaType}&limit=10`)
                    .then(response => response.json())
                    .then(data => {
                        results.innerHTML = '';
                        
                        if (data.length > 0) {
                            data.forEach(item => {
                                const div = document.createElement('div');
                                div.className = 'list-group-item list-group-item-action d-flex align-items-center border-0 py-3 px-4 hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors bg-transparent';
                                div.style.cursor = 'pointer';
                                
                                const imgUrl = item.image || 'https://via.placeholder.com/45x60?text=?';
                                div.innerHTML = `
                                    <img src="${imgUrl}" style="width: 45px; height: 60px; object-fit: cover; border-radius: 8px;" class="me-3 shadow-sm" onerror="this.src='https://via.placeholder.com/45x60?text=?'">
                                    <div class="overflow-hidden">
                                        <div class="fw-bold text-truncate text-navy-900 dark:text-white">${item.title}</div>
                                        <div class="text-muted small text-truncate">${item.title_english || ''}</div>
                                    </div>
                                `;
                                
                                div.onclick = function() {
                                    input.value = item.title;
                                    results.style.display = 'none';
                                };
                                results.appendChild(div);
                            });
                            results.style.display = 'block';
                        } else {
                            results.style.display = 'none';
                        }
                    })
                    .catch(err => {
                        console.error('Autocomplete Error:', err);
                        results.style.display = 'none';
                    });
            }, 300); // 300ms debounce
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== input && !results.contains(e.target)) {
                results.style.display = 'none';
            }
        });

        input.dataset.autocompleteInitialized = 'true';
    }

    /**
     * Scan and initialize all search bars.
     */
    function scanAndInit() {
        document.querySelectorAll('.search-autocomplete').forEach(initAutocomplete);
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scanAndInit);
    } else {
        scanAndInit();
    }
    
    // Support HTMX content loads
    document.addEventListener('htmx:afterSwap', (event) => {
        const target = event.detail.target;
        if (target && typeof target.querySelectorAll === 'function') {
            target.querySelectorAll('.search-autocomplete').forEach(initAutocomplete);
        }
    });
})();
