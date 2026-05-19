function markAllRead() {
    const configElement = document.getElementById('notifications-config');
    if (!configElement) return;

    const config = JSON.parse(configElement.textContent);
    fetch(config.markReadUrl)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'ok') {
                window.location.reload();
            }
        });
}
