/**
 * LifeQuest — auth.js
 * Particle canvas background + Password toggle
 */

/* ─── Particle Canvas ─── */
(function () {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let W, H, particles;

    const COLORS = [
        'rgba(255, 193,   7, VAL)',   // neon yellow
        'rgba(196, 102, 255, VAL)',   // neon purple
        'rgba(  0, 229, 255, VAL)',   // cyan
        'rgba(255, 140,   0, VAL)',   // orange
        'rgba(255, 255, 255, VAL)',   // white
    ];

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function randomColor() {
        const base = COLORS[Math.floor(Math.random() * COLORS.length)];
        const alpha = (Math.random() * 0.45 + 0.15).toFixed(2);
        return base.replace('VAL', alpha);
    }

    function createParticle() {
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 2.8 + 0.6,         // radius
            dx: (Math.random() - 0.5) * 0.45,       // x velocity
            dy: -(Math.random() * 0.55 + 0.15),     // float upward
            color: randomColor(),
            blink: Math.random() > 0.5,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 0.02 + 0.01,
        };
    }

    function initParticles(count) {
        particles = [];
        for (let i = 0; i < count; i++) particles.push(createParticle());
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);

        const now = performance.now() / 1000;

        particles.forEach(p => {
            // opacity pulse for blinking particles
            let alpha = 1;
            if (p.blink) alpha = 0.4 + 0.6 * Math.abs(Math.sin(now * p.speed * 60 + p.phase));

            ctx.save();
            ctx.globalAlpha = alpha;

            // outer soft glow
            const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 5);
            grd.addColorStop(0, p.color);
            grd.addColorStop(1, 'transparent');
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r * 5, 0, Math.PI * 2);
            ctx.fillStyle = grd;
            ctx.fill();

            // solid core
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();

            ctx.restore();

            // move
            p.x += p.dx;
            p.y += p.dy;

            // wrap
            if (p.y < -10) p.y = H + 10;
            if (p.x < -10) p.x = W + 10;
            if (p.x > W + 10) p.x = -10;
        });

        requestAnimationFrame(draw);
    }

    function init() {
        resize();
        // scale particle count to screen area
        const count = Math.floor((W * H) / 7000);
        initParticles(Math.min(count, 200));
        draw();
    }

    window.addEventListener('resize', () => {
        resize();
        const count = Math.floor((W * H) / 7000);
        initParticles(Math.min(count, 200));
    });

    // Start after DOM & styles have painted
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();


/* ─── Password Toggle(s) ─── */
document.addEventListener('DOMContentLoaded', function () {
    const toggles = document.querySelectorAll('.pw-toggle');

    toggles.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const wrapper = btn.closest('.input-wrapper');
            const input = wrapper.querySelector('input');
            const icon = btn.querySelector('i');

            if (!input) return;

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
                btn.setAttribute('aria-label', 'Hide password');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
                btn.setAttribute('aria-label', 'Show password');
            }
        });
    });
});
