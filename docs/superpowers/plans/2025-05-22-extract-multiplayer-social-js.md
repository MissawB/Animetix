# Extract Multiplayer & Social Modes JS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract inline JavaScript from multiplayer and social templates into dedicated `.js` files to improve modularity, security, and maintainability.

**Architecture:** Use `<script type="application/json">` tags in Django templates to pass server-side variables to external JavaScript files. Logic will be moved to `backend/api/animetix/static/animetix/js/`.

**Tech Stack:** Django Templates, JavaScript (ES6+), WebSockets (Django Channels).

---

### Task 1: Refactor Duel Room

**Files:**
- Create: `backend/api/animetix/static/animetix/js/duel_room.js`
- Modify: `backend/api/animetix/templates/animetix/social/duel_room.html`

- [ ] **Step 1: Create duel_room.js**
Extract logic from `duel_room.html`.

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const config = JSON.parse(document.getElementById('duel-config').textContent);
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
```

- [ ] **Step 2: Modify duel_room.html**
Add JSON config and include script.

```html
<!-- Inside block content or near game-ui -->
<script type="application/json" id="duel-config">
{
    "roomCode": "{{ duel.room_code|escapejs }}",
    "currentUsername": "{{ request.user.username|escapejs }}"
}
</script>

<!-- Replace block extra_js -->
{% block extra_js %}
<script src="{% static 'animetix/js/duel_room.js' %}"></script>
{% endblock %}
```

- [ ] **Step 3: Commit**

### Task 2: Refactor Notifications

**Files:**
- Create: `backend/api/animetix/static/animetix/js/notifications.js`
- Modify: `backend/api/animetix/templates/animetix/social/notifications.html`

- [ ] **Step 1: Create notifications.js**

```javascript
function markAllRead() {
    const config = JSON.parse(document.getElementById('notifications-config').textContent);
    fetch(config.markReadUrl)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'ok') {
                window.location.reload();
            }
        });
}
```

- [ ] **Step 2: Modify notifications.html**

```html
<script type="application/json" id="notifications-config">
{
    "markReadUrl": "{% url 'mark_notifications_read' %}"
}
</script>
<script src="{% static 'animetix/js/notifications.js' %}"></script>
```

- [ ] **Step 3: Commit**

### Task 3: Refactor Undercover Party

**Files:**
- Create: `backend/api/animetix/static/animetix/js/undercover_party.js`
- Modify: `backend/api/animetix/templates/animetix/undercover/undercover_party.html`

- [ ] **Step 1: Create undercover_party.js**

```javascript
let activeCivils = 0;
let activeUndercovers = 1;
let pendingElimination = null;
let gameOver = false;

document.addEventListener('DOMContentLoaded', () => {
    const config = JSON.parse(document.getElementById('undercover-config').textContent);
    activeCivils = config.numPlayers - 1;

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
    
    const agentInner = document.getElementById(`agent-${id}`);
    if (agentInner && agentInner.classList.contains('is-flipped')) return;

    pendingElimination = { id, role };
    const targetIdDisplay = document.getElementById('overlay-target-id');
    if (targetIdDisplay) targetIdDisplay.innerText = id;

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
    const finalResults = document.getElementById('final-results');
    if (winOverlay) {
        winOverlay.classList.add('hidden');
        winOverlay.classList.remove('flex');
    }
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
```

- [ ] **Step 2: Modify undercover_party.html**

```html
<script type="application/json" id="undercover-config">
{
    "numPlayers": {{ num_players|default:0 }}
}
</script>

{% block extra_js %}
<script src="{% static 'animetix/js/undercover_party.js' %}"></script>
{% endblock %}
```

- [ ] **Step 3: Commit**

### Task 4: Refactor Undercover Setup

**Files:**
- Create: `backend/api/animetix/static/animetix/js/undercover_setup.js`
- Modify: `backend/api/animetix/templates/animetix/undercover/undercover_setup.html`

- [ ] **Step 1: Create undercover_setup.js**

```javascript
function setPlayers(n) {
    const input = document.getElementById('num_players_input');
    if (input) input.value = n;
    document.querySelectorAll('.player-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById('p-btn-' + n);
    if (activeBtn) activeBtn.classList.add('active');
}

function setDiff(val) {
    fetch(`/switch_diff/${val}/`).then(() => window.location.reload());
}

function switchTab(mode) {
    const localTab = document.getElementById('tab-local');
    const onlineTab = document.getElementById('tab-online');
    const localContent = document.getElementById('content-local');
    const onlineContent = document.getElementById('content-online');

    if (mode === 'local') {
        if (localTab) {
            localTab.classList.add('active');
            localTab.classList.remove('opacity-40');
        }
        if (onlineTab) {
            onlineTab.classList.remove('active');
            onlineTab.classList.add('opacity-40');
        }
        if (localContent) localContent.classList.remove('hidden');
        if (onlineContent) onlineContent.classList.add('hidden');
    } else {
        if (onlineTab) {
            onlineTab.classList.add('active');
            onlineTab.classList.remove('opacity-40');
        }
        if (localTab) {
            localTab.classList.remove('active');
            localTab.classList.add('opacity-40');
        }
        if (onlineContent) onlineContent.classList.remove('hidden');
        if (localContent) localContent.classList.add('hidden');
    }
}
```

- [ ] **Step 2: Modify undercover_setup.html**

```html
<!-- Replace script block -->
<script src="{% static 'animetix/js/undercover_setup.js' %}"></script>
```

- [ ] **Step 3: Commit**
