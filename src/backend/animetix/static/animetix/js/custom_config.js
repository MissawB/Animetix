/**
 * custom_config.js
 * Logic for the custom configuration page (filtering by titles, genres, tags).
 */

document.addEventListener('DOMContentLoaded', () => {
    /**
     * Logic for manual addition of titles (Whitelist/Blacklist).
     */
    const setupManual = (inputId, listId, color, name) => {
        const input = document.getElementById(inputId);
        const list = document.getElementById(listId);
        const btn = document.getElementById('btn-add-' + color);
        
        if (!input || !list || !btn) return;

        btn.onclick = () => {
            const val = input.value.trim();
            if (!val) return;
            
            // Avoid duplicates
            if (list.querySelector(`input[value="${val}"]`)) {
                input.value = '';
                return;
            }

            const span = document.createElement('span');
            span.className = `badge bg-${color} bg-opacity-10 text-${color} p-2 rounded-xl d-flex align-items-center gap-2`;
            span.innerHTML = `${val}<input type="hidden" name="${name}" value="${val}"><i class="bi bi-x-circle-fill cursor-pointer" onclick="this.parentElement.remove()"></i>`;
            list.appendChild(span);
            input.value = '';
        };

        // Support Enter key
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                btn.click();
            }
        });
    };

    /**
     * Logic for Select-based filtering (Genres/Tags).
     */
    const setupSelect = (selectId, listId, badgeColor, name) => {
        const select = document.getElementById(selectId);
        const list = document.getElementById(listId);
        
        if (!select || !list) return;

        select.onchange = () => {
            const val = select.value;
            if (!val) return;
            
            // Avoid duplicates
            if (list.querySelector(`input[value="${val}"]`)) {
                select.value = '';
                return;
            }
            
            const span = document.createElement('span');
            span.className = `badge bg-${badgeColor} text-white p-2 rounded-xl d-flex align-items-center gap-2`;
            span.innerHTML = `${val}<input type="hidden" name="${name}" value="${val}"><i class="bi bi-x-circle-fill cursor-pointer" onclick="this.parentElement.remove()"></i>`;
            list.appendChild(span);
            select.value = '';
        };
    };

    // Initialize Manual Inputs
    setupManual('white-input', 'white-list', 'success', 'whitelist');
    setupManual('black-input', 'black-list', 'danger', 'blacklist');
    
    // Initialize Selects
    setupSelect('genre-white-select', 'genres-white-list', 'success', 'genres_white');
    setupSelect('genre-black-select', 'genres-black-list', 'danger', 'genres_black');
    setupSelect('tag-white-select', 'tags-white-list', 'primary', 'tags_white');
    setupSelect('tag-black-select', 'tags-black-list', 'dark', 'tags_black');
});
