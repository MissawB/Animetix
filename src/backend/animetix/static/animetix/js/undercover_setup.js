function setPlayers(n) {
    const input = document.getElementById('num_players_input');
    if (input) input.value = n;
    document.querySelectorAll('.player-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById('p-btn-' + n);
    if (btn) btn.classList.add('active');
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

document.addEventListener('DOMContentLoaded', () => {
    // Initial setup if needed
});
