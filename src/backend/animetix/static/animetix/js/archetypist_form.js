let mainItems = [];
let crossData = {};
let currentAlphaPool = [];
let currentBetaPool = [];
let defaultImgUrl = '';

function searchItems(input, resultsId, side) {
    const query = input.value.toLowerCase().trim();
    const resultsBox = document.getElementById(resultsId);
    if (query.length < 2) { resultsBox.classList.add('hidden'); return; }
    const pool = (side === 'A') ? currentAlphaPool : currentBetaPool;
    const filtered = pool.filter(it => {
        const t = (it.title || "").toLowerCase();
        const tn = (it.title_native || "").toLowerCase();
        return t.includes(query) || tn.includes(query);
    }).slice(0, 8);

    if (filtered.length > 0) {
        resultsBox.innerHTML = '';
        filtered.forEach(it => {
            const title = it.title;
            const native = it.title_native || "";
            const img = it.image || "";
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerHTML = `<img src="${img}" onerror="this.src='${defaultImgUrl}'"><div class="flex-1 overflow-hidden"><div class="font-bold text-[11px] truncate text-white uppercase">${title}</div>${native ? `<div class="text-[9px] text-warning opacity-40 truncate">${native}</div>` : ''}</div>`;
            div.onmousedown = (e) => { e.preventDefault(); selectItem(title, native, img, input, resultsBox, side); };
            resultsBox.appendChild(div);
        });
        resultsBox.classList.remove('hidden');
    } else { resultsBox.classList.add('hidden'); }
}

function selectItem(title, native, img, input, resultsBox, side) {
    input.value = title;
    input.classList.add('hidden');
    resultsBox.classList.add('hidden');
    
    const info = document.getElementById('selected-info-' + side);
    const preview = document.getElementById('preview-' + side + '-mini');
    document.getElementById('display-title-' + side).innerText = title;
    document.getElementById('media-label-' + side).innerText = document.getElementById(side === 'A' ? 'media-type-alpha' : 'media-type-beta').value;
    preview.innerHTML = `<img src="${img}" class="w-full h-full object-cover" onerror="this.src='${defaultImgUrl}'">`;
    info.classList.remove('hidden');
}

function resetSide(side) {
    const input = document.getElementById('input-' + side);
    const info = document.getElementById('selected-info-' + side);
    input.value = '';
    input.classList.remove('hidden');
    info.classList.add('hidden');
}

function selectStyle(btn, styleName) {
    document.getElementById('art-style-input').value = styleName;
    document.querySelectorAll('.style-btn').forEach(b => {
        b.classList.remove('border-warning', 'text-warning', 'opacity-100');
        b.classList.add('border-white/10', 'opacity-40');
    });
    btn.classList.remove('border-white/10', 'opacity-40');
    btn.classList.add('border-warning', 'text-warning', 'opacity-100');
}

document.addEventListener('DOMContentLoaded', () => {
    const itemsDataElement = document.getElementById('items-data-hidden');
    const crossDataElement = document.getElementById('cross-data-hidden');
    const configElement = document.getElementById('archetypist-config');
    
    if (itemsDataElement) mainItems = JSON.parse(itemsDataElement.textContent || '[]');
    if (crossDataElement) crossData = JSON.parse(crossDataElement.textContent || '{}');
    if (configElement) {
        const config = JSON.parse(configElement.textContent);
        defaultImgUrl = config.defaultImgUrl;
    }
    
    currentAlphaPool = mainItems; 
    currentBetaPool = mainItems;
    
    document.addEventListener('click', e => { 
        if (!e.target.closest('.position-relative')) {
            document.querySelectorAll('.search-results-box').forEach(b => b.classList.add('hidden')); 
        }
    });
});
