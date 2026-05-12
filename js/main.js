const root = document.documentElement;

// Place avatar.jpg in assets/avatar/ — set false to hide the photo
const SHOW_AVATAR = true;

if (SHOW_AVATAR) {
  document.querySelector('.hero-outer').classList.add('has-avatar');
}

// =========================================
// Canvas Setup
// =========================================
const canvas = document.getElementById('stars');
const ctx = canvas.getContext('2d');

let stars = [];
let nodes = [];
let pulses = []; // travelling signals along edges

function resize() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
  initStars();
  initNodes();
}

// =========================================
// Stars (dark mode)
// =========================================
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
  for (const s of stars) {
    const a = Math.max(0, s.base + Math.sin(t * s.freq + s.phase) * 0.1);
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${a})`;
    ctx.fill();
  }
}

// =========================================
// Network graph (light mode)
// =========================================
const NODE_COUNT  = 52;
const EDGE_DIST   = 155;
const NODE_SPEED  = 0.28;
const PULSE_SPEED = 1.4;
const PULSE_RATE  = 0.006; // chance per edge per frame to spawn a pulse

function initNodes() {
  nodes = Array.from({ length: NODE_COUNT }, () => ({
    x:  Math.random() * canvas.width,
    y:  Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * NODE_SPEED * 2,
    vy: (Math.random() - 0.5) * NODE_SPEED * 2,
    r:  Math.random() * 1.2 + 0.8,
  }));
  pulses = [];
}

function drawNetwork() {
  // Move nodes, bounce off walls
  for (const n of nodes) {
    n.x += n.vx;
    n.y += n.vy;
    if (n.x < 0)              { n.x = 0;              n.vx *= -1; }
    if (n.x > canvas.width)   { n.x = canvas.width;   n.vx *= -1; }
    if (n.y < 0)              { n.y = 0;              n.vy *= -1; }
    if (n.y > canvas.height)  { n.y = canvas.height;  n.vy *= -1; }
  }

  // Draw edges + maybe spawn pulses
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx   = nodes[j].x - nodes[i].x;
      const dy   = nodes[j].y - nodes[i].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > EDGE_DIST) continue;

      const alpha = (1 - dist / EDGE_DIST) * 0.13;
      ctx.beginPath();
      ctx.moveTo(nodes[i].x, nodes[i].y);
      ctx.lineTo(nodes[j].x, nodes[j].y);
      ctx.strokeStyle = `rgba(71,85,105,${alpha})`;
      ctx.lineWidth = 0.8;
      ctx.stroke();

      // Randomly fire a signal along this edge
      if (Math.random() < PULSE_RATE * (1 - dist / EDGE_DIST)) {
        pulses.push({ i, j, t: 0, dir: Math.random() < 0.5 ? 1 : -1 });
      }
    }
  }

  // Draw nodes
  for (const n of nodes) {
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(71,85,105,0.4)';
    ctx.fill();
  }

  // Advance and draw pulses
  pulses = pulses.filter(p => {
    p.t += PULSE_SPEED / 100;
    if (p.t > 1) return false;

    const from = p.dir === 1 ? nodes[p.i] : nodes[p.j];
    const to   = p.dir === 1 ? nodes[p.j] : nodes[p.i];
    const dx   = to.x - from.x;
    const dy   = to.y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > EDGE_DIST) return false;

    const px = from.x + dx * p.t;
    const py = from.y + dy * p.t;

    // Fade in/out at ends
    const fade = Math.sin(p.t * Math.PI);
    ctx.beginPath();
    ctx.arc(px, py, 1.8, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(71,85,105,${fade * 0.55})`;
    ctx.fill();

    return true;
  });
}

// =========================================
// Unified animation loop
// =========================================
function animate(t) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (root.getAttribute('data-theme') === 'light') {
    drawNetwork();
  } else {
    drawStars(t);
  }
  requestAnimationFrame(animate);
}

resize();
window.addEventListener('resize', resize);
requestAnimationFrame(animate);

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
// Theme Toggle
// =========================================
document.getElementById('theme-toggle').addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  root.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
});

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
