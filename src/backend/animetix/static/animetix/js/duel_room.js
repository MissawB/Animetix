document.addEventListener('DOMContentLoaded', () => {
    const configElement = document.getElementById('duel-config');
    if (!configElement) return;

    const config = JSON.parse(configElement.textContent);
    const roomCode = config.roomCode;
    const currentUsername = config.currentUsername;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const duelSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/duel/${roomCode}/`);

    const input = document.getElementById('duel-guess');
    const feed = document.getElementById('duel-feed');
    const winnerDisplay = document.getElementById('winner-name');

    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const val = input.value.trim();
                if (val) {
                    duelSocket.send(JSON.stringify({'type': 'guess', 'guess': val}));
                    input.value = '';
                }
            }
        });
    }

    duelSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log("Duel Event:", data);

        if (data.type === 'duel_state') {
            if (data.player2) {
                const p2Name = document.getElementById('p2-name');
                const p2Avatar = document.getElementById('p2-avatar');
                const waitingP2 = document.getElementById('waiting-p2');
                const playingUi = document.getElementById('playing-ui');

                if (p2Name) p2Name.innerText = data.player2;
                if (p2Avatar) {
                    p2Avatar.classList.remove('bg-gray-700');
                    p2Avatar.classList.add('bg-red-500');
                    p2Avatar.innerText = data.player2[0].toUpperCase();
                }
                if (waitingP2) waitingP2.classList.add('hidden');
                if (playingUi) playingUi.classList.remove('hidden');
            }
        }

        if (data.type === 'opponent_guess') {
            const div = document.createElement('div');
            div.innerText = `${data.player} a tenté... Score: ${data.score}%`;
            if (feed) feed.prepend(div);
            
            if (data.player !== currentUsername && window.sounds) {
                window.sounds.play('hover');
            }
        }

        if (data.type === 'duel_finished') {
            if (winnerDisplay) winnerDisplay.innerText = data.winner;
            const playingUi = document.getElementById('playing-ui');
            const victoryUi = document.getElementById('victory-ui');
            if (playingUi) playingUi.classList.add('hidden');
            if (victoryUi) victoryUi.classList.remove('hidden');
            if (window.sounds) window.sounds.play('win');
        }
    };
});
