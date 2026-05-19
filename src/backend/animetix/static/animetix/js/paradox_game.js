document.addEventListener("DOMContentLoaded", function() {
    const scenarioText = document.getElementById('scenario-text');
    const thoughtLog = document.getElementById('thought-log-paradox');
    
    const configElement = document.getElementById('paradox-config');
    if (!configElement) return;
    
    const config = JSON.parse(configElement.textContent);
    
    const existingScenario = config.existingScenario;
    const t1 = config.t1;
    const t2 = config.t2;
    const intruder = config.intruder;
    const streamUrl = config.streamUrl;

    if (!existingScenario && intruder) {
        const url = `${streamUrl}?t1=${encodeURIComponent(t1)}&t2=${encodeURIComponent(t2)}&intruder=${encodeURIComponent(intruder)}`;
        const eventSource = new EventSource(url);
        
        eventSource.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'thought') {
                const step = document.createElement('div');
                step.className = 'animate__animated animate__fadeIn';
                step.innerHTML = `<i class="bi bi-cpu-fill me-2 text-primary"></i> ${data.content}`;
                thoughtLog.appendChild(step);
            } else if (data.type === 'result') {
                scenarioText.innerText = `"${data.content.scenario}"`;
                thoughtLog.classList.add('d-none');
                eventSource.close();
            } else if (data.type === 'error') {
                scenarioText.innerHTML = `<span class="text-danger">Erreur : ${data.content}</span>`;
                eventSource.close();
            }
        };
        eventSource.onerror = () => eventSource.close();
    }
});
