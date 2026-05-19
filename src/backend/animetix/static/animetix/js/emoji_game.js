document.addEventListener("DOMContentLoaded", function() {
    const emojiContainer = document.getElementById('emoji-container');
    const thoughtLog = document.getElementById('thought-log');
    
    const configElement = document.getElementById('emoji-config');
    if (!configElement) return;
    
    const config = JSON.parse(configElement.textContent);
    
    const existingEmojis = config.existingEmojis;
    const secret = config.secret;
    const streamUrl = config.streamUrl;

    if (!existingEmojis && secret) {
        const eventSource = new EventSource(`${streamUrl}?secret=${encodeURIComponent(secret)}`);
        
        eventSource.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'thought') {
                const step = document.createElement('div');
                step.className = 'animate__animated animate__fadeIn';
                step.innerHTML = `<i class="bi bi-cpu-fill me-2"></i> ${data.content}`;
                thoughtLog.appendChild(step);
            } else if (data.type === 'result') {
                emojiContainer.innerText = data.content;
                thoughtLog.classList.add('opacity-0');
                eventSource.close();
            } else if (data.type === 'error') {
                emojiContainer.innerHTML = `<span class="text-sm">🔮 Erreur : ${data.content}</span>`;
                eventSource.close();
            }
        };
        
        eventSource.onerror = () => eventSource.close();
    }
});
