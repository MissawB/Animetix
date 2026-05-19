/**
 * Codemanga Room/Lobby Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('room-data');
    if (!dataElement) return;

    const config = JSON.parse(dataElement.textContent);
    const roomCode = config.roomCode;
    const gameUrl = config.gameUrl;
    
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/codemanga/${roomCode}/`;
    let socket = new WebSocket(wsUrl);
    let myRole = null;
    let myTeam = null;
    let myName = localStorage.getItem('cm_name') || `Agent#${Math.floor(Math.random()*900)+100}`;

    const nameInput = document.getElementById('player-name-lobby');
    if (nameInput) {
        nameInput.value = myName;
    }

    socket.onopen = () => {
        const overlay = document.getElementById('sync-overlay');
        if (overlay) overlay.classList.add('d-none');
        applyIdentity();
    };

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'redirect') {
            window.location.href = data.url;
            return;
        }
        if (data.type === 'state') {
            const room = data.room;
            if (room.state === 'playing') {
                window.location.href = gameUrl;
            } else {
                updateLobby(room.players || []);
            }
        }
    };

    function updateLobby(players) {
        const containers = {
            'blue-operative': document.getElementById('blue-operatives'),
            'blue-spymaster': document.getElementById('blue-spymaster'),
            'red-operative': document.getElementById('red-operatives'),
            'red-spymaster': document.getElementById('red-spymaster'),
            'spectators': document.getElementById('spectators-list')
        };
        
        Object.values(containers).forEach(c => {
            if (c) c.innerHTML = '';
        });

        players.forEach(p => {
            const entry = document.createElement('div');
            entry.className = 'player-entry';
            if (p.name === myName) entry.classList.add('me');
            entry.innerHTML = `<span class="opacity-30">#</span> <span>${p.name}</span>`;
            
            const key = `${p.team}-${p.role}`;
            if (containers[key]) {
                containers[key].appendChild(entry);
            } else if (containers['spectators']) {
                const avatar = document.createElement('div');
                avatar.className = 'w-10 h-10 rounded-full border-2 border-yellow-500 object-cover bg-gray-800 flex items-center justify-center text-xs font-black relative group cursor-help';
                avatar.innerHTML = `👤 <div class="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-black text-[10px] px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-50 shadow-xl">${p.name}</div>`;
                containers['spectators'].appendChild(avatar);
            }
        });
    }

    function applyIdentity() {
        const input = document.getElementById('player-name-lobby');
        myName = (input && input.value) || myName;
        localStorage.setItem('cm_name', myName);
        socket.send(JSON.stringify({action: 'set_player', name: myName, team: myTeam, role: myRole}));
    }

    window.applyIdentity = applyIdentity;

    window.pickSlot = function(team, role) {
        myTeam = team; myRole = role;
        localStorage.setItem('cm_team', team);
        localStorage.setItem('cm_role', role);
        socket.send(JSON.stringify({action: 'set_player', name: myName, team: team, role: role}));
    };

    window.startGame = function() {
        socket.send(JSON.stringify({action: 'start_game'}));
    };
});
