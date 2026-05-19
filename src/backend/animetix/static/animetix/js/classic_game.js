/**
 * Classic Game Logic
 * Manages hint confirmation and UI enhancements for the classic guess mode.
 */

window.confirmHint = function(type, message) {
    if (confirm(message)) {
        // We use a placeholder that will be replaced in the template or handled via data attributes
        const gameContainer = document.getElementById('game-main-col');
        const hintUrlTemplate = gameContainer ? gameContainer.dataset.hintUrlTemplate : '';
        if (hintUrlTemplate) {
            window.location.href = hintUrlTemplate.replace('PLACEHOLDER', type);
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    // Scroll automatique vers le dernier essai si présent
    const guessesContainer = document.querySelector('.guesses-container');
    if (guessesContainer && guessesContainer.dataset.gameOver === 'false') {
        const lastGuess = guessesContainer.querySelector('.guess-row');
        if (lastGuess) {
            // lastGuess.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});
