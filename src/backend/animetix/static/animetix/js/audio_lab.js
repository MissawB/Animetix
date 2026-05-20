let currentVoiceId = 'naruto';
let currentSource = 'library';
let uploadedFile = null;
let mediaRecorder = null;
let audioChunks = [];

function selectVoice(id) {
    currentSource = 'library';
    currentVoiceId = id;
    document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
    document.querySelector(`[data-voice-id="${id}"]`).classList.add('selected');
}

function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        currentSource = 'upload';
        uploadedFile = input.files[0];
        const info = document.getElementById('file-info');
        info.innerText = `Fichier prêt: ${uploadedFile.name}`;
        info.classList.remove('d-none');
    }
}

async function toggleRecording() {
    const btn = document.getElementById('record-btn');
    const status = document.getElementById('record-status');
    
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        btn.classList.remove('animate-pulse');
        status.innerText = "Traitement de l'enregistrement...";
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
        mediaRecorder.onstop = () => {
            currentSource = 'mic';
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            uploadedFile = new File([audioBlob], "record.wav", { type: "audio/wav" });
            status.innerText = "Enregistrement prêt !";
        };

        mediaRecorder.start();
        btn.classList.add('animate-pulse');
        status.innerText = "Enregistrement en cours...";
    } catch (err) {
        alert("Erreur micro: " + err);
    }
}

async function generateClone() {
    const text = document.getElementById('clone-text').value;
    if (!text) return alert("Entrez un texte !");

    const loading = document.getElementById('loading-zone');
    const result = document.getElementById('result-zone');
    const btn = document.getElementById('generate-btn');

    loading.classList.remove('d-none');
    result.classList.add('d-none');
    btn.disabled = true;

    const formData = new FormData();
    formData.append('text', text);
    formData.append('source_type', currentSource);
    
    if (currentSource === 'library') formData.append('voice_id', currentVoiceId);
    else if (uploadedFile) formData.append('audio_data', uploadedFile);

    try {
        const response = await fetch('/audio_lab/clone/', {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            const player = document.getElementById('audio-player');
            const download = document.getElementById('download-link');
            
            player.src = data.audio_base64;
            download.href = data.audio_base64;
            download.download = data.filename;
            
            result.classList.remove('d-none');
            player.play();
        } else {
            alert("Erreur: " + data.error);
        }
    } catch (err) {
        alert("Échec de la connexion au serveur.");
    } finally {
        loading.classList.add('d-none');
        btn.disabled = false;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Init
selectVoice('naruto');
