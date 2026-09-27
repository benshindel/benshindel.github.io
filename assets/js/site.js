// Day/night: the oil lamp. Lit = night (baize, lamplight); out = day (linen).
// The saved choice lives in localStorage("theme"); the <head> script applies it before first paint.
// At night the lamp is the light source for the whole table: the light layer is centred on its
// flame, every object's shadow points away from it, and the flame flickers (window.__flicker is
// read by coins.js so the coins' highlights flicker with it).
(function () {
  var root = document.documentElement;
  var me = document.currentScript;
  var table = document.querySelector('.table');
  var lamp = document.getElementById('lamp');
  var mq = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var nightLight = document.querySelector('.light.night');
  var glow = document.querySelector('.glow');
  var halo = document.querySelector('.lamp .halo');
  var shadowed = document.querySelectorAll('.letter .coin img, .seal, .nameplate, .letter, .page img:not(.plain), .page .sheet, .plate figcaption');

  function isNight() {
    return root.dataset.theme ? root.dataset.theme === 'dark' : !!(mq && mq.matches);
  }
  function wick() {
    var l = lamp.getBoundingClientRect();
    return { x: l.left + l.width * .88, y: l.top + l.height * .30 };   // the middle of the flame
  }

  // centre the light on the flame, and point every shadow away from it
  function place() {
    if (!lamp || !table) return;
    var t = table.getBoundingClientRect(), w = wick();
    if (!lamp.getBoundingClientRect().width) return;
    table.style.setProperty('--gx', (w.x - t.left) + 'px');
    table.style.setProperty('--gy', (w.y - t.top) + 'px');
    var night = root.dataset.night === '1';
    Array.prototype.forEach.call(shadowed, function (el) {
      if (!night) { el.style.removeProperty('--sx'); el.style.removeProperty('--sy'); return; }
      var r = el.getBoundingClientRect();
      var dx = r.left + r.width / 2 - w.x, dy = r.top + r.height / 2 - w.y;
      var d = Math.hypot(dx, dy) || 1;
      var len = Math.min(14, 4 + d / 90);          // the lamp is low: farther things cast longer shadows
      el.style.setProperty('--sx', (dx / d * len).toFixed(2));
      el.style.setProperty('--sy', (dy / d * len).toFixed(2));
    });
  }

  function sync() {
    var night = isNight();
    root.dataset.night = night ? '1' : '0';
    if (lamp) lamp.setAttribute('aria-label', night ? 'Put out the lamp (switch to day)' : 'Light the lamp (switch to night)');
    place();
    if (night) flicker();
  }

  // ---- flicker: a few incommensurate wobbles plus the odd gust, ~30 times a second
  var fl = false, gust = 0, gustAim = 0;
  function flicker() {
    if (fl || reduce) return;
    fl = true;
    (function tick() {
      if (root.dataset.night !== '1') {
        fl = false; window.__flicker = 1;
        if (nightLight) nightLight.style.opacity = ''; if (glow) glow.style.opacity = ''; if (halo) halo.style.opacity = '';
        return;
      }
      var t = performance.now() / 1000;
      if (Math.random() < .02) gustAim = -Math.random() * .12;
      gustAim *= .96; gust += (gustAim - gust) * .25;
      var f = 1 + .03 * Math.sin(t * 7.3) + .02 * Math.sin(t * 13.1 + 1.7) + .015 * Math.sin(t * 23.9 + .4) + gust;
      window.__flicker = f;
      if (nightLight) nightLight.style.opacity = Math.min(1, Math.max(0, 1 - (f - 1) * 1.6)).toFixed(3);
      if (glow) glow.style.opacity = Math.min(1, f).toFixed(3);
      if (halo) halo.style.opacity = Math.min(1, .75 + (f - .9) * 1.6).toFixed(3);
      setTimeout(function () { requestAnimationFrame(tick); }, 30);
    })();
  }

  // ---- smoke from the wick when the lamp is put out: a thin ribbon that drifts off across the table
  // in the draught (leftward and a little up, since the lamp sits near the top of the page), swaying
  // and spreading as it goes. Drawn on a canvas at the screen's full resolution, only while it lasts.
  function smoke() {
    if (!lamp || !table || reduce) return;
    var l = lamp.getBoundingClientRect(), t = table.getBoundingClientRect();
    var w = { x: l.left + l.width * .88, y: l.top + l.height * .46 };   // the wick itself
    var W = 300, H = 240, dpr = Math.min(window.devicePixelRatio || 1, 2);
    var cv = document.createElement('canvas');
    cv.className = 'smoke'; cv.width = W * dpr; cv.height = H * dpr;
    cv.style.width = W + 'px'; cv.style.height = H + 'px';
    var sx = W * .8, sy = H * .9;                                       // where the wick sits in the canvas
    cv.style.left = (w.x - t.left - sx) + 'px'; cv.style.top = (w.y - t.top - sy) + 'px';
    table.appendChild(cv);
    var g = cv.getContext('2d'); g.scale(dpr, dpr);
    // one soft puff, drawn once and stamped many times
    var sp = document.createElement('canvas'); sp.width = sp.height = 64;
    var sg = sp.getContext('2d'), rg = sg.createRadialGradient(32, 32, 0, 32, 32, 32);
    rg.addColorStop(0, 'rgba(105,100,95,.7)'); rg.addColorStop(.5, 'rgba(105,100,95,.3)'); rg.addColorStop(1, 'rgba(105,100,95,0)');
    sg.fillStyle = rg; sg.fillRect(0, 0, 64, 64);
    var dx = -.28, dy = -.96, px = -dy, py = dx;                         // it rises, then the draught bends it left
    var P = [], t0 = performance.now(), prev = t0, seed = Math.random() * 6, owed = 0, EMIT = 1.4, LIFE = 2.8;
    (function step(now) {
      var age = (now - t0) / 1000, dt = Math.min(.05, (now - prev) / 1000);
      prev = now;
      if (age < EMIT) {                                 // emit by time, thinning as the wick cools
        owed += dt * 120 * (1 - age / EMIT);
        for (; owed >= 1; owed--) {
          var early = Math.random() * dt, v0 = 75 + Math.random() * 15;   // spread each frame's puffs along the path
          P.push({ s: v0 * early, v: v0, b: now - early * 1000, j: (Math.random() - .5) * .8 });
        }
      }
      g.clearRect(0, 0, W, H);
      for (var i = P.length - 1; i >= 0; i--) {
        var p = P[i], life = (now - p.b) / 1000;
        if (life > LIFE) { P.splice(i, 1); continue; }
        p.s += p.v * dt; p.v *= Math.pow(.45, dt);      // distance travelled; slowing as it cools
        // sway across the drift, growing with distance, the wave travelling along the ribbon
        var off = p.j + Math.sin(p.s * .045 - age * 2.6 + seed) * p.s * .14 + Math.sin(p.s * .11 - age * 3.4 + seed * 2) * p.s * .045;
        var x = sx + dx * p.s + px * off - p.s * p.s * .006, y = sy + dy * p.s + py * off;
        var r = 1.2 + life * 3.5 + p.s * .07;
        var a = Math.max(0, 1 - life / LIFE) * Math.min(1, life * 10);
        g.globalAlpha = a * .45;
        g.drawImage(sp, x - r * 1.5, y - r * 1.5, r * 3, r * 3);
      }
      if (P.length || age < EMIT) requestAnimationFrame(step); else cv.remove();
    })(t0);
  }

  if (lamp) {
    lamp.addEventListener('click', function () {
      var wasNight = isNight();
      root.dataset.theme = wasNight ? 'light' : 'dark';
      try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
      sync();
      if (wasNight) smoke();
    });
  }
  // ---- page transitions (site.css): the coin you pick up on the homepage glides to that page's coin,
  // and back again. Only that one coin is tagged, so the others simply fade with the rest of the page.
  var homeCoins = document.querySelectorAll('.letter a.coin');
  function tag(path) {
    Array.prototype.forEach.call(homeCoins, function (a) {
      var img = a.querySelector('img');
      if (img) img.style.viewTransitionName = new URL(a.href, location.href).pathname === path ? 'coin' : '';
    });
  }
  Array.prototype.forEach.call(homeCoins, function (a) {
    a.addEventListener('click', function () {
      var path = new URL(a.href, location.href).pathname;
      tag(path);
      try { sessionStorage.setItem('coin', path); } catch (e) {}
    });
  });
  if (homeCoins.length) {
    window.addEventListener('pagereveal', function (e) {
      if (!e.viewTransition) return;
      var from = null;
      try { from = navigation.activation.from && new URL(navigation.activation.from.url).pathname; } catch (err) {}
      if (!from) try { from = sessionStorage.getItem('coin'); } catch (err) {}
      tag(from);
      e.viewTransition.finished.then(function () { tag(null); });
    });
  }

  if (mq && mq.addEventListener) mq.addEventListener('change', sync);
  window.addEventListener('resize', place);
  window.addEventListener('load', function () {
    place();
    // live coin lighting comes after everything else has loaded
    if (document.querySelector('.coin, .seal')) {
      var s = document.createElement('script');
      s.src = me && me.src ? me.src.replace(/site\.js.*$/, 'coins.js') : '/assets/js/coins.js';
      s.async = true; document.body.appendChild(s);
    }
  });
  sync();
})();
