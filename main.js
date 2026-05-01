// =========================================
// Stars Canvas
// =========================================
const canvas = document.getElementById('stars');
const ctx = canvas.getContext('2d');
let stars = [];

function resize() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
  initStars();
}

function initStars() {
  stars = Array.from({ length: 180 }, () => ({
    x:     Math.random() * canvas.width,
    y:     Math.random() * canvas.height,
    r:     Math.random() * 0.85 + 0.25,
    base:  Math.random() * 0.4  + 0.08,
    phase: Math.random() * Math.PI * 2,
    freq:  Math.random() * 0.006 + 0.002,
  }));
}

function drawStars(t) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const s of stars) {
    const a = s.base + Math.sin(t * s.freq + s.phase) * 0.1;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${Math.max(0, a)})`;
    ctx.fill();
  }
  requestAnimationFrame(drawStars);
}

resize();
window.addEventListener('resize', resize);
requestAnimationFrame(drawStars);

// =========================================
// Scroll Reveal
// =========================================
const revealObs = new IntersectionObserver(
  (entries) => entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      revealObs.unobserve(e.target);
    }
  }),
  { threshold: 0.1 }
);

document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// =========================================
// Scroll Spy — active nav link
// =========================================
const sections   = document.querySelectorAll('section[id]');
const navAnchors = document.querySelectorAll('.nav-links a[data-section]');

const spyObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navAnchors.forEach(a =>
          a.classList.toggle('active', a.dataset.section === e.target.id)
        );
      }
    });
  },
  { threshold: 0.4 }
);

sections.forEach(s => spyObs.observe(s));

// =========================================
// Mobile Hamburger Menu
// =========================================
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('nav-links');

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navLinks.classList.toggle('open');
});

navLinks.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
  });
});
