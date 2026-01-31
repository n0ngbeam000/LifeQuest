// Add Bootstrap form control classes to all input elements
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input').forEach(input => {
        input.classList.add('form-control', 'game-input');
    });
});
