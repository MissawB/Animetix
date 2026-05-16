document.addEventListener("DOMContentLoaded", function() {
    const chatWindow = document.getElementById('chat-window');
    const oracleForm = document.getElementById('oracle-form');
    const oracleInput = document.getElementById('oracle-input');
    const anchor = document.getElementById('streaming-anchor');
    const submitBtn = document.getElementById('oracle-submit');

    function scrollToBottom() {
        if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    scrollToBottom();

    if (oracleForm) {
        oracleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const question = oracleInput.value.trim();
            if (!question) return;

            oracleInput.disabled = true;
            submitBtn.disabled = true;
            oracleInput.value = "";

            const userBubble = `
                <div class="d-flex justify-content-end mb-5 animate__animated animate__fadeInRight">
                    <div class="chat-bubble-user">
                        <p class="mb-0 text-lg">${question}</p>
                    </div>
                </div>
            `;
            anchor.insertAdjacentHTML('beforebegin', userBubble);
            scrollToBottom();

            const oracleContainerId = 'oracle-response-' + Date.now();
            const oracleThoughtId = 'oracle-thought-' + Date.now();
            const oracleTextId = 'oracle-text-' + Date.now();

            const oracleBubble = `
                <div class="d-flex gap-4 mb-5 animate__animated animate__fadeInLeft" id="${oracleContainerId}">
                    <div class="oracle-avatar flex-shrink-0">🔮</div>
                    <div class="chat-bubble-oracle border-warning/30 shadow-[0_0_40px_rgba(255,193,7,0.08)] w-full">
                        <div id="${oracleThoughtId}" class="mb-3 text-xs italic text-warning/50 font-mono flex flex-col gap-1"></div>
                        <p id="${oracleTextId}" class="mb-0 fw-bold leading-relaxed text-xl"></p>
                    </div>
                </div>
            `;
            anchor.insertAdjacentHTML('beforebegin', oracleBubble);
            scrollToBottom();

            const thoughtContainer = document.getElementById(oracleThoughtId);
            const textContainer = document.getElementById(oracleTextId);

            const streamUrl = oracleForm.dataset.streamUrl;
            const eventSource = new EventSource(`${streamUrl}?q=${encodeURIComponent(question)}`);

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.type === 'thought') {
                    const step = document.createElement('div');
                    step.className = 'animate__animated animate__fadeIn';
                    step.innerHTML = `<i class="bi bi-cpu-fill me-2"></i> ${data.content}`;
                    thoughtContainer.appendChild(step);
                } 
                else if (data.type === 'token') {
                    textContainer.innerText += data.content;
                }
                else if (data.type === 'done') {
                    const qBadge = document.querySelector('.q-badge');
                    if (qBadge) qBadge.innerText = `Potentiel de Prophétie : ${data.questions_left}/20`;
                    const progressBar = document.querySelector('.h-full.bg-gradient-to-r');
                    if (progressBar) progressBar.style.width = `${(data.questions_left / 20) * 100}%`;
                    
                    if (data.questions_left <= 0) {
                        window.location.reload();
                    } else {
                        oracleInput.disabled = false;
                        submitBtn.disabled = false;
                    }
                    eventSource.close();
                }
                else if (data.type === 'error') {
                    textContainer.innerHTML = `<span class="text-danger">🔮 Erreur des astres : ${data.content}</span>`;
                    eventSource.close();
                    oracleInput.disabled = false;
                    submitBtn.disabled = false;
                }
                
                scrollToBottom();
            };

            eventSource.onerror = function() {
                eventSource.close();
            };
        });
    }
});
