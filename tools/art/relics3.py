"""Round 3 of the relics: the terracotta oil lamp, its flame, and the bronze name plate, rebuilt with
the image-based shading from coins4.py (reflections of a room plus a soft key light).

  lamp()     -> lamp.webp       red-slipped terracotta, soot at the nozzle; 2x the old resolution
  flame()    -> flame.webp      an upright teardrop flame: blue root, bright body, orange skirt, glow
  tabula()   -> nameplate.webp  tabula ansata in statuary bronze, letters and mouldings rubbed bright,
                                dovetail handles bevelled, a bronze nail in each
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sketch import smooth_noise
from coins3 import F, text_line
from coins4 import shade, env, DAY, sstep, unit, Relief

OUTD = os.environ.get("ART_OUT", os.path.join(HERE, "out"))

def down(a, ss):
    s = a.shape
    return a.reshape(s[0] // ss, ss, s[1] // ss, ss, *s[2:]).mean((1, 3))

def normals(h):
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    return n / np.linalg.norm(n, axis=2, keepdims=True)

def shade_clay(alb, n, rough, L=DAY):
    """Fired clay: mostly diffuse, with a faint broad sheen from the slip."""
    lam = np.clip((n * L["dir"]).sum(-1), 0, 1)[..., None]
    En = env(n, L)
    nz = n[..., 2]
    r = np.dstack([2 * nz * n[..., 0], 2 * nz * n[..., 1], 2 * nz * nz - 1])
    p = np.exp2(7 * (1 - rough) + 1)
    sheen = (np.clip((r * L["dir"]).sum(-1), 0, 1) ** p * (p + 2) / 8)[..., None]
    col = alb * (L["col"] * lam * .85 + En * .55) + L["col"] * sheen * .07
    over = np.clip(col - .8, 0, None)
    return np.where(col > .8, .8 + over / (1 + over * 2.5), col)

def save_rgba(rgb, a, path, crop=True, **kw):
    im = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a]) * 255 + .5).astype(np.uint8), "RGBA")
    box = im.getbbox() if crop else None
    if box: im = im.crop(box)
    im.save(path, **kw)
    return im, box

# ---------------------------------------------------------------- the lamp
def lamp(k=2, ss=3, seed=5):
    rng = np.random.default_rng(seed)
    u = k * ss                                 # pixels per unit of the original 240x150 layout
    W, H = 240 * u, 150 * u
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx, cy, R = 95 * u, H / 2, 58 * u
    body = np.hypot(xx - cx, yy - cy) / R
    nx0, nx1 = cx + R * .55, cx + R * 1.62
    t = np.clip((xx - nx0) / (nx1 - nx0), 0, 1)
    halfw = R * (0.46 - 0.10 * t)
    nozzle = np.where((xx > nx0) & (xx < nx1 + halfw), np.hypot(np.maximum(xx - nx1, 0), yy - cy) / halfw, 9)
    nozzle = np.minimum(nozzle, np.where((xx > nx0) & (xx <= nx1), np.abs(yy - cy) / halfw, 9))
    hx = cx - R * 1.12
    hr = np.hypot(xx - hx, yy - cy)
    handle_in, handle_out = R * .17, R * .33
    shape = np.minimum(body, nozzle)
    m = np.clip((1 - shape) / .02, 0, 1)
    hm = sstep((handle_out - hr) / (.8 * ss)) * sstep((hr - handle_in) / (.8 * ss))
    m = np.maximum(m, hm)
    # heights, in pixels: a domed body, a lower rounded nozzle, a rounded ring handle
    dome = np.clip(1 - body, 0, 1)
    h = R * .42 * (1 - (1 - dome) ** 2.2) * (body < 1)
    ndome = np.clip(1 - nozzle, 0, 1)
    h = np.maximum(h, R * .26 * (1 - (1 - ndome) ** 2) * (nozzle < 1))
    ring_t = np.clip(1 - np.abs(hr - (handle_in + handle_out) / 2) / ((handle_out - handle_in) / 2), 0, 1)
    h = np.maximum(h, R * .16 * np.sqrt(ring_t) * (hr < handle_out))
    h = nd.gaussian_filter(h, 1.2 * ss)
    rel = Relief(H, ss, W)
    for sgn in (-1, 1):                         # volutes either side of the nozzle
        im, d = rel.layer()
        vx, vy = cx + R * .98, cy + sgn * R * .36
        d.ellipse([vx - R * .11, vy - R * .11, vx + R * .11, vy + R * .11], outline=255, width=int(R * .045))
        d.ellipse([vx - R * .035, vy - R * .035, vx + R * .035, vy + R * .035], fill=255)
        rel.add(im, R * .03, R * .02, dome=.8, dome_w=R * .025)
    # concave discus, framed by two raised rings, a star in relief
    disc = np.clip((0.62 - body) / .06, 0, 1)
    h -= R * .12 * sstep(disc) * (1 - (body / .62) ** 2 * .3)
    for rr, w_ in ((.66, .025), (.74, .018)):
        im, d = rel.layer()
        d.ellipse([cx - R * rr, cy - R * rr, cx + R * rr, cy + R * rr], outline=255, width=int(R * w_ * 2))
        rel.add(im, R * .025, R * w_, dome=.9, dome_w=R * w_)
    im, d = rel.layer()
    pts = []
    for i in range(16):
        r_ = R * (.34 if i % 2 == 0 else .12)
        a = i * math.pi / 8
        pts.append((cx + r_ * math.cos(a), cy + r_ * math.sin(a)))
    d.polygon(pts, fill=255)
    rel.add(im, R * .05, R * .03, dome=.6, dome_w=R * .06)
    h += rel.h
    # filling hole and wick hole
    fh = np.hypot(xx - (cx - R * .28), yy - (cy + R * .22)) / (R * .09)
    wx, wy = nx1 - R * .05, cy
    wh = np.hypot(xx - wx, yy - wy) / (R * .13)
    for q, dep in ((fh, .3), (wh, .25)):
        h -= R * dep * sstep((1 - q) / .35)
        h += R * .03 * np.exp(-((q - 1.05) / .12) ** 2)       # a little lip round each hole
    h += R * .004 * smooth_noise(H, W, R * .3, rng) + R * .0025 * smooth_noise(H, W, R * .03, rng) + R * .0012 * smooth_noise(H, W, R * .008, rng)
    n = normals(h)
    # materials: red slip over buff clay, worn through on the high points; soot round the wick
    slip = np.array([.58, .32, .22])
    buff = np.array([.80, .60, .44])
    alb = np.broadcast_to(slip, (H, W, 3)).copy()
    mott = smooth_noise(H, W, R * .25, rng)
    alb *= (1 + .08 * mott)[..., None]
    top = np.clip((h - nd.gaussian_filter(h, R * .12)) / (R * .03), 0, 1)
    wear = np.clip(top * 1.2 + .5 * smooth_noise(H, W, R * .06, rng) - .55, 0, 1)
    alb = alb * (1 - wear[..., None] * .7) + buff * wear[..., None] * .7
    cav = np.clip(nd.gaussian_filter(h, R * .04) - h, 0, None) / (R * .03)
    dirt = np.clip(cav * .8, 0, 1)
    alb = alb * (1 - dirt[..., None] * .45) + np.array([.28, .18, .12]) * dirt[..., None] * .45
    soot = np.exp(-(np.hypot((xx - wx) * .8, yy - wy) / (R * .34)) ** 2) * (1 + .4 * smooth_noise(H, W, R * .1, rng))
    soot = np.clip(soot, 0, 1) * .85
    alb = alb * (1 - soot[..., None]) + np.array([.08, .06, .05]) * soot[..., None]
    alb = np.where((wh < 1)[..., None], np.array([.05, .04, .035]), alb)       # the burnt wick
    rough = np.clip(.78 - .12 * wear + .15 * soot, 0, 1)
    rgb = shade_clay(alb, n, rough)
    rgb_o = down(rgb * m[..., None], ss) / np.maximum(down(m, ss), 1e-4)[..., None]
    im, box = save_rgba(rgb_o, down(m, ss), os.path.join(OUTD, "lamp.webp"), quality=86, method=6)
    wick = ((wx / ss - box[0]) / im.width, (wy / ss - box[1]) / im.height)
    return im, wick

# ---------------------------------------------------------------- the flame
def flame(W=200, H=320):
    """An upright flame, as the eye sees a lamp flame from a little in front: a teardrop that tapers
    up to a point, a blue root on the wick, a darker cone just above it, a white-yellow body with an
    orange skirt, and a soft glow round it all. The wick is at (50%, 84%) of the image."""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    wx, wy = W * .5, H * .84
    u = (xx - wx) / W
    v = (wy - yy) / H                       # up is positive
    Lh = .56                                # flame height, fraction of H
    t = v / Lh                              # 0 at the wick, 1 at the tip
    b = .16                                 # how far the rounded base sits below the wick
    q = np.clip((t + b) / (1 + b), 0, 1)
    # teardrop: round at the bottom (sqrt), drawn out to a point at the top
    prof = np.sqrt(q) * (1 - q) ** 1.35
    prof = .15 * prof / (np.sqrt(.27) * .73 ** 1.35)
    prof = np.maximum(prof, 1e-4)
    d = np.abs(u) / prof                    # 0 on the axis, 1 at the edge
    inside = np.clip((1 - d) / .35, 0, 1) * (t > -b) * (t < 1)
    body = sstep(inside) * sstep((1 - t) / .3) * sstep((t + b) / .08)
    core = sstep((1 - d / .55) / .5) * sstep((t - .12) / .15) * sstep((.8 - t) / .4)
    dark = np.exp(-((u / .035) ** 2) - ((t - .12) / .09) ** 2) * .45     # the cooler cone above the wick
    blue = np.exp(-((u / .075) ** 2) - ((t + .01) / .06) ** 2)
    glow = np.exp(-((u / .2) ** 2) - ((v - Lh * .45) / .32) ** 2)
    rgb = (np.array([1.0, .96, .80]) * (core * (1 - dark))[..., None]
           + np.array([1.0, .66, .20]) * np.clip(body - core, 0, 1)[..., None] * 1.1
           + np.array([.30, .45, 1.0]) * blue[..., None] * .9
           + np.array([1.0, .55, .18]) * glow[..., None] * .25)
    a = np.clip(body * .95 + blue * .6 + glow * .28, 0, 1)
    rgb = np.clip(rgb / np.maximum(a[..., None], 1e-3), 0, 1)
    ex = np.minimum(xx, W - 1 - xx) / (W * .1); ey = np.minimum(yy, H - 1 - yy) / (H * .08)
    a = a * np.clip(np.minimum(ex, ey), 0, 1)
    im, _ = save_rgba(rgb, a, os.path.join(OUTD, "flame.webp"), crop=False, quality=90, method=6)
    return im

# ---------------------------------------------------------------- the name plate
def poly(W, H, pts):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return im

def tabula(ss=3, seed=11):
    rng = np.random.default_rng(seed)
    u = ss
    W, H = 820 * u, 204 * u
    x0, x1, y0, y1 = 110 * u, W - 110 * u, 24 * u, H - 28 * u
    cyp = (y0 + y1) / 2
    rel = Relief(H, ss, W)
    # the plate and its dovetail handles, bevelled all round
    shape = poly(W, H, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    ears = []
    for side in (-1, 1):
        xe = x0 if side < 0 else x1
        tip = xe + side * 88 * u
        ears.append([(xe + side * -2 * u, cyp - 50 * u), (tip, cyp - 74 * u), (tip, cyp + 74 * u), (xe + side * -2 * u, cyp + 50 * u)])
        ImageDraw.Draw(shape).polygon(ears[-1], fill=255)
    m = np.asarray(shape, float) / 255
    dt = nd.distance_transform_edt(m > .5)
    h = 10 * u * (1 - (1 - np.clip(dt / (5 * u), 0, 1)) ** 2)
    h += 1.5 * u * np.clip(dt / (40 * u), 0, 1)                 # the handles are a touch thinner at their tips
    # mouldings: two raised frames
    for inset, amt, wdt in ((8, 5, 6), (19, 3.5, 4)):
        im, d = rel.layer()
        d.rectangle([x0 + inset * u, y0 + inset * u, x1 - inset * u, y1 - inset * u], outline=255, width=int(wdt * u))
        rel.add(im, amt * u, wdt * .5 * u, dome=.9, dome_w=wdt * .5 * u)
    frame = np.clip(rel.h / (3 * u), 0, 1)
    # a sunken field, the letters standing proud of it
    im, d = rel.layer()
    d.rectangle([x0 + 30 * u, y0 + 30 * u, x1 - 30 * u, y1 - 30 * u], fill=255)
    rel.cut(im, 3 * u, 2 * u)
    field = np.asarray(im, float) / 255
    im, _ = rel.layer()
    text_line(im, W / 2, cyp + 2 * u, "BEN·SHINDEL", F("roman", 66 * u), track=1.1)
    before = rel.h.copy()
    rel.add(im, 7 * u, 2.2 * u, dome=.35, dome_w=4 * u)
    letters = np.clip((rel.h - before) / (3 * u), 0, 1)
    h += rel.h / 1.5                                            # Relief exaggerates by 1.5; undo it here
    # a hole through each handle with a round-headed bronze nail in it
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    nails = np.zeros((H, W))
    for side in (-1, 1):
        ncx = (x0 - 50 * u) if side < 0 else (x1 + 50 * u)
        r = np.hypot(xx - ncx, yy - cyp)
        h -= 6 * u * sstep((12 * u - r) / (2 * u))                          # countersink
        head = np.clip(1 - (r / (8.5 * u)) ** 2, 0, 1)
        h = np.maximum(h, h * 0 + 9 * u * np.sqrt(head) * (r < 8.5 * u) + (h * (r >= 8.5 * u)))
        nails = np.maximum(nails, (r < 8.5 * u) * 1.0)
    h += .6 * u * smooth_noise(H, W, 30 * u, rng) + .15 * u * smooth_noise(H, W, 3 * u, rng)
    n = normals(h)
    # the plate's lower edge: a sliver of its thickness, like the coins
    wall_px = 5 * u
    sh = np.zeros_like(m); sh[wall_px:] = m[:-wall_px]
    wall = np.clip(sh - m, 0, 1)
    wall_n = np.dstack([np.zeros_like(m), np.full_like(m, .85), np.full_like(m, .5)])
    n = n * (1 - wall[..., None]) + wall_n * wall[..., None]
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    alpha = np.maximum(m, sh)
    # statuary bronze: dark brown-olive patina, rubbed to warm metal on the letters and mouldings
    base = np.array([.34, .26, .17])
    alb = np.broadcast_to(base, (H, W, 3)).copy()
    mott = smooth_noise(H, W, 60 * u, rng)
    alb = alb * (1 + .12 * mott[..., None])
    alb = alb * (1 - field[..., None] * .18)
    cav = np.clip(nd.gaussian_filter(h, 6 * u) - h, 0, None) / (3 * u)
    alb = alb * (1 - np.clip(cav, 0, 1)[..., None] * .5)
    bright = np.array([.86, .66, .40])
    rub = np.clip(letters * 1.2 + frame * .7 + nails * .8, 0, 1)
    edge_rub = np.clip(1 - dt / (6 * u), 0, 1) * (m > .5) * .5
    rub = np.clip(rub + edge_rub, 0, 1)
    alb = alb * (1 - rub[..., None]) + bright * rub[..., None]
    rough = np.clip(.62 - .38 * rub + .05 * mott, .15, .9)
    rough = np.where(wall > .5, .5, rough)
    alb = np.where(wall[..., None] > .5, alb * .7, alb)
    rgb = shade(alb, n, rough, DAY)
    A = down(alpha, ss)
    rgb_o = down(rgb * alpha[..., None], ss) / np.maximum(A, 1e-4)[..., None]
    im, _ = save_rgba(rgb_o, A, os.path.join(OUTD, "nameplate.webp"), quality=88, method=6)
    return im

if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    im, wick = lamp(); print("lamp", im.size, "wick at %.3f, %.3f" % wick)
    print("flame", flame().size)
    print("plate", tabula().size)

# ---------------------------------------------------------------- the picture frame
def frame(S=600, B=108, ss=2, seed=12):
    """Bronze picture moulding for CSS border-image (slice = B). A mitred profile runs round all four
    sides: an outer bead, a groove, an ogee rising to a flat with a fine bead, a cove, then the sight
    bead and a small lip down to the mat. A cast palmette sits over each mitre. Statuary bronze, with
    the beads and ornament rubbed bright."""
    rng = np.random.default_rng(seed)
    S2, B2 = S * ss, B * ss
    yy, xx = np.mgrid[0:S2, 0:S2].astype(float)
    dx, dy = np.minimum(xx, S2 - 1 - xx), np.minimum(yy, S2 - 1 - yy)
    din = np.minimum(dx, dy)                                  # distance in from the outer edge: mitres come for free
    m = sstep((B2 - din) / (.8 * ss)) * sstep((din + .5) / (.8 * ss))
    t = np.clip(din / B2, 0, 1)
    def bump(c, w): return np.sqrt(np.clip(1 - ((t - c) / w) ** 2, 0, 1))
    ogee = sstep((t - .18) / .37)
    cove = sstep((t - .7) / .16)
    prof = (.10 * bump(.055, .055)                             # outer bead
            + .07 + .15 * ogee * (1 - cove) + .02 * (1 - cove)  # ogee up to the flat, cove down again
            + .025 * bump(.62, .025)                            # fine bead on the flat
            + .10 * bump(.9, .05)                               # sight bead
            - .06 * sstep((t - .955) / .03))                    # lip down to the mat
    prof -= .03 * np.exp(-((t - .14) / .015) ** 2)             # a crisp groove after the outer bead
    h = B2 * prof * m
    # a hairline where the mitred pieces meet
    mitre = (np.abs(dx - dy) < .9 * ss) & (din < B2 * .96)
    h -= B2 * .012 * nd.gaussian_filter(mitre.astype(float), .5 * ss)
    # a cast rosette over each mitre: eight petals round a domed boss, on a round plate
    orn = Image.new("L", (S2, S2), 0); od = ImageDraw.Draw(orn)
    boss = Image.new("L", (S2, S2), 0); bd = ImageDraw.Draw(boss)
    for sx in (0, 1):
        for sy in (0, 1):
            cx = B2 * .5 if sx == 0 else S2 - 1 - B2 * .5
            cy = B2 * .5 if sy == 0 else S2 - 1 - B2 * .5
            R0 = B2 * .36
            od.ellipse([cx - R0, cy - R0, cx + R0, cy + R0], fill=255)
            for i in range(8):
                a = i * math.pi / 4 + math.pi / 8
                px, py = cx + R0 * .52 * math.cos(a), cy + R0 * .52 * math.sin(a)
                pts = []
                for k in np.linspace(0, 2 * math.pi, 24):
                    u, v = R0 * .3 * math.cos(k), R0 * .15 * math.sin(k)
                    pts.append((px + u * math.cos(a) - v * math.sin(a), py + u * math.sin(a) + v * math.cos(a)))
                bd.polygon(pts, fill=255)
            rb = R0 * .26
            bd.ellipse([cx - rb, cy - rb, cx + rb, cy + rb], fill=255)
    rel = Relief(S2, ss)
    rel.add(orn, B2 * .05, B2 * .05, dome=.6, dome_w=B2 * .1)
    rel.add(boss, B2 * .05, B2 * .03, dome=.9, dome_w=B2 * .05)
    ornh = rel.h / 1.5
    om = np.clip(ornh / (B2 * .02), 0, 1)
    h = np.maximum(h, (B2 * .2 + ornh) * (om > 0)) * m + h * 0
    h = np.where(om > 0, np.maximum(B2 * prof, B2 * .17) + ornh, h) * m
    # veins in each leaf, and a little casting texture
    h += B2 * .002 * smooth_noise(S2, S2, B2 * .3, rng)
    n = normals(nd.gaussian_filter(h, .5 * ss))
    base = np.array([.36, .27, .17])
    alb = np.broadcast_to(base, (S2, S2, 3)).copy() * (1 + .12 * smooth_noise(S2, S2, B2 * .5, rng))[..., None]
    cav = np.clip(nd.gaussian_filter(h, B2 * .04) - h, 0, None) / (B2 * .03)
    alb *= (1 - .55 * np.clip(cav, 0, 1))[..., None]
    beads = np.clip(bump(.055, .045) + bump(.9, .04) + bump(.62, .02), 0, 1)
    rub = np.clip(beads * .8 + om * .9 + np.clip((prof - .2) / .05, 0, 1) * .3, 0, 1) * (1 - np.clip(cav * 2, 0, 1))
    bright = np.array([.86, .68, .42])
    alb = alb * (1 - rub[..., None] * .8) + bright * rub[..., None] * .8
    rough = np.clip(.6 - .35 * rub, .15, .9)
    rgb = shade(alb, n, rough, DAY)
    A = down(m, ss)
    rgb_o = down(rgb * m[..., None], ss) / np.maximum(A, 1e-4)[..., None]
    im, _ = save_rgba(rgb_o, A, os.path.join(OUTD, "frame.webp"), crop=False, quality=88, method=6)
    return im
