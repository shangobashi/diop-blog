/* ===================================================================
   DIOP RESEARCH — Site JavaScript
   Theme toggle, scroll progress, particle canvas, post animations
   =================================================================== */

(function() {
    'use strict';

    // ---- THEME ----
    const root = document.documentElement;
    const saved = localStorage.getItem('diop-theme');
    if (saved) root.setAttribute('data-theme', saved);
    else root.setAttribute('data-theme', 'dark');

    document.getElementById('theme-toggle').addEventListener('click', () => {
        const current = root.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        localStorage.setItem('diop-theme', next);
    });

    // ---- SCROLL PROGRESS ----
    const progressBar = document.getElementById('scroll-progress');
    function updateProgress() {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        if (progressBar) progressBar.style.width = pct + '%';
    }
    window.addEventListener('scroll', updateProgress, { passive: true });

    // ---- NAV SHADOW ----
    const nav = document.getElementById('nav');
    function updateNav() {
        if (nav) {
            if (window.scrollY > 10) nav.classList.add('nav--scrolled');
            else nav.classList.remove('nav--scrolled');
        }
    }
    window.addEventListener('scroll', updateNav, { passive: true });

    // ---- CURSOR ORB ----
    const orb = document.querySelector('.cursor-orb');
    let orbX = -1000, orbY = -1000, targetX = -1000, targetY = -1000;
    if (orb && window.innerWidth > 900) {
        document.addEventListener('mousemove', (e) => {
            targetX = e.clientX - 260;
            targetY = e.clientY - 260;
        });
        function animateOrb() {
            orbX += (targetX - orbX) * 0.08;
            orbY += (targetY - orbY) * 0.08;
            orb.style.transform = 'translate(' + orbX + 'px, ' + orbY + 'px)';
            requestAnimationFrame(animateOrb);
        }
        animateOrb();
    }

    // ---- PARTICLE CANVAS ----
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let W, H;
        const nodes = [];
        const NODE_COUNT = 45;
        const MAX_DIST = 120;

        function resize() {
            W = canvas.width = window.innerWidth;
            H = canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', resize);

        for (let i = 0; i < NODE_COUNT; i++) {
            nodes.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                r: Math.random() * 1.5 + 0.5
            });
        }

        function drawParticles() {
            ctx.clearRect(0, 0, W, H);
            const style = getComputedStyle(document.documentElement);
            const accent = style.getPropertyValue('--accent').trim() || '#b7a285';
            const borderAlpha = style.getPropertyValue('--border').trim() || 'rgba(255,255,255,0.06)';

            // Update positions
            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                n.x += n.vx;
                n.y += n.vy;
                if (n.x < 0 || n.x > W) n.vx *= -1;
                if (n.y < 0 || n.y > H) n.vy *= -1;
                n.x = Math.max(0, Math.min(W, n.x));
                n.y = Math.max(0, Math.min(H, n.y));
            }

            // Draw edges
            ctx.strokeStyle = borderAlpha;
            ctx.lineWidth = 0.5;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < MAX_DIST) {
                        ctx.globalAlpha = (1 - dist / MAX_DIST) * 0.3;
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.stroke();
                    }
                }
            }

            // Draw nodes
            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                ctx.globalAlpha = 1;
                ctx.fillStyle = accent;
                ctx.beginPath();
                ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.globalAlpha = 1;

            requestAnimationFrame(drawParticles);
        }
        drawParticles();
    }

    // ---- POST CARD SCROLL ANIMATIONS ----
    const cards = document.querySelectorAll('.post-card');
    if (cards.length && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    e.target.classList.add('visible');
                    observer.unobserve(e.target);
                }
            });
        }, { threshold: 0.1 });
        cards.forEach(c => observer.observe(c));
    }

    // ---- POST COUNT ----
    const countEl = document.getElementById('post-count');
    if (countEl) {
        const grid = document.getElementById('posts-grid');
        if (grid) {
            const count = grid.querySelectorAll('.post-card').length;
            countEl.textContent = count;
        }
    }

    // ---- LIVE STATUS INDICATOR ----
    const liveDot = document.getElementById('live-dot');
    const liveStatus = document.getElementById('live-status');
    // Just keep it green for now — future hook for real status
    if (liveDot) liveDot.style.background = '#2d7d5a';

    // ---- CURSOR BLINK IN TERMINAL (pause on last line) ----
    const typingLine = document.querySelector('.typing .terminal__cursor');
    if (typingLine) {
        setTimeout(() => {
            typingLine.style.animation = 'none';
            typingLine.style.opacity = '0';
            // Replace with a period to show "completed"
            const parent = typingLine.parentElement;
            if (parent) {
                parent.innerHTML = parent.innerHTML.replace(/▊/g, 'writing...');
            }
        }, 4000);
    }

})();
