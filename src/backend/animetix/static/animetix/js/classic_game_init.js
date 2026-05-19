function confirmHint(type, message) {
    const configElement = document.getElementById('classic-config');
    if (!configElement) return;
    
    const config = JSON.parse(configElement.textContent);
    const revealUrlTemplate = config.revealUrlTemplate;

    if (confirm(message)) {
        window.location.href = revealUrlTemplate.replace('PLACEHOLDER', type);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const lastGuess = document.querySelector('.guess-row');
    if (lastGuess) {
        // Optionnel : lastGuess.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
