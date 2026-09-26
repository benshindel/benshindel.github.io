"""More name relics: tabula ansata, medallion, wax tablet, marble fragment, bronze letter tiles, ribbon banner."""
import math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sketch import smooth_noise
import relics
from relics import shade, finish, text_mask, rounded_rect_mask, OUTD
from coins3 import F, text_arc, beads

relics.METALS.update({
    "statuary": dict(base=(92, 74, 50), shadow=(26, 20, 14), spec=(255, 226, 170), tones=[(62, 58, 44), (80, 66, 40)], patina=0.15, crust=(70, 62, 48), tone_k=.4),
    "terracotta": dict(base=(168, 104, 74), shadow=(70, 40, 28), spec=(150, 104, 80), tones=[(136, 84, 60), (190, 150, 118)], patina=0.0, crust=(186, 164, 132), tone_k=.45),
    "wood":   dict(base=(122, 84, 52), shadow=(40, 26, 14), spec=(230, 200, 160), tones=[(96, 62, 36)], patina=0.0, crust=(90, 70, 50), tone_k=.4),
    "wax":    dict(base=(58, 40, 30), shadow=(16, 10, 8), spec=(200, 170, 140), tones=[(40, 28, 22)], patina=0.0, crust=(60, 44, 34), tone_k=.3),
    "marble": dict(base=(226, 222, 212), shadow=(120, 116, 108), spec=(255, 255, 250), tones=[(200, 194, 182)], patina=0.0, crust=(190, 176, 150), tone_k=.4),
})

def poly_mask(W, H, pts, soft):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.array(im.filter(ImageFilter.GaussianBlur(soft))) / 255.0

# ---------------------------------------------------------------- tabula ansata: Roman plaque with dovetail handles
def tabula(ss=2, seed=11):
    rng = np.random.default_rng(seed)
    W, H = 820 * ss, 200 * ss
    x0, x1, y0, y1 = 110 * ss, W - 110 * ss, 24 * ss, H - 24 * ss
    m = poly_mask(W, H, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ss)
    for side in (-1, 1):
        xe = x0 if side < 0 else x1
        tip = xe + side * 88 * ss
        m = np.maximum(m, poly_mask(W, H, [(xe, H / 2 - 50 * ss), (tip, H / 2 - 74 * ss), (tip, H / 2 + 74 * ss), (xe, H / 2 + 50 * ss)], ss))
    h = 0.2 * m
    frame = np.zeros((H, W))
    for inset, amt in ((8, .06), (19, .04)):
        fm = Image.new("L", (W, H), 0)
        ImageDraw.Draw(fm).rectangle([x0 + inset * ss, y0 + inset * ss, x1 - inset * ss, y1 - inset * ss], outline=255, width=int(5 * ss))
        f_ = np.array(fm.filter(ImageFilter.GaussianBlur(ss * 1.1))) / 255
        h += amt * f_; frame = np.maximum(frame, f_)
    # field slightly sunken inside the frame so the letters stand proud
    fld, _ = rounded_rect_mask(W, H, x0 + 30 * ss, y0 + 30 * ss, x1 - 30 * ss, y1 - 30 * ss, 2 * ss, 2 * ss)
    h -= 0.03 * fld
    t = text_mask(W, H, "BEN·SHINDEL", F("roman", 66 * ss), W / 2, H / 2 + 2 * ss, track=1.1)
    tt = nd.gaussian_filter(t, ss * .5)
    h += 0.10 * tt
    yy, xx = np.mgrid[0:H, 0:W]
    for side in (-1, 1):
        cx = (x0 - 50 * ss) if side < 0 else (x1 + 50 * ss)
        r = np.hypot(xx - cx, yy - H / 2)
        m = m * np.clip((r - 9 * ss) / (1.5 * ss), 0, 1)
        h += 0.03 * np.clip(1 - np.abs(r - 13 * ss) / (3 * ss), 0, 1)
    rgba = shade(h, m, "statuary", rng, H, crust_amt=.5, grad=1.4)
    # letter faces and frame ridges rubbed bright, as on handled bronze
    hi = np.clip(tt * 1.4, 0, 1) * .75 + frame * .45
    hi = np.clip(hi, 0, 1)[..., None]
    rgba[..., :3] = rgba[..., :3] * (1 - hi) + np.array([0.86, 0.70, 0.42]) * hi * (0.75 + 0.25 * rgba[..., :3].mean(-1, keepdims=True) / .5)
    rgba[..., :3] = np.clip(rgba[..., :3], 0, 1)
    return finish(rgba, ss, OUTD + "name-tabula.webp")

# ---------------------------------------------------------------- medallion: name round the rim, BS monogram
def medallion(ss=2, seed=12):
    rng = np.random.default_rng(seed)
    S = 440 * ss; c = S / 2; R = 190 * ss
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    d = np.hypot(xx - c, yy - c)
    m = np.clip((R - d) / (3 * ss), 0, 1)
    h = 0.2 * m + 0.06 * np.clip((d - R * .9) / (R * .06), 0, 1) * m        # raised rim
    b = Image.new("L", (S, S), 0); bd = ImageDraw.Draw(b)
    beads(bd, (c, c), R * .84, 90, R * .014)
    L = Image.new("L", (S, S), 0)
    text_arc(L, c, c, R * .7, "BEN SHINDEL", F("roman", int(R * .2)), -90, track=1.15)
    text_arc(L, c, c, R * .72, "· MMXXVI ·", F("roman", int(R * .12)), 90, bottom=True, track=1.2)
    mono = Image.new("L", (S, S), 0)
    from coins3 import text_line
    text_line(mono, c, c + R * .02, "BS", F("greek", int(R * .5)), track=.92)
    h += 0.05 * np.array(b.filter(ImageFilter.GaussianBlur(ss))) / 255
    h += 0.07 * nd.gaussian_filter(np.array(L) / 255, ss * .6)
    mm = np.array(mono) / 255
    dt = nd.distance_transform_edt(mm > .1) / (6 * ss)
    h += 0.1 * nd.gaussian_filter(np.clip(dt, 0, 1) ** .6, ss * .6)
    rgba = shade(h, m, "silver", rng, S * .5, crust_amt=.6)
    return finish(rgba, ss, OUTD + "name-medallion.webp")

# ---------------------------------------------------------------- Roman wax writing tablet
def wax_tablet(ss=2, seed=13):
    rng = np.random.default_rng(seed)
    W, H = 780 * ss, 220 * ss
    m, d = rounded_rect_mask(W, H, 20 * ss, 20 * ss, W - 20 * ss, H - 20 * ss, 8 * ss, 2 * ss)
    wm, wd = rounded_rect_mask(W, H, 52 * ss, 50 * ss, W - 52 * ss, H - 50 * ss, 4 * ss, 2 * ss)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    grain = nd.gaussian_filter(rng.standard_normal((H, W)), (0.6 * ss, 40 * ss)); grain /= np.abs(grain).max()
    h = 0.25 * m - 0.06 * wm + 0.01 * grain * (1 - wm)
    t = text_mask(W, H, "BEN SHINDEL", F("greek", 70 * ss), W / 2, H / 2 + 2 * ss, track=1.18)
    t = nd.gaussian_filter(t, ss * .5)
    h -= 0.03 * t * wm
    frame = shade(h, m, "wood", rng, H, crust_amt=0)
    wax = shade(h, m, "wax", rng, H, crust_amt=0)
    k = wm[..., None]
    rgb = frame[..., :3] * (1 - k) + wax[..., :3] * k
    # scratched letters show the pale wood underneath
    lt = (t * wm)[..., None]
    rgb = rgb * (1 - lt * .85) + np.array([0.62, 0.48, 0.32]) * lt * .85
    # a little wood grain colour on the frame
    rgb = rgb * (1 + 0.06 * grain[..., None] * (1 - k))
    return finish(np.dstack([np.clip(rgb, 0, 1), m]), ss, OUTD + "name-wax.webp")

# ---------------------------------------------------------------- marble inscription fragment
def marble_fragment(ss=2, seed=14):
    rng = np.random.default_rng(seed)
    W, H = 800 * ss, 230 * ss
    pts = [(30, 70), (120, 22), (330, 34), (430, 18), (610, 30), (770, 58), (760, 150), (700, 205), (520, 196), (470, 212),
           (260, 200), (140, 214), (40, 170)]
    pts = [(x * ss + rng.normal(0, 3 * ss), y * ss + rng.normal(0, 3 * ss)) for x, y in pts]
    m = poly_mask(W, H, pts, 1.2 * ss)
    rough = smooth_noise(H, W, 30 * ss, rng)
    h = 0.22 * m + 0.012 * rough + 0.006 * smooth_noise(H, W, 4 * ss, rng)
    t = text_mask(W, H, "BEN·SHINDEL", F("roman", 76 * ss), W / 2, H / 2 + 4 * ss, track=1.1)
    # V-cut letters: deepest along the stroke centre
    dt = nd.distance_transform_edt(t > .3) / (5 * ss)
    vcut = np.clip(dt, 0, 1)
    h -= 0.07 * nd.gaussian_filter(vcut, ss * .5)
    # break edges: chipped, slightly lower
    edge = nd.distance_transform_edt(m > .5) / (10 * ss)
    h -= 0.03 * np.clip(1 - edge, 0, 1) * (0.5 + 0.5 * rough)
    rgba = shade(h, m, "marble", rng, H, crust_amt=.5, grad=1.2)
    # traces of red paint in the letters
    red = (vcut > .15)[..., None] * 0.55
    rgba[..., :3] = rgba[..., :3] * (1 - red) + np.array([0.55, 0.16, 0.10]) * red
    # grey veins
    v = np.exp(-np.abs(np.sin(np.mgrid[0:H, 0:W][1] * .004 + np.mgrid[0:H, 0:W][0] * .006 + smooth_noise(H, W, 120 * ss, rng) * 5)) * 14)
    rgba[..., :3] *= (1 - 0.18 * v[..., None])
    return finish(rgba, ss, OUTD + "name-marble.webp")

# ---------------------------------------------------------------- bronze letter tiles (a nod to crosswords)
def letter_tiles(ss=2, seed=15):
    rng = np.random.default_rng(seed)
    word = "BEN SHINDEL"
    tile, gap = 72 * ss, 8 * ss
    W, H = int(len(word) * (tile + gap) + 40 * ss), int(tile + 70 * ss)
    canvas = np.zeros((H, W, 4))
    x = 20 * ss
    for i, ch in enumerate(word):
        if ch == " ":
            x += tile * .45; continue
        S = int(tile * 1.3)
        m, d = rounded_rect_mask(S, S, (S - tile) / 2, (S - tile) / 2, (S + tile) / 2, (S + tile) / 2, 7 * ss, 1.5 * ss)
        bevel = np.clip(d / (6 * ss), 0, 1)
        h = 0.2 * m + 0.05 * bevel ** .5
        t = text_mask(S, S, ch, F("roman", int(tile * .66)), S / 2, S / 2 + 2 * ss, track=1)
        h += 0.08 * nd.gaussian_filter(t, ss * .6)
        rgba = shade(h, m, rng.choice(["bronze", "brass"]) if i % 3 else "brass", rng, S, crust_amt=.5)
        im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").rotate(rng.uniform(-6, 6), resample=Image.BICUBIC)
        arr = np.array(im) / 255.0
        oy = int((H - S) / 2 + rng.normal(0, 3 * ss))
        ox = int(x - (S - tile) / 2)
        sub = canvas[oy:oy + S, ox:ox + S]
        a = arr[..., 3:4]
        sub[..., :3] = sub[..., :3] * (1 - a) + arr[..., :3] * a
        sub[..., 3:4] = np.maximum(sub[..., 3:4], a)
        x += tile + gap
    return finish(canvas, ss, OUTD + "name-tiles.webp")

# ---------------------------------------------------------------- ribbon banner with swallowtail ends
def ribbon(ss=2, seed=16):
    rng = np.random.default_rng(seed)
    W, H = 840 * ss, 200 * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cy = H / 2
    xL, xR = 150 * ss, W - 150 * ss
    main = poly_mask(W, H, [(xL, cy - 52 * ss), (xR, cy - 52 * ss), (xR, cy + 52 * ss), (xL, cy + 52 * ss)], ss)
    tails = []
    for side in (-1, 1):
        xe = xL if side < 0 else xR
        xo = xe + side * 120 * ss
        tails.append(poly_mask(W, H, [(xe - side * 10 * ss, cy - 36 * ss), (xo, cy - 36 * ss), (xo - side * 34 * ss, cy + 6 * ss),
                                      (xo, cy + 48 * ss), (xe - side * 10 * ss, cy + 48 * ss)], ss))
    tail = np.maximum(*tails)
    m = np.maximum(main, tail)
    # the tails sit lower (folded behind), the band bows gently
    bow = 0.05 * np.cos((xx - W / 2) / (xR - xL) * math.pi)
    h = 0.2 * main + 0.12 * tail * (1 - main) + bow * main
    # fold shading where band meets tails
    for xe in (xL, xR):
        h -= 0.05 * np.exp(-((xx - xe) / (5 * ss)) ** 2) * tail
    t = text_mask(W, H, "BEN SHINDEL", F("roman", 66 * ss), W / 2, cy + 2 * ss, track=1.14)
    h += 0.07 * nd.gaussian_filter(t, ss * .6)
    for off in (-42, 42):
        h += 0.02 * (np.abs(yy - (cy + off * ss)) < 1.5 * ss) * main
    rgba = shade(h, m, "gold", rng, H, crust_amt=0)
    return finish(rgba, ss, OUTD + "name-ribbon.webp")

if __name__ == "__main__":
    for f in (tabula, medallion, wax_tablet, marble_fragment, letter_tiles, ribbon):
        im = f(); print(f.__name__, im.size)
