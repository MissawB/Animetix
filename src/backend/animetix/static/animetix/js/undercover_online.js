/**
 * Undercover Online Game Mode Logic
 * Handles WebSocket communication and UI updates for the online room.
 */

(function() {
    const gameContainer = document.getElementById('game-container') || document.body;
    const roomCode = gameContainer.dataset.roomCode;
    
    if (!roomCode) {
        console.error("Room code not found in data-room-code attribute.");
        return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/ws/undercover/${roomCode}/`;
    let socket = null;
    let myId = null;
    let isHost = false;

    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            const savedName = localStorage.getItem('undercover_name');
            if (savedName) {
                const nameInput = document.getElementById('player-name-input');
                if (nameInput) nameInput.value = savedName;
                socket.send(JSON.stringify({'action': 'set_name', 'name': savedName}));
            }
        };

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'room_state') updateUI(data);
            else if (data.type === 'private_role') updatePrivateRole(data);
            else if (data.type === 'chat_message') addChatMessage(data.message);
        };

        socket.onclose = () => setTimeout(connect, 2000);
    }

    window.flipCard = function() {
        const flipCardEl = document.getElementById('secret-flip-card');
        if (flipCardEl) flipCardEl.classList.toggle('flipped');
    };

    function updateUI(data) {
        // Player List & Host Identification
        const playerList = document.getElementById('players-list');
        if (!playerList) return;
        playerList.innerHTML = '';
        
        const nameInput = document.getElementById('player-name-input');
        const myName = nameInput ? nameInput.value : "";
        const me = data.players.find(p => p.name === myName);
        if (me) {
            myId = me.id;
            isHost = me.is_host;
        }

        data.players.forEach(p => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center border-0 px-4 py-3';
            li.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-3" style="width: 32px; height: 32px; font-size: 0.8rem;">
                        ${p.name.charAt(0).toUpperCase()}
                    </div>
                    <span class="fw-bold ${p.id === myId ? 'text-primary' : ''}">${p.name}</span>
                    ${p.is_host ? '<i class="bi bi-star-fill text-warning ms-2 shadow-sm" title="Hôte"></i>' : ''}
                </div>
                ${p.has_voted ? '<i class="bi bi-check-circle-fill text-success"></i>' : ''}
            `;
            playerList.appendChild(li);
        });

        const playerCountEl = document.getElementById('player-count');
        if (playerCountEl) playerCountEl.innerText = data.players.length;

        // Visibility Toggling
        const sections = {
            'lobby': document.getElementById('lobby-section'),
            'playing': document.getElementById('playing-section'),
            'revealed': document.getElementById('revealed-section')
        };

        Object.keys(sections).forEach(s => {
            if (sections[s]) sections[s].classList.toggle('d-none', data.state !== s);
        });

        const progressEl = document.getElementById('game-progress');
        if (progressEl) {
            progressEl.style.width = data.state === 'lobby' ? '33%' : (data.state === 'playing' ? '66%' : '100%');
        }

        if (data.state === 'lobby') {
            const hostControls = document.getElementById('host-controls');
            if (hostControls) hostControls.classList.toggle('d-none', !isHost);
            const waitingMsg = document.getElementById('waiting-msg');
            if (waitingMsg) waitingMsg.classList.toggle('d-none', isHost);
        } else if (data.state === 'playing') {
            const hostReveal = document.getElementById('host-reveal-controls');
            if (hostReveal) hostReveal.classList.toggle('d-none', !isHost);
            
            // Vote buttons
            const voteList = document.getElementById('vote-list');
            if (voteList) {
                voteList.innerHTML = '';
                data.players.forEach(p => {
                    if (p.id === myId) return; // Ne pas voter pour soi
                    const btn = document.createElement('button');
                    btn.className = `btn ${data.votes[myId] === p.id ? 'btn-danger' : 'btn-outline-danger'} rounded-pill fw-bold px-4 py-2`;
                    btn.innerHTML = `<i class="bi bi-bullseye me-2"></i> ${p.name}`;
                    btn.onclick = () => socket.send(JSON.stringify({'action': 'vote', 'voted_for': p.id}));
                    voteList.appendChild(btn);
                });
            }
        } else if (data.state === 'revealed') {
            const finalClueEl = document.getElementById('final-clue');
            if (finalClueEl) finalClueEl.innerText = `"${data.clue}"`;
            const hostRestart = document.getElementById('host-restart-controls');
            if (hostRestart) hostRestart.classList.toggle('d-none', !isHost);
        }
    }

    function updatePrivateRole(data) {
        const myWordEl = document.getElementById('my-word');
        if (data.word && myWordEl) {
            myWordEl.innerText = data.word;
            const myImageEl = document.getElementById('my-image');
            if (myImageEl) {
                if (data.image) {
                    myImageEl.src = data.image;
                    myImageEl.classList.remove('d-none');
                } else {
                    myImageEl.classList.add('d-none');
                }
            }
        }

        if (data.all_roles) {
            const container = document.getElementById('final-results-container');
            if (container) {
                container.innerHTML = '';
                const alert = document.createElement('div');
                alert.className = "col-12";
                alert.innerHTML = `
                    <div class="alert alert-warning p-4 rounded-4 shadow-sm border-0">
                        <h4 class="fw-bold">Le rideau tombe !</h4>
                        <p class="mb-0">Vous étiez : <strong class="text-uppercase">${data.role}</strong>. L'Undercover a-t-il été démasqué ?</p>
                    </div>
                `;
                container.appendChild(alert);
            }
        }
    }

    function addChatMessage(msg) {
        const box = document.getElementById('chat-box');
        if (!box) return;
        const div = document.createElement('div');
        const nameInput = document.getElementById('player-name-input');
        const isSelf = msg.user === (nameInput ? nameInput.value : "");
        
        if (msg.is_system) {
            div.className = 'chat-msg system';
            div.innerText = msg.text;
        } else {
            div.className = `chat-msg ${isSelf ? 'self' : 'other'}`;
            div.innerHTML = `<strong>${msg.user}:</strong> ${msg.text}`;
        }
        
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    // Initialize listeners when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const text = e.target.value.trim();
                    if (text) {
                        socket.send(JSON.stringify({'action': 'chat', 'message': text}));
                        e.target.value = '';
                    }
                }
            });
        }

        const btnSaveName = document.getElementById('btn-save-name');
        if (btnSaveName) {
            btnSaveName.onclick = () => {
                const nameInput = document.getElementById('player-name-input');
                const name = nameInput ? nameInput.value.trim() : "";
                if (name) {
                    localStorage.setItem('undercover_name', name);
                    socket.send(JSON.stringify({'action': 'set_name', 'name': name}));
                }
            };
        }

        const btnStartGame = document.getElementById('btn-start-game');
        if (btnStartGame) {
            btnStartGame.onclick = () => {
                const hostMedia = document.getElementById('host-media');
                const hostDiff = document.getElementById('host-difficulty');
                socket.send(JSON.stringify({
                    'action': 'set_settings', 
                    'media_type': hostMedia ? hostMedia.value : 'Anime',
                    'difficulty': hostDiff ? hostDiff.value : 'Normal'
                }));
                socket.send(JSON.stringify({'action': 'start_game'}));
            };
        }

        const btnReveal = document.getElementById('btn-reveal');
        if (btnReveal) btnReveal.onclick = () => socket.send(JSON.stringify({'action': 'reveal'}));
        
        const btnBackLobby = document.getElementById('btn-back-lobby');
        if (btnBackLobby) btnBackLobby.onclick = () => socket.send(JSON.stringify({'action': 'back_to_lobby'}));

        connect();
    });
})();
