/* ========================================
   LIFE QUEST — Leaderboard Particles
   ======================================== */

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('particles-container');
    if (!container) return;

    const colors = [
        'rgba(251, 191, 36, 0.6)',   // gold
        'rgba(148, 163, 184, 0.5)',  // silver
        'rgba(234, 88, 12, 0.5)',    // bronze / orange
        'rgba(139, 92, 246, 0.5)',   // purple
        'rgba(59, 130, 246, 0.4)',   // blue
        'rgba(236, 72, 153, 0.4)',   // pink
        'rgba(34, 197, 94, 0.4)',    // green
    ];

    const PARTICLE_COUNT = 35;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        const dot = document.createElement('div');
        dot.classList.add('particle');

        const size = Math.random() * 6 + 3;           // 3–9 px
        const left = Math.random() * 100;              // 0–100 %
        const delay = Math.random() * 8;               // 0–8 s
        const duration = Math.random() * 8 + 8;        // 8–16 s
        const color = colors[Math.floor(Math.random() * colors.length)];

        dot.style.width = size + 'px';
        dot.style.height = size + 'px';
        dot.style.left = left + '%';
        dot.style.background = color;
        dot.style.animationDelay = delay + 's';
        dot.style.animationDuration = duration + 's';

        container.appendChild(dot);
    }
});
