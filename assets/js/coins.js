// Live coin lighting. Loaded by site.js after the page has finished loading.
// Each coin's static image stays underneath (it is also the fallback). On top, a small WebGL
// canvas re-lights the coin from its material sheet (base colour, normals, roughness) with the
// same model as tools/art/coins4.py: by day a soft window to the upper left, by night the oil
// lamp, flickering, from wherever the lamp sits relative to that coin. Hovering tilts the coin
// toward the pointer so the highlights move.
(function () {
  var holders = document.querySelectorAll('.coin, .seal');
  if (!holders.length || !window.WebGLRenderingContext) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;
  var lampEl = document.getElementById('lamp');
  var DPR = Math.min(window.devicePixelRatio || 1, 2);

  var VS = 'attribute vec2 p;varying vec2 uv;void main(){uv=vec2(p.x*.5+.5,.5-p.y*.5);gl_Position=vec4(p,0.,1.);}';
  var FS = [
    'precision mediump float;',
    'uniform sampler2D T;uniform vec3 Ld,Lc,Lw,Ls,Lh,Lg;uniform vec2 tilt;varying vec2 uv;',
    'vec3 env(vec3 v){vec3 c=mix(Lg,Lh,smoothstep(-.15,.3,v.z));c=mix(c,Ls,smoothstep(.3,1.,v.z));',
    ' return c+Lw*pow(max(dot(v,Ld),0.),3.);}',
    'void main(){',
    ' vec4 a=texture2D(T,vec2(uv.x*.5,uv.y));vec4 m=texture2D(T,vec2(.5+uv.x*.5,uv.y));',
    ' if(a.a<.004){gl_FragColor=vec4(0.);return;}',
    ' vec3 n=vec3(m.rg*2.-1.,0.);n.z=sqrt(max(1.-dot(n.xy,n.xy),0.));n=normalize(n+vec3(tilt,0.));',
    ' float ro=m.b;vec3 r=vec3(2.*n.z*n.xy,2.*n.z*n.z-1.);',
    ' vec3 En=env(n);vec3 E=env(r)*(1.-ro)+En*ro*.9;',
    ' float p=exp2(9.*(1.-ro)+1.);',
    ' float spec=min(pow(max(dot(r,Ld),0.),p)*(p+2.)/8.,6.);',
    ' float lam=max(dot(n,Ld),0.);float metal=smoothstep(0.,1.,(.92-ro)/.3);',
    ' vec3 col=mix(a.rgb*(Lc*lam*.9+En*.6),a.rgb*(E+Lc*spec),metal);',
    ' vec3 ov=max(col-.8,0.);col=mix(col,.8+ov/(1.+ov*2.5),step(.8,col));',
    ' gl_FragColor=vec4(col*a.a,a.a);}'
  ].join('\n');

  function norm(v) { var l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; }
  // must match DAY / NIGHT in coins4.py
  var DAY = { dir: norm([-.50, -.60, .62]), col: [1.30, 1.25, 1.15], win: [.95, .93, .88], sky: [.54, .53, .51], hor: [.30, .29, .27], gnd: [.62, .58, .52] };
  var NIGHT = { col: [2.4, 1.85, 1.2], win: [.9, .7, .45], sky: [.42, .32, .21], hor: [.20, .15, .10], gnd: [.05, .09, .06] };

  var coins = [];
  var seen = window.IntersectionObserver ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { e.target._coin.visible = e.isIntersecting; }); kick();
  }) : null;

  Array.prototype.forEach.call(holders, function (h) {
    var img = h.querySelector('img');
    if (!img) return;
    var src = img.getAttribute('src').replace(/\.webp$/, '-mat.webp');
    var cv = document.createElement('canvas');
    cv.className = 'gl'; cv.setAttribute('aria-hidden', 'true');
    var gl = cv.getContext('webgl', { premultipliedAlpha: true, alpha: true, antialias: false });
    if (!gl) return;
    function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; }
    var pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
    gl.useProgram(pr);
    var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var U = {};
    ['Ld', 'Lc', 'Lw', 'Ls', 'Lh', 'Lg', 'tilt'].forEach(function (k) { U[k] = gl.getUniformLocation(pr, k); });
    var c = { h: h, img: img, cv: cv, gl: gl, U: U, ready: false, visible: true, tilt: [0, 0], aim: [0, 0] };
    var tex = new Image();
    tex.decoding = 'async';
    tex.onload = function () {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      img.insertAdjacentElement('afterend', cv);
      c.ready = true; size(c); draw(c, performance.now());
      requestAnimationFrame(function () { cv.classList.add('on'); });
    };
    tex.src = src;
    if (!reduce) {
      h.addEventListener('pointermove', function (e) {
        var r = cv.getBoundingClientRect();
        c.aim = [((e.clientX - r.left) / r.width - .5) * .5, ((e.clientY - r.top) / r.height - .5) * .5];
        kick();
      });
      h.addEventListener('pointerleave', function () { c.aim = [0, 0]; kick(); });
    }
    h._coin = c; coins.push(c);
    if (seen) seen.observe(h);
  });

  function size(c) {
    var w = Math.round((c.img.clientWidth || 150) * DPR);
    if (c.cv.width !== w) { c.cv.width = c.cv.height = w; }
  }

  // the rotation the coin currently has on the page (it straightens on hover)
  function rotation(el) {
    var m = getComputedStyle(el).transform;
    if (!m || m === 'none') return 0;
    var v = m.match(/matrix\(([^)]+)\)/);
    if (!v) return 0;
    v = v[1].split(',').map(parseFloat);
    return Math.atan2(v[1], v[0]);
  }

  // light: 0 = day, 1 = night, eased; flicker for the flame
  var mix = root.dataset.night === '1' ? 1 : 0;
  function lerp(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function mul(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }

  function lampDir(c) {
    if (!lampEl) return norm([.55, -.55, .45]);
    var l = lampEl.getBoundingClientRect(), r = c.cv.getBoundingClientRect();
    var dx = (l.left + l.width * .88) - (r.left + r.width / 2), dy = (l.top + l.height * .30) - (r.top + r.height / 2);
    var d = Math.hypot(dx, dy) || 1;
    var el = Math.max(.55, Math.atan2(420, d));  // high enough that the far coins' lettering still catches it
    return norm([dx / d * Math.cos(el), dy / d * Math.cos(el), Math.sin(el)]);
  }

  function draw(c, now) {
    if (!c.ready) return;
    var gl = c.gl, U = c.U;
    var f = window.__flicker || 1;
    var ld = mix > 0 ? lampDir(c) : DAY.dir;
    var dir = norm(lerp(DAY.dir, ld, mix));
    var a = -(rotation(c.img) + rotation(c.h));  // page space -> the coin's own texture space
    var ca = Math.cos(a), sa = Math.sin(a);
    dir = [dir[0] * ca - dir[1] * sa, dir[0] * sa + dir[1] * ca, dir[2]];
    gl.viewport(0, 0, c.cv.width, c.cv.height);
    gl.uniform3fv(U.Ld, dir);
    gl.uniform3fv(U.Lc, lerp(DAY.col, mul(NIGHT.col, f), mix));
    gl.uniform3fv(U.Lw, lerp(DAY.win, mul(NIGHT.win, .6 + .4 * f), mix));
    gl.uniform3fv(U.Ls, lerp(DAY.sky, NIGHT.sky, mix));
    gl.uniform3fv(U.Lh, lerp(DAY.hor, NIGHT.hor, mix));
    gl.uniform3fv(U.Lg, lerp(DAY.gnd, NIGHT.gnd, mix));
    var tx = c.tilt[0] * ca - c.tilt[1] * sa, ty = c.tilt[0] * sa + c.tilt[1] * ca;
    gl.uniform2f(U.tilt, tx, ty);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  var running = false, last = 0;
  function frame(now) {
    var target = root.dataset.night === '1' ? 1 : 0;
    var busy = false;
    if (mix !== target) {
      var step = Math.min(1, (now - (last || now)) / 800);
      mix = target > mix ? Math.min(target, mix + step) : Math.max(target, mix - step);
      busy = true;
    }
    coins.forEach(function (c) {
      var d0 = c.aim[0] - c.tilt[0], d1 = c.aim[1] - c.tilt[1];
      if (Math.abs(d0) + Math.abs(d1) > .002) { c.tilt[0] += d0 * .15; c.tilt[1] += d1 * .15; busy = true; c.moving = true; }
      else if (c.moving) { c.tilt = c.aim.slice(); c.moving = false; c.dirty = true; }
    });
    var flick = mix > 0 && !reduce;
    // the coins also re-light while their hover transform (straightening) is animating
    var t = now - (window.__lastHover || 0) < 450;
    coins.forEach(function (c) { if (c.visible && (busy || flick || t || c.dirty)) { draw(c, now); c.dirty = false; } });
    last = now;
    if (busy || flick || t) {
      // at night, 30 frames a second is plenty for a flame
      if (flick && !busy) setTimeout(function () { requestAnimationFrame(frame); }, 28);
      else requestAnimationFrame(frame);
    } else running = false;
  }
  function kick() { if (!running) { running = true; last = 0; requestAnimationFrame(frame); } }
  window.__coinsKick = kick;
  Array.prototype.forEach.call(holders, function (h) {
    h.addEventListener('pointerenter', function () { window.__lastHover = performance.now(); kick(); });
    h.addEventListener('pointerleave', function () { window.__lastHover = performance.now(); kick(); });
  });
  new MutationObserver(kick).observe(root, { attributes: true, attributeFilter: ['data-night'] });
  window.addEventListener('resize', function () { coins.forEach(function (c) { size(c); c.dirty = true; }); kick(); });
  kick();
})();
