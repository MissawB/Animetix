/**
 * Code Manga Game Logic
 * Handles WebSocket communication and UI updates for the matrix grid.
 */

(function() {
    const gameContainer = document.getElementById('game-matrix') || document.body;
    const roomCode = gameContainer.dataset.roomCode;
    const lobbyUrl = gameContainer.dataset.lobbyUrl;
    
    if (!roomCode) {
        console.error("Room code not found in data-room-code attribute.");
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/codemanga/${roomCode}/`;
    let socket = new WebSocket(wsUrl);
    
    let myRole = localStorage.getItem('cm_role');
    let myTeam = localStorage.getItem('cm_team');
    let myName = localStorage.getItem('cm_name') || "Agent";

    socket.onopen = () => socket.send(JSON.stringify({action: 'set_player', name: myName, team: myTeam, role: myRole}));

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'state') {
            const room = data.room || data.message;
            if (room.state === 'lobby' && lobbyUrl) {
                window.location.href = lobbyUrl;
            } else {
                updateUI(room, data.my_role, data.my_team);
            }
        }
    };

    function updateUI(room, role, team) {
        myRole = role; 
        myTeam = team;
        
        const blueScoreEl = document.getElementById('blue-score');
        const redScoreEl = document.getElementById('red-score');
        if (blueScoreEl) blueScoreEl.innerText = 9 - (room.blue_score || 0);
        if (redScoreEl) redScoreEl.innerText = 8 - (room.red_score || 0);

        const turnText = document.getElementById('turn-text');
        if (turnText) {
            turnText.innerText = `Tour de l'équipe ${room.turn === 'blue' ? 'Bleue' : 'Rouge'}`;
            turnText.style.color = room.turn === 'blue' ? '#1ea3f0' : '#eb4924';
        }

        // Compact Player Lists
        const blueP = document.getElementById('blue-players');
        const redP = document.getElementById('red-players');
        if (blueP) blueP.innerHTML = ''; 
        if (redP) redP.innerHTML = '';
        
        room.players.forEach(p => {
            if (!p.team) return;
            const div = document.createElement('div');
            div.className = 'player-list-pill' + (p.name === myName ? ' border border-warning' : '');
            div.innerHTML = `<span class="truncate">${p.name}</span> <span class="ml-auto opacity-40 text-[6px]">${p.role === 'spymaster' ? 'SPY' : 'AGT'}</span>`;
            if (p.team === 'blue' && blueP) blueP.appendChild(div); 
            else if (p.team === 'red' && redP) redP.appendChild(div);
        });

        const grid = document.getElementById('game-grid');
        if (grid) {
            grid.innerHTML = '';
            room.grid.forEach((card, idx) => {
                const col = document.createElement('div');
                let stateClass = "";
                let borderClass = "";
                
                if (card.revealed) stateClass = `revealed role-${card.role}`;
                else if (myRole === 'spymaster') borderClass = `spymaster-border-${card.role}`;

                col.innerHTML = `
                    <div class="card-matrix ${stateClass} ${borderClass}" onclick="clickCard(${idx})">
                        ${card.image ? `<img src="${card.image}" class="card-bg-img" onerror="this.style.display='none'">` : ''}
                        <div class="card-overlay">
                            <div class="card-title-en text-[9px] md:text-[11px] text-shadow-tactical">${card.title_en}</div>
                            <div class="card-title-jp text-shadow-tactical">${card.title_jp || ''}</div>
                        </div>
                    </div>
                `;
                grid.appendChild(col);
            });
        }

        const winnerModal = document.getElementById('winner-modal');
        const winnerText = document.getElementById('winner-text');
        if (winnerModal) {
            if (room.winner) {
                winnerModal.classList.remove('d-none');
                if (winnerText) winnerText.innerText = `TEAM ${room.winner.toUpperCase()} VICTORIEUSE`;
            } else {
                winnerModal.classList.add('d-none');
            }
        }
    }

    window.pickSlot = function(team, role) {
        myTeam = team; myRole = role;
        localStorage.setItem('cm_team', team); localStorage.setItem('cm_role', role);
        socket.send(JSON.stringify({action: 'set_player', name: myName, team: team, role: role}));
    };

    window.startGame = function() { 
        socket.send(JSON.stringify({action: 'start_game'})); 
    };

    window.clickCard = function(idx) { 
        if (myRole === 'spymaster') return; 
        socket.send(JSON.stringify({action: 'click_card', index: idx})); 
    };
})();
