let activeCivils = 0;
let activeUndercovers = 1;
let pendingElimination = null;
let gameOver = false;

document.addEventListener('DOMContentLoaded', () => {
    const configElement = document.getElementById('undercover-config');
    if (configElement) {
        const config = JSON.parse(configElement.textContent);
        activeCivils = config.numPlayers - 1;
    }

    const overlayConfirmBtn = document.getElementById('overlay-confirm-btn');
    if (overlayConfirmBtn) {
        overlayConfirmBtn.addEventListener('click', () => {
            if (!pendingElimination) return;
            executeElimination(pendingElimination.id, pendingElimination.role);
            closeEliminationOverlay();
        });
    }
});

function toggleCard(id) {
    if (gameOver) return;
    const card = document.getElementById(`agent-${id}`);
    if (card) card.classList.toggle('is-flipped');
}

function promptElimination(id, role) {
    if (gameOver) return;
    
    // Anti-misclick security: Check if card is flipped (verso)
    const agentInner = document.getElementById(`agent-${id}`);
    if (agentInner && agentInner.classList.contains('is-flipped')) return;

    pendingElimination = { id, role };
    const targetIdDisplay = document.getElementById('overlay-target-id');
    if (targetIdDisplay) targetIdDisplay.innerText = id;

    // Show Overlay
    const eliminationOverlay = document.getElementById('elimination-overlay');
    if (eliminationOverlay) {
        eliminationOverlay.classList.remove('hidden');
        eliminationOverlay.classList.add('flex');
    }
}

function closeEliminationOverlay() {
    const eliminationOverlay = document.getElementById('elimination-overlay');
    if (eliminationOverlay) {
        eliminationOverlay.classList.add('hidden');
        eliminationOverlay.classList.remove('flex');
    }
    pendingElimination = null;
}

function executeElimination(id, role) {
    const agent = document.getElementById(`agent-${id}`);
    const stamp = document.getElementById(`stamp-${id}`);

    if (agent) agent.classList.add('eliminated');
    if (stamp) {
        stamp.innerText = role.toUpperCase();
        stamp.style.color = role === 'Civil' ? '#22c55e' : '#ef4444';
        stamp.style.borderColor = role === 'Civil' ? '#22c55e' : '#ef4444';
    }

    if (role === 'Undercover') {
        activeUndercovers--;
        finishGame(true);
    } else {
        activeCivils--;
        if (activeUndercovers >= activeCivils) {
            finishGame(false);
        }
    }
}

function finishGame(victory) {
    gameOver = true;
    const titleText = victory ? "VICTOIRE DES CIVILS" : "VICTOIRE UNDERCOVER";
    const msgText = victory ? "L'agent infiltré a été démasqué." : "Le système a été totalement corrompu.";
    const emojiText = victory ? "🏆" : "💀";

    const card = document.getElementById('win-card');
    const title = document.getElementById('win-title');
    const msg = document.getElementById('win-msg');
    const emoji = document.getElementById('win-emoji');
    const winOverlay = document.getElementById('win-overlay');
    const finalResults = document.getElementById('final-results');

    // Update Overlay Style
    if (card && title) {
        if (victory) {
            card.classList.add('border-green-500', 'bg-green-950/20');
            card.style.boxShadow = "0 0 100px rgba(34, 197, 94, 0.3)";
            title.style.color = "#22c55e";
        } else {
            card.classList.add('border-red-600', 'bg-red-950/20');
            card.style.boxShadow = "0 0 100px rgba(220, 38, 38, 0.3)";
            title.style.color = "#ef4444";
        }
    }

    if (title) title.innerText = titleText;
    if (msg) msg.innerText = msgText;
    if (emoji) emoji.innerText = emojiText;

    setTimeout(() => {
        if (winOverlay) {
            winOverlay.classList.remove('hidden');
            winOverlay.classList.add('flex');
        }
        if (finalResults) finalResults.classList.remove('hidden');
    }, 800);
}

function closeWinOverlay() {
    const winOverlay = document.getElementById('win-overlay');
    if (winOverlay) {
        winOverlay.classList.add('hidden');
        winOverlay.classList.remove('flex');
    }
    const finalResults = document.getElementById('final-results');
    if (finalResults) {
        window.scrollTo({ 
            top: finalResults.offsetTop - 50, 
            behavior: 'smooth' 
        });
    }
}

function triggerAbort() {
    if(confirm("Confirmer l'abandon de la mission ?")) {
        finishGame(false);
    }
}
