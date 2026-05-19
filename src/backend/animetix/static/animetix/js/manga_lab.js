/**
 * Manga Lab - AI Bubble Cleaner Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('manga-lab-data');
    if (!dataElement) return;

    const config = JSON.parse(dataElement.textContent);
    const processUrl = config.processUrl;
    const translateUrl = config.translateUrl;
    const csrfToken = config.csrfToken;

    let currentMangaData = { url: null, file: null, title: "" };

    function uploadManga(input) {
        if (input.files && input.files[0]) {
            processManga(null, input.files[0].name, input.files[0]);
        }
    }

    function processManga(url, title, file = null) {
        currentMangaData = { url, file, title };
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            const span = overlay.querySelector('span');
            if (span) span.innerText = "DÉTECTION & NETTOYAGE IA...";
            overlay.classList.remove('d-none');
        }
        
        const placeholderView = document.getElementById('placeholder-view');
        if (placeholderView) placeholderView.classList.add('d-none');
        
        const formData = new FormData();
        if (file) formData.append('image_file', file);
        else formData.append('image_url', url);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(processUrl, {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (overlay) overlay.classList.add('d-none');
            if (data.status === 'success') {
                const resultView = document.getElementById('result-view');
                if (resultView) resultView.classList.remove('d-none');
                
                const originalImg = document.getElementById('original-img');
                const cleanedImg = document.getElementById('cleaned-img');
                const translatedImg = document.getElementById('translated-img');
                const titleEl = document.getElementById('manga-title');
                const countEl = document.getElementById('bubble-count');

                if (originalImg) originalImg.src = data.original_image;
                if (cleanedImg) cleanedImg.src = data.cleaned_image;
                if (translatedImg) translatedImg.src = "";
                
                toggleResultView('clean');
                
                if (titleEl) titleEl.innerText = title;
                if (countEl) countEl.innerText = `${data.bubbles_found} BULLES / TEXTES NETTOYÉS`;
                
                if (window.sounds) window.sounds.play('unlock');
            } else {
                alert("Erreur: " + data.error);
                resetManga();
            }
        })
        .catch(err => {
            if (overlay) overlay.classList.add('d-none');
            console.error(err);
            alert("Une erreur est survenue lors du traitement.");
            resetManga();
        });
    }

    function translateCurrentManga() {
        if (!currentMangaData.url && !currentMangaData.file) return;
        
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            const span = overlay.querySelector('span');
            if (span) span.innerText = "OCR & TRADUCTION IA...";
            overlay.classList.remove('d-none');
        }
        
        const formData = new FormData();
        if (currentMangaData.file) formData.append('image_file', currentMangaData.file);
        else formData.append('image_url', currentMangaData.url);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(translateUrl, {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (overlay) overlay.classList.add('d-none');
            if (data.status === 'success') {
                const translatedImg = document.getElementById('translated-img');
                if (translatedImg) translatedImg.src = data.translated_image;
                toggleResultView('translated');
                if (window.sounds) window.sounds.play('reveal');
            } else {
                alert("Erreur Traduction: " + data.error);
            }
        })
        .catch(err => {
            if (overlay) overlay.classList.add('d-none');
            console.error(err);
            alert("Erreur réseau lors de la traduction.");
        });
    }

    function toggleResultView(mode) {
        const btnClean = document.getElementById('btn-show-clean');
        const btnTrans = document.getElementById('btn-show-translated');
        const imgClean = document.getElementById('cleaned-img');
        const imgTrans = document.getElementById('translated-img');

        if (mode === 'clean') {
            if (btnClean) btnClean.classList.add('active');
            if (btnTrans) btnTrans.classList.remove('active');
            if (imgClean) imgClean.classList.remove('d-none');
            if (imgTrans) imgTrans.classList.add('d-none');
        } else {
            if (!imgTrans || !imgTrans.src || imgTrans.src === window.location.href) {
                translateCurrentManga();
                return;
            }
            if (btnTrans) btnTrans.classList.add('active');
            if (btnClean) btnClean.classList.remove('active');
            if (imgTrans) imgTrans.classList.remove('d-none');
            if (imgClean) imgClean.classList.add('d-none');
        }
    }

    function resetManga() {
        const resultView = document.getElementById('result-view');
        const placeholderView = document.getElementById('placeholder-view');
        if (resultView) resultView.classList.add('d-none');
        if (placeholderView) placeholderView.classList.remove('d-none');
        currentMangaData = { url: null, file: null, title: "" };
    }

    // Expose functions to window for onclick handlers
    window.uploadManga = uploadManga;
    window.processManga = processManga;
    window.translateCurrentManga = translateCurrentManga;
    window.toggleResultView = toggleResultView;
    window.resetManga = resetManga;
});
