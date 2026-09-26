"""Name relics (seen from above) and a Roman oil lamp, rendered from height maps like the coins."""
import math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sketch import smooth_noise
from coins3 import F, text_line, beads, METALS
METALS = dict(METALS, brass=dict(base=(196, 160, 92), shadow=(70, 50, 20), spec=(255, 240, 200), tones=[(150, 120, 70)], patina=0.1, crust=(120, 100, 70), tone_k=.3))

OUTD = os.environ.get("ART_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")) + "/"

def shade(h, mask, metal, rng, scale, light=(-0.55, -0.65, 0.6), crust_amt=1.0, fill_dark=None, grad=1.3):
    Hh, Ww = h.shape
    cav = np.clip(nd.gaussian_filter(h, scale * .03) - h, 0, None)
    crust = np.clip((smooth_noise(Hh, Ww, scale * .15, rng) * 0.8 + cav * 14 - 0.6) * 2.0, 0, 1) * mask * crust_amt
    h = h + 0.015 * crust
    gy, gx = np.gradient(h * scale * grad)
    nrm = np.dstack([-gx, -gy, np.ones_like(h)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    Lv = np.array(light, float); Lv /= np.linalg.norm(Lv)
    lam = np.clip((nrm * Lv).sum(2), 0, 1)
    Hv = Lv + np.array([0, 0, 1.0]); Hv /= np.linalg.norm(Hv)
    specl = np.clip((nrm * Hv).sum(2), 0, 1) ** 30
    cav = np.clip(nd.gaussian_filter(h, scale * .02) - h, 0, None)
    ao = np.clip(1 - cav * 9, 0.4, 1)
    M = METALS[metal]
    base, shad, spc, crc = (np.array(M[k], float) / 255 for k in ("base", "shadow", "spec", "crust"))
    col = np.broadcast_to(base, (Hh, Ww, 3)).copy()
    for t in M["tones"]:
        w = np.clip(smooth_noise(Hh, Ww, scale * rng.uniform(.35, .7), rng) * 1.2 - 0.15, 0, 1)[..., None]
        k = M["tone_k"] * w * .7
        col = col * (1 - k) + np.array(t) / 255 * k
    if M["patina"]:
        pat = np.clip(cav * 22 + 0.4 * smooth_noise(Hh, Ww, scale * .25, rng), 0, 1)[..., None] * M["patina"]
        col = col * (1 - pat) + np.array(M["tones"][0]) / 255 * pat
    cm = (crust * 0.8)[..., None]
    col = col * (1 - cm) + crc * cm
    shine = specl * (1 - crust) * (1 - 0.6 * M["patina"])
    rgb = shad + (col - shad) * (0.28 + 0.9 * lam[..., None]) * ao[..., None] + spc * shine[..., None] * 0.6
    if fill_dark is not None:       # engraved letters filled with black wax
        k = fill_dark[..., None]
        rgb = rgb * (1 - k) + np.array([0.09, 0.07, 0.06]) * k * (0.6 + 0.4 * lam[..., None])
    return np.dstack([np.clip(rgb, 0, 1), mask])

def rounded_rect_mask(W, H, x0, y0, x1, y1, r, soft):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx = np.clip(xx, x0 + r, x1 - r); cy = np.clip(yy, y0 + r, y1 - r)
    d = np.hypot(xx - cx, yy - cy) - r
    return np.clip(-d / soft, 0, 1), -d

def text_mask(W, H, text, font, cx, cy, track=1.12):
    m = Image.new("L", (W, H), 0)
    text_line(m, cx, cy, text, font, track=track)
    return np.array(m) / 255.0

def finish(rgba, ss, path):
    im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    im = im.resize((im.width // ss, im.height // ss), Image.LANCZOS)
    im = im.crop(im.getbbox())
    im.save(path, quality=88, method=6)
    return im

# ---------------------------------------------------------------- 1. brass cabinet nameplate, engraved + waxed
def plate_brass(ss=2, seed=1):
    rng = np.random.default_rng(seed)
    W, H = 760 * ss, 190 * ss
    m, d = rounded_rect_mask(W, H, 20 * ss, 20 * ss, W - 20 * ss, H - 20 * ss, 10 * ss, 3 * ss)
    bevel = np.clip(d / (14 * ss), 0, 1)
    h = 0.25 * m + 0.12 * bevel ** .6
    # inner ruled border (engraved)
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    gd.rounded_rectangle([44 * ss, 44 * ss, W - 44 * ss, H - 44 * ss], radius=6 * ss, outline=255, width=int(2.2 * ss))
    border = np.array(g.filter(ImageFilter.GaussianBlur(ss * .6))) / 255
    t = text_mask(W, H, "BEN SHINDEL", F("roman", 74 * ss), W / 2, H / 2 + 2 * ss, track=1.16)
    t = nd.gaussian_filter(t, ss * .5)
    h -= 0.06 * t + 0.03 * border
    # four countersunk screws
    for sx in (32, W / ss - 32):
        for sy in (32, H / ss - 32):
            yy, xx = np.mgrid[0:H, 0:W]
            r = np.hypot(xx - sx * ss, yy - sy * ss)
            h += np.where(r < 8 * ss, 0.03 * (1 - (r / (8 * ss)) ** 2), 0)
            slot = (np.abs((xx - sx * ss) * .6 - (yy - sy * ss) * .8) < 1.2 * ss) & (r < 7 * ss)
            h -= 0.02 * slot
    # brushed grain
    brush = nd.gaussian_filter(rng.standard_normal((H, W)), (0.4 * ss, 30 * ss)) * 0.004
    h += brush * m
    rgba = shade(h, m, "brass", rng, H, crust_amt=0.25, fill_dark=np.clip(t * 1.3, 0, 1) * 0.9)
    return finish(rgba, ss, OUTD + "name-plate.webp")

# ---------------------------------------------------------------- 2. Roman silver ingot with a stamped cartouche
def plate_ingot(ss=2, seed=2):
    rng = np.random.default_rng(seed)
    W, H = 780 * ss, 210 * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    # a cast bar, slightly waisted with rounded ends and a lumpy outline
    cx, cy = W / 2, H / 2
    u = (xx - cx) / (W * .46); v = (yy - cy) / (H * .38)
    waist = 1 - 0.10 * np.cos(u * math.pi) ** 2
    lump = 1 + 0.04 * smooth_noise(H, W, 60 * ss, rng)
    r = (np.abs(u) ** 6 + (np.abs(v) / waist) ** 2.2) ** (1 / 2.2) / lump
    m = np.clip((1 - r) / 0.03, 0, 1)
    dome = np.clip(1 - r, 0, 1) ** .5
    h = 0.22 * m + 0.10 * dome
    # sunken stamp with raised letters, like a maker's mark
    sm, sd = rounded_rect_mask(W, H, 110 * ss, 58 * ss, W - 110 * ss, H - 58 * ss, 14 * ss, 3 * ss)
    h -= 0.08 * sm
    t = text_mask(W, H, "BEN · SHINDEL", F("roman", 60 * ss), W / 2, H / 2 + 1 * ss, track=1.1)
    h += 0.07 * nd.gaussian_filter(t, ss * .6) * sm
    # hammer marks and casting pits
    h += 0.01 * smooth_noise(H, W, 40 * ss, rng) - (smooth_noise(H, W, 6 * ss, rng) > .6) * 0.012
    rgba = shade(h, m, "silver", rng, H, crust_amt=0.8)
    return finish(rgba, ss, OUTD + "name-ingot.webp")

# ---------------------------------------------------------------- 3. lead tablet, letters scratched in
def plate_lead(ss=2, seed=3):
    rng = np.random.default_rng(seed)
    W, H = 760 * ss, 200 * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    th = np.arctan2(yy - H / 2, xx - W / 2)
    m, d = rounded_rect_mask(W, H, 26 * ss, 26 * ss, W - 26 * ss, H - 26 * ss, 5 * ss, 2.5 * ss)
    # torn, irregular edges
    edge = smooth_noise(H, W, 14 * ss, rng) * 7 * ss
    m = np.clip((d + edge) / (2.5 * ss), 0, 1)
    h = 0.2 * m + 0.02 * smooth_noise(H, W, 80 * ss, rng)
    # letters incised with a stylus (sunken), plus ruled guide lines
    t = text_mask(W, H, "BEN SHINDEL", F("greek", 72 * ss), W / 2, H / 2, track=1.18)
    t = nd.gaussian_filter(t, ss * .7)
    h -= 0.07 * t
    for gy_ in (52, H / ss - 52):
        h -= 0.012 * (np.abs(yy - gy_ * ss) < 0.8 * ss) * m
    # a nail hole, as if it had been fixed to a wall
    r = np.hypot(xx - 50 * ss, yy - H / 2)
    m = m * np.clip((r - 7 * ss) / (1.5 * ss), 0, 1)
    rgba = shade(h, m, "billon", rng, H, crust_amt=1.2, grad=1.1)
    rgba[..., :3] = rgba[..., :3] * np.array([0.86, 0.88, 0.92])        # lead is bluish grey
    return finish(rgba, ss, OUTD + "name-lead.webp")

# ---------------------------------------------------------------- 4. gold tessera (a ticket token)
def plate_tessera(ss=2, seed=4):
    rng = np.random.default_rng(seed)
    W, H = 720 * ss, 200 * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    # an elongated oval with pointed ends (vesica), beaded rim, raised name
    u = (xx - W / 2) / (W * .47); v = (yy - H / 2) / (H * .42)
    r = np.sqrt(u ** 2 + v ** 2 * (1 + 0.8 * u ** 2))
    m = np.clip((1 - r) / 0.02, 0, 1)
    h = 0.22 * m + 0.05 * np.clip(1 - r, 0, 1)
    b = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(b)
    for k in range(120):
        a = k / 120 * 2 * math.pi
        # walk the same shape at r = 0.9
        uu, vv = math.cos(a), math.sin(a)
        s = 0.9 / math.sqrt(uu ** 2 + vv ** 2 * (1 + 0.8 * uu ** 2))
        px, py = W / 2 + uu * s * W * .47, H / 2 + vv * s * H * .42
        bd.ellipse([px - 2.4 * ss, py - 2.4 * ss, px + 2.4 * ss, py + 2.4 * ss], fill=255)
    h += 0.07 * np.array(b.filter(ImageFilter.GaussianBlur(ss * .6))) / 255 * m
    t = text_mask(W, H, "BEN SHINDEL", F("greek", 70 * ss), W / 2, H / 2 + 1 * ss, track=1.16)
    h += 0.08 * nd.gaussian_filter(t, ss * .6)
    rgba = shade(h, m, "gold", rng, H, crust_amt=0.0)
    return finish(rgba, ss, OUTD + "name-tessera.webp")

# ---------------------------------------------------------------- Roman oil lamp, seen from above
def oil_lamp(ss=3, seed=5):
    rng = np.random.default_rng(seed)
    W, H = 240 * ss, 150 * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx, cy, R = 95 * ss, H / 2, 58 * ss
    body = np.hypot(xx - cx, yy - cy) / R
    # nozzle: a rounded spout extending to the right
    nx0, nx1 = cx + R * .55, cx + R * 1.62
    t = np.clip((xx - nx0) / (nx1 - nx0), 0, 1)
    halfw = R * (0.46 - 0.10 * t)
    nozzle = np.where((xx > nx0) & (xx < nx1 + halfw), np.hypot(np.maximum(xx - nx1, 0), yy - cy) / halfw, 9)
    nozzle = np.minimum(nozzle, np.where((xx > nx0) & (xx <= nx1), np.abs(yy - cy) / halfw, 9))
    # ring handle on the left
    hx = cx - R * 1.12
    hr = np.hypot(xx - hx, yy - cy)
    handle = (hr < R * .33) & (hr > R * .17)
    shape = np.minimum(body, nozzle)
    m = np.clip((1 - shape) / 0.04, 0, 1)
    m = np.maximum(m, handle.astype(float) * 1.0)
    m = nd.gaussian_filter(m, ss * .6)
    dome = np.clip(1 - body, 0, 1) ** .45
    ndome = np.clip(1 - nozzle, 0, 1) ** .5 * (nozzle < 1)
    h = 0.30 * m + 0.25 * dome * (body < 1) + 0.16 * ndome * (body >= .98)
    for sgn in (-1, 1):   # volutes either side of the nozzle
        vx, vy = cx + R * .98, cy + sgn * R * .36
        vr = np.hypot(xx - vx, yy - vy)
        h += 0.05 * ((vr < R * .11) & (vr > R * .06)) + 0.03 * (vr <= R * .04)
    # concave discus with two raised rings and a small star in relief
    disc = body < 0.62
    h -= 0.16 * np.clip((0.62 - body) / 0.06, 0, 1)
    h += 0.05 * (np.abs(body - 0.66) < 0.025) + 0.03 * (np.abs(body - 0.74) < 0.018)
    st = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(st)
    pts = []
    for i in range(16):
        r_ = R * (.34 if i % 2 == 0 else .12)
        a = i * math.pi / 8
        pts.append((cx + r_ * math.cos(a), cy + r_ * math.sin(a)))
    sd.polygon(pts, fill=255)
    h += 0.06 * nd.gaussian_filter(np.array(st) / 255, ss * .8)
    # filling hole in the discus and wick hole at the nozzle tip
    fh = np.hypot(xx - (cx - R * .28), yy - (cy + R * .22)) < R * .09
    wh = np.hypot(xx - (nx1 - R * .05), yy - cy) < R * .13
    h -= 0.25 * nd.gaussian_filter((fh | wh).astype(float), ss * .7)
    h += 0.04 * handle
    h += 0.004 * smooth_noise(H, W, 20 * ss, rng) + 0.004 * smooth_noise(H, W, 3 * ss, rng)
    rgba = shade(h, m, "terracotta", rng, H, crust_amt=0.9, grad=1.1)
    im = finish(rgba, ss, OUTD + "lamp.webp")
    return im, ((nx1 - R * .05) / ss, cy / ss)

if __name__ == "__main__":
    for f in (plate_brass, plate_ingot, plate_lead, plate_tessera):
        im = f(); print(f.__name__, im.size)
    im, wick = oil_lamp(); print("lamp", im.size, "wick at", wick)

# ---------------------------------------------------------------- lamp flame (seen from above, leaning away from the nozzle)
def flame(W=320, H=200, seed=6):
    """A soft flame sprite pointing right. Alpha falls to zero well inside the canvas,
    so there is never a hard edge when it is scaled or blended."""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx, cy = W * .28, H * .5            # the wick
    dx = (xx - cx) / W; dy = (yy - cy) / H
    L = .55                              # flame length (fraction of W) downwind
    t = np.clip(dx / L, 0, 1)
    taper = (1 - t * t * (3 - 2 * t)) ** .8          # smooth narrowing toward the tip
    ay = np.where(dx < 0, .16, .16 * taper + 1e-3)
    ax = np.where(dx < 0, .07, .30)
    d = np.sqrt((dx / ax) ** 2 + (dy / ay) ** 2)
    core = np.exp(-(d / .45) ** 2)
    body = np.exp(-(d / .95) ** 2)
    rootblue = np.exp(-((dx + .01) / .03) ** 2 - (dy / .07) ** 2) * .45
    rgb = (np.array([1.0, .97, .85]) * core[..., None]
           + np.array([1.0, .62, .18]) * np.clip(body - core, 0, None)[..., None] * 1.25
           + np.array([.40, .50, 1.0]) * rootblue[..., None])
    a = np.clip(body * 1.1 + rootblue * .5, 0, 1)
    # guarantee a clean fade well before the canvas edge
    ex = np.minimum(xx, W - 1 - xx) / (W * .08); ey = np.minimum(yy, H - 1 - yy) / (H * .12)
    a = a * np.clip(np.minimum(ex, ey), 0, 1)
    rgb = np.clip(rgb / np.maximum(a[..., None], 1e-3), 0, 1)
    out = np.dstack([rgb, a])
    im = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
    im.save(OUTD + "flame.webp", quality=92, method=6)
    return im, (cx / W, cy / H)
