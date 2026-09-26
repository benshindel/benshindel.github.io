// Day/night: the oil lamp. Lit = night (baize, lamplight); out = day (linen).
// The saved choice lives in localStorage("theme"); the <head> script applies it before first paint.
(function () {
  var root = document.documentElement;
  var table = document.querySelector('.table');
  var lamp = document.getElementById('lamp');
  var smoke = document.getElementById('smoke');
  var glow = document.querySelector('.glow');
  var mq = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;

  function isNight() {
    return root.dataset.theme ? root.dataset.theme === 'dark' : !!(mq && mq.matches);
  }
  function placeGlow() {
    if (!lamp || !table || !glow) return;
    var t = table.getBoundingClientRect(), l = lamp.getBoundingClientRect();
    if (!l.width) return;
    glow.style.setProperty('--gx', (l.left - t.left + l.width * .85) + 'px');
    glow.style.setProperty('--gy', (l.top - t.top + l.height * .45) + 'px');
  }
  function sync() {
    var night = isNight();
    root.dataset.night = night ? '1' : '0';
    if (lamp) lamp.setAttribute('aria-label', night ? 'Put out the lamp (switch to day)' : 'Light the lamp (switch to night)');
    placeGlow();
  }
  if (lamp) {
    lamp.addEventListener('click', function () {
      var wasNight = isNight();
      root.dataset.theme = wasNight ? 'light' : 'dark';
      try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
      sync();
      if (wasNight && smoke) { smoke.classList.remove('go'); void smoke.getBoundingClientRect(); smoke.classList.add('go'); }
    });
  }
  if (mq && mq.addEventListener) mq.addEventListener('change', sync);
  window.addEventListener('resize', placeGlow);
  window.addEventListener('load', placeGlow);
  sync();
})();
