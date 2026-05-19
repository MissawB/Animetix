/**
 * Codemanga Setup Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('setup-data');
    if (!dataElement) return;

    const config = JSON.parse(dataElement.textContent);
    const roomUrlPlaceholder = config.roomUrlPlaceholder;

    function joinRoom() {
        const input = document.getElementById('room-code-input');
        let code = input ? input.value.toUpperCase().trim() : '';
        const diffInput = document.querySelector('input[name="difficulty"]:checked');
        const difficulty = diffInput ? diffInput.value : 'Normal';
        
        if (!code) {
            code = Math.random().toString(36).substring(2, 6).toUpperCase();
        }
        
        const baseUrl = roomUrlPlaceholder.replace('PLACEHOLDER', code);
        window.location.href = `${baseUrl}?difficulty=${difficulty}`;
    }

    window.joinRoom = joinRoom;
});
