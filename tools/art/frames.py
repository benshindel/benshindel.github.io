"""Picture frames as 9-slice border images (bronze moulding, Greek key, tabula) + paper mat tile."""
import math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sketch import smooth_noise
import relics2  # registers extra materials
from relics import shade
OUT = os.environ.get("ART_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")) + "/"

def save(rgba, path, ss=1):
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA")
    if ss > 1:
        im = im.resize((im.width // ss, im.height // ss), Image.LANCZOS)
    im.save(path, quality=90, method=6)
    return im

# ---------------------------------------------------------------- bronze moulding (slice = B px)
def moulding(S=400, B=64, seed=1, name="frame-bronze.webp", rosettes=True, metal="statuary", highlight=True):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    # distance inward from the outer edge (0 at edge, B at inner edge)
    din = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    m = (din < B).astype(float) * np.clip(din / 1.5, 0, 1)
    t = np.clip(din / B, 0, 1)
    # profile: outer bead, a cove, a raised fillet, then a small inner lip
    prof = (0.55 * np.exp(-((t - .16) / .12) ** 2) + 0.25 * np.clip(1 - np.abs(t - .45) / .18, 0, 1) * 0 +
            -0.15 * np.exp(-((t - .42) / .1) ** 2) + 0.45 * np.exp(-((t - .66) / .07) ** 2) + 0.3 * np.exp(-((t - .9) / .05) ** 2))
    h = 0.15 * m + 0.14 * prof * m
    if rosettes:
        for cx, cy in ((B * .52, B * .52), (S - B * .52, B * .52), (B * .52, S - B * .52), (S - B * .52, S - B * .52)):
            r = np.hypot(xx - cx, yy - cy); a = np.arctan2(yy - cy, xx - cx)
            petal = np.clip(1 - r / (B * .42 * (0.75 + 0.25 * np.cos(8 * a))), 0, 1)
            h = np.where(r < B * .44, 0.15 + 0.12 * petal ** .6 + 0.05 * (r < B * .1), h)
    h += 0.004 * smooth_noise(S, S, 30, rng)
    rgba = shade(h, m, metal, rng, 160, crust_amt=.4, grad=1.2)
    if highlight:
        hi = np.clip(prof, 0, 1)[..., None] * .35
        rgba[..., :3] = rgba[..., :3] * (1 - hi) + np.array([0.82, 0.66, 0.40]) * hi
    return save(rgba, OUT + name)

# ---------------------------------------------------------------- Greek key (meander) border
def meander_unit(U, lw):
    """One meander repeat drawn in a U×U cell (horizontal band)."""
    im = Image.new("L", (U, U), 0); d = ImageDraw.Draw(im)
    g = U / 10
    pts = [(0, 8), (9, 8), (9, 1), (3, 1), (3, 5), (6, 5), (6, 3.5)]
    d.line([(x * g, y * g) for x, y in pts], fill=255, width=int(lw), joint="curve")
    d.line([(0, 9.3 * g), (U, 9.3 * g)], fill=255, width=int(lw * .6))
    d.line([(0, .2 * g), (U, .2 * g)], fill=255, width=int(lw * .6))
    return np.array(im) / 255.0

def greek_key(U=72, seed=2, name="frame-greek.webp"):
    rng = np.random.default_rng(seed)
    S = U * 3
    lw = U * .09
    unit = meander_unit(U, lw)
    pat = np.zeros((S, S))
    pat[0:U, U:2 * U] = unit                          # top
    pat[2 * U:S, U:2 * U] = np.flipud(unit)           # bottom
    pat[U:2 * U, 0:U] = np.rot90(unit, 1)             # left
    pat[U:2 * U, 2 * U:S] = np.rot90(unit, -1)        # right
    # corners: a square rosette
    cr = Image.new("L", (U, U), 0); cd = ImageDraw.Draw(cr)
    cd.rectangle([U * .1, U * .1, U * .9, U * .9], outline=255, width=int(lw * .7))
    for k in range(8):
        a = k * math.pi / 4
        cd.ellipse([U / 2 + U * .22 * math.cos(a) - U * .09, U / 2 + U * .22 * math.sin(a) - U * .09,
                    U / 2 + U * .22 * math.cos(a) + U * .09, U / 2 + U * .22 * math.sin(a) + U * .09], fill=255)
    c = np.array(cr) / 255.0
    for (y, x) in ((0, 0), (0, 2 * U), (2 * U, 0), (2 * U, 2 * U)):
        pat[y:y + U, x:x + U] = c
    pat = nd.gaussian_filter(pat, .8)
    m = np.ones((S, S)); m[U:2 * U, U:2 * U] = 0
    h = 0.12 * m + 0.10 * pat * m
    # dark ground (bronze gone nearly black) with bright inlaid key
    ground = shade(h, m, "statuary", rng, 120, crust_amt=.2)
    key = shade(h, m, "gold", rng, 120, crust_amt=0)
    k = pat[..., None]
    rgb = ground[..., :3] * 0.55 * (1 - k) + key[..., :3] * k
    return save(np.dstack([rgb, m]), OUT + name)

# ---------------------------------------------------------------- tabula frame: a flat bronze plaque edge + dovetail handles
def tabula_frame(S=360, B=70, seed=3):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    din = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    m = (din < B).astype(float) * np.clip(din / 1.5, 0, 1)
    t = din / B
    h = 0.2 * m + 0.05 * (np.abs(t - .18) < .06) + 0.04 * (np.abs(t - .38) < .05) - 0.03 * (t > .8)
    h = nd.gaussian_filter(h, 1.0) * m
    rgba = shade(h, m, "statuary", rng, 160, crust_amt=.5)
    hi = ((np.abs(t - .18) < .06) | (np.abs(t - .38) < .05))[..., None] * .4
    rgba[..., :3] = rgba[..., :3] * (1 - hi) + np.array([0.82, 0.66, 0.40]) * hi
    save(rgba, OUT + "frame-tabula.webp")
    # handle (left one; right is mirrored in CSS)
    Wd, Hd = 150, 260
    hm = Image.new("L", (Wd, Hd), 0)
    ImageDraw.Draw(hm).polygon([(Wd, Hd * .22), (8, 4), (8, Hd - 4), (Wd, Hd * .78)], fill=255)
    hmask = np.array(hm.filter(ImageFilter.GaussianBlur(1))) / 255
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(float)
    r = np.hypot(xx - Wd * .42, yy - Hd / 2)
    hmask = hmask * np.clip((r - 11) / 1.5, 0, 1)
    hh = 0.2 * hmask + 0.03 * np.clip(1 - np.abs(r - 16) / 4, 0, 1) + 0.004 * smooth_noise(Hd, Wd, 30, rng)
    save(shade(hh, hmask, "statuary", rng, 160, crust_amt=.5), OUT + "frame-tabula-handle.webp")

# ---------------------------------------------------------------- mat board paper (tileable)
def mat_paper(T=256, seed=4):
    rng = np.random.default_rng(seed)
    n = nd.gaussian_filter(rng.standard_normal((T, T)), 0.8, mode="wrap"); n /= np.abs(n).max()
    n2 = nd.gaussian_filter(rng.standard_normal((T, T)), 12, mode="wrap"); n2 /= np.abs(n2).max()
    lum = 0.93 + 0.012 * n + 0.012 * n2
    rgb = lum[..., None] * np.array([1.0, 0.985, 0.95])
    Image.fromarray((rgb * 255).astype(np.uint8)).save(OUT + "mat.jpg", quality=86)

if __name__ == "__main__":
    moulding(); greek_key(); tabula_frame(); mat_paper()
    moulding(S=300, B=26, name="frame-vitrine.webp", rosettes=False, metal="statuary")
    print("ok")

# ---------------------------------------------------------------- corner motifs for the bronze moulding
def _dome(mask, w):
    dt = nd.distance_transform_edt(mask > .5) / w
    return np.clip(dt, 0, 1) ** .6

def corner_motif(kind, B, rng):
    """Height map (B×B) for the top-left corner block; flipped for the others."""
    ss = 4
    Z = B * ss
    im = Image.new("L", (Z, Z), 0); d = ImageDraw.Draw(im)
    c = Z * .52
    h = np.zeros((Z, Z))
    if kind == "palmette":
        # an anthemion: a fan of leaves opening toward the outer corner, on a pair of volutes
        base = (c + Z * .2, c + Z * .2)
        for k in range(9):
            a = math.radians(225 + (k - 4) * 13)
            L = Z * (.55 if k % 2 == 0 else .46)
            tip = (base[0] + L * math.cos(a), base[1] + L * math.sin(a))
            mid = (base[0] + L * .55 * math.cos(a), base[1] + L * .55 * math.sin(a))
            d.line([base, mid, tip], fill=255, width=int(Z * .05))
            d.ellipse([tip[0] - Z * .05, tip[1] - Z * .05, tip[0] + Z * .05, tip[1] + Z * .05], fill=255)
        for s_ in (-1, 1):
            vx, vy = base[0] + s_ * Z * .12 + Z * .02, base[1] - s_ * Z * .12 + Z * .02
            d.ellipse([vx - Z * .075, vy - Z * .075, vx + Z * .075, vy + Z * .075], outline=255, width=int(Z * .035))
        d.ellipse([base[0] - Z * .06, base[1] - Z * .06, base[0] + Z * .06, base[1] + Z * .06], fill=255)
        m = np.array(im) / 255
        h = 0.12 * _dome(m, Z * .025)
    elif kind == "coin":
        r = Z * .34
        d.ellipse([c - r, c - r, c + r, c + r], fill=255)
        m = np.array(im) / 255
        yy, xx = np.mgrid[0:Z, 0:Z]
        rr = np.hypot(xx - c, yy - c)
        h = 0.08 * m + 0.05 * (np.abs(rr - r * .82) < Z * .02)
        star = Image.new("L", (Z, Z), 0)
        pts = [(c + (r * .55 if i % 2 == 0 else r * .2) * math.cos(i * math.pi / 8), c + (r * .55 if i % 2 == 0 else r * .2) * math.sin(i * math.pi / 8)) for i in range(16)]
        ImageDraw.Draw(star).polygon(pts, fill=255)
        h += 0.06 * _dome(np.array(star) / 255, Z * .02)
        for i in range(28):
            a = i * 2 * math.pi / 28
            bx, by = c + r * .92 * math.cos(a), c + r * .92 * math.sin(a)
            h += 0.04 * (np.hypot(xx - bx, yy - by) < Z * .018)
    elif kind == "rivets":
        # a plain mitred corner held with three nails
        yy, xx = np.mgrid[0:Z, 0:Z]
        h = -0.05 * (np.abs(xx - yy) < Z * .012)
        for t in (.2, .5, .8):
            px = py = Z * t
            rr = np.hypot(xx - px - Z * .06, yy - py + Z * .06)
            h += 0.08 * np.clip(1 - (rr / (Z * .06)) ** 2, 0, 1) ** .5
        m = np.zeros((Z, Z))
        return nd.zoom(h, 1 / ss, order=1), None
    elif kind == "shell":
        # a scallop shell, ribs fanning toward the outer corner
        hinge = (c + Z * .22, c + Z * .22)
        R = Z * .56
        d.pieslice([hinge[0] - R, hinge[1] - R, hinge[0] + R, hinge[1] + R], 225 - 50, 225 + 50, fill=150)
        rib = Image.new("L", (Z, Z), 0); rd = ImageDraw.Draw(rib)
        for k in range(11):
            a = math.radians(225 + (k - 5) * 9.5)
            rd.line([hinge, (hinge[0] + R * math.cos(a), hinge[1] + R * math.sin(a))], fill=255, width=int(Z * .045))
        ribs = np.array(rib) / 255
        # scalloped rim
        for k in range(11):
            a = math.radians(225 + (k - 5) * 9.5)
            px, py = hinge[0] + R * math.cos(a), hinge[1] + R * math.sin(a)
            d.ellipse([px - Z * .05, py - Z * .05, px + Z * .05, py + Z * .05], fill=150)
        d.polygon([(hinge[0] - Z * .14, hinge[1] + Z * .02), (hinge[0] + Z * .02, hinge[1] - Z * .14), (hinge[0] + Z * .08, hinge[1] + Z * .08)], fill=200)
        m = np.array(im) / 255
        h = 0.08 * _dome(m > .3, Z * .05) + 0.04 * ribs * (m > .3)
    elif kind == "volute":
        # an Ionic scroll: a spiral rolling toward the outer corner
        pts = []
        for i in range(260):
            t = i / 259 * 3.2 * math.pi
            r = Z * .36 * (1 - t / (3.6 * math.pi))
            a = t + math.radians(45)
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.line(pts, fill=255, width=int(Z * .06), joint="curve")
        d.ellipse([c - Z * .06, c - Z * .06, c + Z * .06, c + Z * .06], fill=255)
        m = np.array(im) / 255
        h = 0.10 * _dome(m, Z * .03)
    else:   # rosette
        yy, xx = np.mgrid[0:Z, 0:Z]
        r = np.hypot(xx - c, yy - c); a = np.arctan2(yy - c, xx - c)
        petal = np.clip(1 - r / (Z * .42 * (0.75 + 0.25 * np.cos(8 * a))), 0, 1)
        h = 0.12 * petal ** .6 + 0.05 * (r < Z * .1)
    h = nd.gaussian_filter(h, ss * .6)
    return nd.zoom(h, 1 / ss, order=1), True

def moulding_corners(kind, S=400, B=72, seed=1):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    din = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    m = (din < B).astype(float) * np.clip(din / 1.5, 0, 1)
    t = np.clip(din / B, 0, 1)
    prof = (0.55 * np.exp(-((t - .16) / .12) ** 2) - 0.15 * np.exp(-((t - .42) / .1) ** 2) +
            0.45 * np.exp(-((t - .66) / .07) ** 2) + 0.3 * np.exp(-((t - .9) / .05) ** 2))
    h = 0.15 * m + 0.14 * prof * m
    motif, block = corner_motif(kind, B, rng)
    Bm = motif.shape[0]
    blk = np.zeros((S, S), bool)
    for fy in (False, True):
        for fx in (False, True):
            mm = motif[::-1] if fy else motif
            mm = mm[:, ::-1] if fx else mm
            ys = slice(S - Bm, S) if fy else slice(0, Bm)
            xs = slice(S - Bm, S) if fx else slice(0, Bm)
            if block:
                # a flat corner block with a small bevel, the motif raised on it
                bev = np.clip(np.minimum.outer(np.minimum(np.arange(Bm), np.arange(Bm)[::-1]), np.minimum(np.arange(Bm), np.arange(Bm)[::-1])) / 3, 0, 1)
                h[ys, xs] = 0.17 + 0.03 * bev + mm
                blk[ys, xs] = True
            else:
                h[ys, xs] += mm
    h += 0.004 * smooth_noise(S, S, 30, rng)
    rgba = shade(h, m, "statuary", rng, 160, crust_amt=.4, grad=1.2)
    hi = (np.clip(prof, 0, 1) * (~blk))[..., None] * .35
    rgba[..., :3] = rgba[..., :3] * (1 - hi) + np.array([0.82, 0.66, 0.40]) * hi
    # rub the raised motif bright
    mot = np.zeros((S, S))
    for fy in (False, True):
        for fx in (False, True):
            mm = motif[::-1] if fy else motif
            mm = mm[:, ::-1] if fx else mm
            mot[slice(S - Bm, S) if fy else slice(0, Bm), slice(S - Bm, S) if fx else slice(0, Bm)] = np.clip(mm * 9, 0, 1)
    k = mot[..., None] * .45
    rgba[..., :3] = rgba[..., :3] * (1 - k) + np.array([0.84, 0.68, 0.42]) * k
    return save(rgba, OUT + f"frame-bronze-{kind}.webp")
