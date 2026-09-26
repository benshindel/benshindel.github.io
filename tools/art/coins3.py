"""Coin studies, round 3: individually designed coins from different eras, low flat relief with fine
detail, period lettering, no double strikes."""
import math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sketch import smooth_noise, OUT

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"
def F(kind, size):
    if kind == "greek":
        f = ImageFont.truetype(FD + "Cinzel.ttf", size); f.set_variation_by_axes([600]); return f
    if kind == "roman":
        f = ImageFont.truetype(FD + "Cinzel.ttf", size); f.set_variation_by_axes([800]); return f
    if kind == "medieval":
        return ImageFont.truetype(FD + "UncialAntiqua-Regular.ttf", size)
    if kind == "modern":
        return ImageFont.truetype(FD + "IMFeENsc28P.ttf", size)

# ---------------------------------------------------------------- lettering helpers
def text_line(m, x, y, text, f, angle=0.0, track=1.12, fill=255):
    size = f.size
    w = int(sum(f.getlength(ch) * track for ch in text) + size)
    tile = Image.new("L", (w, int(size * 1.7)), 0)
    d = ImageDraw.Draw(tile)
    cx = size / 2
    for ch in text:
        d.text((cx, size * .22), ch, font=f, fill=fill)
        cx += f.getlength(ch) * track
    tile = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
    m.paste(tile, (int(x - tile.width / 2), int(y - tile.height / 2)), tile)

def text_arc(m, cx, cy, radius, text, f, centre_deg, bottom=False, track=1.12, fill=255):
    size = f.size
    widths = [f.getlength(ch) * track for ch in text]
    total = sum(widths)
    sgn = -1 if bottom else 1
    ang = math.radians(centre_deg) - sgn * (total / radius) / 2
    for ch, w in zip(text, widths):
        a = ang + sgn * (w / 2) / radius
        if ch != " ":
            tile = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(tile).text((size - f.getlength(ch) / 2, size * .4), ch, font=f, fill=fill)
            rot = -math.degrees(a + math.pi / 2) if not bottom else -math.degrees(a - math.pi / 2)
            tile = tile.rotate(rot, resample=Image.BICUBIC)
            px, py = cx + radius * math.cos(a), cy + radius * math.sin(a)
            m.paste(tile, (int(px - size), int(py - size)), tile)
        ang += sgn * w / radius

def beads(d, c, R, n, r, fill=255):
    for i in range(n):
        a = i * 2 * math.pi / n
        x, y = c[0] + R * math.cos(a), c[1] + R * math.sin(a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

def ring(d, c, R, w, fill=255):
    d.ellipse([c[0] - R, c[1] - R, c[0] + R, c[1] + R], outline=fill, width=max(1, int(w)))

def hatch_into(e, region, spacing, angle, w, level):
    """Engrave fine parallel lines into a region of the emblem (the intricate, flat look)."""
    S = e.size[0]
    L = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(L)
    a = math.radians(angle)
    for k in np.arange(-S, S, spacing):
        x0, y0 = S / 2 + k * -math.sin(a) - S * math.cos(a), S / 2 + k * math.cos(a) - S * math.sin(a)
        x1, y1 = S / 2 + k * -math.sin(a) + S * math.cos(a), S / 2 + k * math.cos(a) + S * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=255, width=max(1, int(w)))
    la = (np.array(L) > 0) & (np.array(region) > 0)
    ea = np.array(e)
    ea[la] = np.minimum(ea[la], level)
    e.paste(Image.fromarray(ea))

def leaf(d, x, y, L, W, ang, fill=255):
    pts = []
    for t in np.linspace(0, math.pi, 12):
        pts.append((L * (t / math.pi - .5), W * math.sin(t) / 2))
    for t in np.linspace(math.pi, 2 * math.pi, 12):
        pts.append((L * (1.5 - t / math.pi), W * math.sin(t) / 2))
    ca, sa = math.cos(ang), math.sin(ang)
    d.polygon([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], fill=fill)

# ---------------------------------------------------------------- the six coins
def d_forecasting(e, leg, c, R):
    """Greek silver tetradrachm: a paper fortune-teller, olive sprig, legend down the right side."""
    d = ImageDraw.Draw(e); x, y = c[0] - R * .08, c[1] + R * .02; k = R * .6
    petals = [[(x, y), (x - k, y), (x, y - k)], [(x, y), (x, y - k), (x + k, y)],
              [(x, y), (x + k, y), (x, y + k)], [(x, y), (x, y + k), (x - k, y)]]
    for i, p in enumerate(petals):
        d.polygon(p, fill=235 if i % 2 else 255)
    reg = Image.new("L", e.size, 0); rd = ImageDraw.Draw(reg)
    for i, p in enumerate(petals):
        if i % 2:
            rd.polygon(p, fill=255)
    hatch_into(e, reg, R * .045, 45, R * .012, 190)
    for sx, sy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.line([(x, y), (x + sx * k, y + sy * k)], fill=150, width=max(2, int(R * .018)))
    for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        d.line([(x + sx * k * .5, y), (x, y + sy * k * .5)], fill=170, width=max(1, int(R * .012)))
        d.ellipse([x + sx * k * .28 - R * .025, y + sy * k * .28 - R * .025, x + sx * k * .28 + R * .025, y + sy * k * .28 + R * .025], fill=150)
    # olive sprig upper left, crescent lower left
    d.line([(c[0] - R * .78, c[1] - R * .38), (c[0] - R * .52, c[1] - R * .7)], fill=230, width=max(2, int(R * .02)))
    for i in range(5):
        t = i / 4
        px, py = c[0] - R * .78 + t * R * .26, c[1] - R * .38 - t * R * .32
        for s in (-1, 1):
            leaf(d, px + s * R * .05, py + s * R * .02, R * .13, R * .045, -0.9 + s * 0.9, 240)
    d.pieslice([c[0] - R * .8, c[1] + R * .5, c[0] - R * .56, c[1] + R * .74], 0, 360, fill=230)
    d.ellipse([c[0] - R * .76, c[1] + R * .48, c[0] - R * .52, c[1] + R * .68], fill=0)
    text_line(leg, c[0] + R * .66, c[1] + R * .02, "FORECASTING", F("greek", int(R * .17)), angle=-90, track=1.0)

def d_writing(e, leg, c, R):
    """Roman bronze sestertius: typewriter, S·C in the field, legend round the rim."""
    d = ImageDraw.Draw(e); x, y = c[0], c[1] + R * .08; s = R * .52
    d.rectangle([x - s * .42, y - s * 1.0, x + s * .42, y - s * .3], fill=225)                      # paper
    for i in range(5):
        d.line([(x - s * .32, y - s * .9 + i * s * .12), (x + s * (.3 if i < 4 else .05), y - s * .9 + i * s * .12)], fill=150, width=max(1, int(R * .01)))
    d.rounded_rectangle([x - s * .8, y - s * .4, x + s * .8, y - s * .2], radius=s * .1, fill=255)    # platen
    for kx in (-.9, .9):
        d.ellipse([x + s * kx - s * .1, y - s * .4, x + s * kx + s * .1, y - s * .2], fill=240)
    body = [(x - s * .75, y - s * .18), (x + s * .75, y - s * .18), (x + s * 1.0, y + s * .72), (x - s * 1.0, y + s * .72)]
    d.polygon(body, fill=215)
    reg = Image.new("L", e.size, 0); ImageDraw.Draw(reg).polygon(body, fill=255)
    hatch_into(e, reg, R * .035, 0, R * .008, 185)
    for row, (yy, n) in enumerate(((y + s * .02, 9), (y + s * .24, 10), (y + s * .46, 9))):
        for i in range(n):
            xx = x + (i - (n - 1) / 2) * s * .17
            d.ellipse([xx - s * .06, yy - s * .06, xx + s * .06, yy + s * .06], fill=255)
            d.ellipse([xx - s * .025, yy - s * .025, xx + s * .025, yy + s * .025], fill=190)
    d.rectangle([x - s * .5, y + s * .58, x + s * .5, y + s * .66], fill=255)                          # space bar
    f = F("roman", int(R * .19))
    text_line(leg, c[0] - R * .62, c[1] + R * .12, "S", f)
    text_line(leg, c[0] + R * .62, c[1] + R * .12, "C", f)
    text_arc(leg, c[0], c[1], R * .8, "WRITING", F("roman", int(R * .19)), -90, track=1.18)
    text_arc(leg, c[0], c[1], R * .82, "THE · BS · DETECTOR", F("roman", int(R * .105)), 90, bottom=True, track=1.1)

def d_tea(e, leg, c, R):
    """Archaic electrum with an incuse square; a cup with steam."""
    d = ImageDraw.Draw(e); x, y = c[0], c[1] + R * .14; s = R * .42
    d.ellipse([x - s * 1.05, y + s * .5, x + s * 1.05, y + s * .82], fill=210)                           # saucer
    d.chord([x - s * .7, y - s * .62, x + s * .7, y + s * .8], 0, 180, fill=255)
    d.rectangle([x - s * .7, y - s * .12, x + s * .7, y + s * .1], fill=255)
    d.ellipse([x + s * .55, y - s * .08, x + s * 1.0, y + s * .4], outline=240, width=max(3, int(s * .1)))
    d.ellipse([x - s * .68, y - s * .22, x + s * .68, y - s * .02], fill=170)
    # a band of tiny leaves round the cup
    for i in range(7):
        leaf(d, x - s * .5 + i * s * .17, y + s * .28, s * .16, s * .07, 0.5 if i % 2 else -0.5, 200)
    for i, off in enumerate((-.3, .05, .38)):
        pts = [(x + s * off + s * .1 * math.sin(t * 1.2 + i), y - s * .32 - t * s * .12) for t in range(8)]
        d.line(pts, fill=230, width=max(2, int(s * .06)), joint="curve")
    text_line(leg, c[0], c[1] - R * .52, "TEA", F("greek", int(R * .24)), track=1.5)

def d_carbon(e, leg, c, R):
    """Eighteenth-century silver crown: crisp rim, factory in a landscape, legend round the edge, dated."""
    d = ImageDraw.Draw(e); x, y = c[0], c[1] + R * .06; s = R * .56
    d.rectangle([x - s * 1.0, y + s * .5, x + s * 1.0, y + s * .56], fill=255)                          # ground line
    reg = Image.new("L", e.size, 0); rd = ImageDraw.Draw(reg)
    rd.rectangle([x - s * 1.0, y + s * .56, x + s * 1.0, y + s * .9], fill=255)
    d.rectangle([x - s * 1.0, y + s * .56, x + s * 1.0, y + s * .9], fill=200)                          # exergue ground
    hatch_into(e, reg, R * .03, 0, R * .008, 150)
    hall = [(x - s * .9, y + s * .5), (x - s * .9, y + s * .02)]
    for i in range(4):
        x0 = x - s * .9 + i * s * .3
        hall += [(x0 + s * .3, y - s * .22), (x0 + s * .3, y + s * .02)]
    hall += [(x + s * .3, y + s * .5)]
    d.polygon(hall, fill=235)
    reg = Image.new("L", e.size, 0); ImageDraw.Draw(reg).polygon(hall, fill=255)
    hatch_into(e, reg, R * .03, 90, R * .008, 195)
    for i in range(4):
        d.rectangle([x - s * .82 + i * s * .3, y + s * .22, x - s * .7 + i * s * .3, y + s * .38], fill=140)
    for sx, hgt in ((.5, 1.05), (.8, .85)):
        d.rectangle([x + s * sx - s * .08, y - s * hgt, x + s * sx + s * .08, y + s * .5], fill=255)
        for j in range(5):
            d.line([(x + s * sx - s * .08, y - s * hgt + j * s * .28), (x + s * sx + s * .08, y - s * hgt + j * s * .28)], fill=180, width=max(1, int(R * .008)))
    # scrolling smoke drawn as curls
    for j, (px, py, r) in enumerate(((.62, -1.12, .12), (.4, -1.0, .1), (.2, -.92, .085), (.02, -.86, .07))):
        d.ellipse([x + s * px - s * r, y + s * py - s * r, x + s * px + s * r, y + s * py + s * r], outline=235, width=max(2, int(R * .02)))
    text_line(leg, c[0], c[1] + R * .67, "2022", F("modern", int(R * .14)), track=1.2)
    text_arc(leg, c[0], c[1], R * .78, "CARBON · CAPTURE", F("modern", int(R * .17)), -90, track=1.08)

def d_research(e, leg, c, R):
    """Medieval silver penny: voided cross with pellets inside a beaded circle, flask at the centre."""
    d = ImageDraw.Draw(e); x, y = c
    ri = R * .6
    w = R * .06
    for a in (0, 90):
        ar = math.radians(a)
        for s_ in (-1, 1):
            p0 = (x + s_ * R * .22 * math.cos(ar), y + s_ * R * .22 * math.sin(ar))
            p1 = (x + s_ * ri * .98 * math.cos(ar), y + s_ * ri * .98 * math.sin(ar))
            d.line([p0, p1], fill=225, width=int(w))
            d.line([p0, p1], fill=150, width=max(1, int(w * .35)))
    for qa in (45, 135, 225, 315):
        ar = math.radians(qa)
        px, py = x + R * .4 * math.cos(ar), y + R * .4 * math.sin(ar)
        for dx, dy in ((0, 0), (math.cos(ar) * .07, 0), (0, math.sin(ar) * .07)):
            qx, qy = px + R * dx, py + R * dy
            d.ellipse([qx - R * .036, qy - R * .036, qx + R * .036, qy + R * .036], fill=255)
    d.ellipse([x - R * .21, y - R * .21, x + R * .21, y + R * .21], fill=0)
    s = R * .17
    fl = [(x - s * .2, y - s * .95), (x + s * .2, y - s * .95), (x + s * .2, y - s * .3), (x + s * .8, y + s * .8),
          (x - s * .8, y + s * .8), (x - s * .2, y - s * .3)]
    d.polygon(fl, fill=255)
    d.polygon([(x - s * .48, y + s * .22), (x + s * .48, y + s * .22), (x + s * .74, y + s * .75), (x - s * .74, y + s * .75)], fill=185)
    ring(d, c, R * .21, R * .014, 225)
    text_arc(leg, x, y, R * .8, "+RESEARCH+", F("roman", int(R * .19)), -90, track=1.1)
    text_arc(leg, x, y, R * .81, "SORBENTS", F("medieval", int(R * .14)), 90, bottom=True, track=1.1)

def d_community(e, leg, c, R):
    """Broad thin gold piece, Byzantine in feeling: a round table with stools, radiant, legend round."""
    d = ImageDraw.Draw(e); x, y = c; s = R * .42
    for i in range(24):                                                          # radiant rays
        a = i * math.pi / 12
        d.line([(x + s * 1.04 * math.cos(a), y + s * 1.04 * math.sin(a)), (x + s * 1.28 * math.cos(a), y + s * 1.28 * math.sin(a))],
               fill=175, width=max(1, int(R * .01)))
    d.ellipse([x - s * .5, y - s * .5, x + s * .5, y + s * .5], fill=255)
    d.ellipse([x - s * .36, y - s * .36, x + s * .36, y + s * .36], fill=215)
    reg = Image.new("L", e.size, 0); ImageDraw.Draw(reg).ellipse([x - s * .36, y - s * .36, x + s * .36, y + s * .36], fill=255)
    hatch_into(e, reg, R * .03, 30, R * .007, 180)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        px, py = x + s * .82 * math.cos(a), y + s * .82 * math.sin(a)
        d.ellipse([px - s * .15, py - s * .15, px + s * .15, py + s * .15], fill=240)
        d.ellipse([px - s * .06, py - s * .06, px + s * .06, py + s * .06], fill=190)
    for a in (-60, -120):
        ar = math.radians(a)
        px, py = x + R * .57 * math.cos(ar), y + R * .57 * math.sin(ar)
        for j in range(6):
            b = j * math.pi / 3
            d.line([(px, py), (px + R * .05 * math.cos(b), py + R * .05 * math.sin(b))], fill=240, width=max(1, int(R * .014)))
    text_arc(leg, x, y, R * .8, "COMMUNITY", F("greek", int(R * .18)), -90, track=1.2)
    text_arc(leg, x, y, R * .82, "· GATHERINGS ·", F("greek", int(R * .12)), 90, bottom=True, track=1.15)

def d_sun(e, leg, c, R):
    d = ImageDraw.Draw(e); x, y = c
    for i in range(16):
        a = i * math.pi / 8
        r1, r2 = R * .36, R * (.66 if i % 2 == 0 else .54)
        w = R * .07
        d.polygon([(x + r1 * math.cos(a - .12), y + r1 * math.sin(a - .12)), (x + r2 * math.cos(a), y + r2 * math.sin(a)),
                   (x + r1 * math.cos(a + .12), y + r1 * math.sin(a + .12))], fill=235)
    d.ellipse([x - R * .33, y - R * .33, x + R * .33, y + R * .33], fill=255)
    d.ellipse([x - R * .2, y - R * .2, x + R * .2, y + R * .2], fill=215)

def d_moon(e, leg, c, R):
    d = ImageDraw.Draw(e); x, y = c
    d.ellipse([x - R * .55, y - R * .55, x + R * .55, y + R * .55], fill=255)
    d.ellipse([x - R * .3, y - R * .68, x + R * .75, y + R * .42], fill=0)
    for (px, py, r) in ((.42, .3, .1), (.1, .58, .07), (.6, -.1, .06)):
        cx_, cy_ = x + R * px, y + R * py
        for j in range(4):
            a = j * math.pi / 4
            d.line([(cx_ - R * r * math.cos(a), cy_ - R * r * math.sin(a)), (cx_ + R * r * math.cos(a), cy_ + R * r * math.sin(a))], fill=240, width=max(2, int(R * .03)))

COINS = {
    "Day":   dict(draw=d_sun, metal="gold", irregular=.3, offc=0, border="dots", era="toggle"),
    "Night": dict(draw=d_moon, metal="silver", irregular=.3, offc=0, border="dots", era="toggle"),
    "Forecasting":    dict(draw=d_forecasting, metal="silver", irregular=.9, offc=.08, cracks=1, border="dots", era="Greek tetradrachm"),
    "Writing":        dict(draw=d_writing, metal="bronze", irregular=.35, offc=.02, border="dots_line", era="Roman sestertius"),
    "Tea":            dict(draw=d_tea, metal="electrum", irregular=1.3, offc=.05, cracks=2, border="incuse", era="Archaic electrum"),
    "Carbon capture": dict(draw=d_carbon, metal="silver_bright", irregular=0, offc=0, border="crown", era="18th-century crown"),
    "Research":       dict(draw=d_research, metal="billon", irregular=.6, offc=.03, clip=(35, .13), border="double_beads", era="Medieval penny"),
    "Community":      dict(draw=d_community, metal="gold", irregular=.15, offc=.01, border="fine_dots", era="Byzantine-style gold"),
}

METALS = {
    "silver":        dict(base=(178, 178, 174), shadow=(52, 50, 48), spec=(255, 252, 245), tones=[(92, 110, 150), (190, 150, 84)], patina=0.0, crust=(120, 104, 86), tone_k=.5),
    "silver_bright": dict(base=(196, 198, 200), shadow=(60, 62, 66), spec=(255, 255, 255), tones=[(150, 140, 120)], patina=0.0, crust=(130, 120, 100), tone_k=.25),
    "bronze":        dict(base=(146, 100, 64), shadow=(44, 30, 20), spec=(255, 214, 170), tones=[(58, 96, 78), (86, 120, 92)], patina=0.7, crust=(118, 100, 74), tone_k=.45),
    "electrum":      dict(base=(214, 188, 124), shadow=(80, 60, 26), spec=(255, 244, 210), tones=[(176, 132, 70)], patina=0.0, crust=(140, 110, 70), tone_k=.4),
    "billon":        dict(base=(150, 144, 136), shadow=(44, 40, 36), spec=(240, 232, 220), tones=[(96, 88, 74), (70, 84, 80)], patina=0.15, crust=(110, 96, 80), tone_k=.45),
    "gold":          dict(base=(222, 176, 72), shadow=(90, 62, 16), spec=(255, 246, 204), tones=[(200, 140, 60)], patina=0.0, crust=(150, 110, 60), tone_k=.2),
}

def coin(R, name, seed=0, ss=2, light=(-0.55, -0.65, 0.6)):
    spec = COINS[name]
    rng = np.random.default_rng(seed)
    Rs = R * ss
    S = int(Rs * 2.2)
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    th = np.arctan2(yy - c, xx - c)
    dist = np.hypot(xx - c, yy - c)
    ir = spec["irregular"]
    ph = rng.uniform(0, 6.3, 4)
    redge = Rs * (1 + ir * (0.03 * np.cos(2 * (th - ph[3])) + 0.018 * np.sin(3 * th + ph[0]) + 0.01 * np.sin(5 * th + ph[1])))
    for _ in range(spec.get("cracks", 0)):
        ca = rng.uniform(0, 2 * math.pi)
        wedge = np.exp(-((np.angle(np.exp(1j * (th - ca)))) / 0.03) ** 2)
        redge = redge - Rs * rng.uniform(.10, .18) * wedge
    flan = np.clip((redge - dist) / (Rs * (0.035 if ir == 0 else 0.05)), 0, 1)
    if spec.get("clip"):
        ang, depth = spec["clip"]
        proj = (xx - c) * math.cos(math.radians(ang)) + (yy - c) * math.sin(math.radians(ang))
        flan = np.minimum(flan, np.clip((Rs * (1 - depth) - proj) / (Rs * .04), 0, 1))
    flan = flan * flan * (3 - 2 * flan)
    h = 0.20 * flan
    off = rng.normal(0, Rs * spec["offc"], 2) if spec["offc"] else np.zeros(2)
    dc = (c + off[0], c + off[1])
    e = Image.new("L", (S, S), 0); leg = Image.new("L", (S, S), 0); brd = Image.new("L", (S, S), 0)
    bd = ImageDraw.Draw(brd)
    b = spec["border"]
    Rd = Rs * 0.98
    if b == "dots":
        beads(bd, dc, Rd * .93, 60, Rd * .022)
    elif b == "dots_line":
        beads(bd, dc, Rd * .95, 72, Rd * .016); ring(bd, dc, Rd * .9, Rd * .012, 200)
    elif b == "fine_dots":
        beads(bd, dc, Rd * .95, 110, Rd * .01); ring(bd, dc, Rd * .915, Rd * .006, 200)
    elif b == "double_beads":
        beads(bd, dc, Rd * .95, 80, Rd * .014); beads(bd, dc, Rd * .62, 50, Rd * .012)
    elif b == "crown":
        # raised flat rim with a fine beaded circle inside it
        ring(bd, dc, Rd * .955, Rd * .07, 255); beads(bd, dc, Rd * .86, 96, Rd * .011)
    Rdesign = Rd * (0.78 if b == "incuse" else 0.95)
    spec["draw"](e, leg, dc, Rdesign)
    earr = np.array(e) / 255.0
    inside = earr > 0.02
    # low, flat relief: mostly plateaus with softly rounded edges
    dt = nd.distance_transform_edt(inside) / (Rs * .035)
    edge = np.clip(dt, 0, 1) ** 0.7
    emb = nd.gaussian_filter(edge * (0.45 + 0.55 * earr), Rs * .004)
    legh = np.array(leg.filter(ImageFilter.GaussianBlur(Rs * .004))) / 255
    brdh = np.array(brd.filter(ImageFilter.GaussianBlur(Rs * .005))) / 255
    relief = 0.30 * emb + 0.24 * legh + 0.18 * brdh
    if b == "crown":
        # milled edge: fine radial reeding on the outermost rim
        reed = (0.5 + 0.5 * np.cos(th * 220)) * np.clip((dist - Rs * .955) / (Rs * .02), 0, 1) * flan
        relief += 0.05 * reed
    if b == "incuse":
        half = Rs * .64
        q = np.maximum(np.abs(xx - dc[0]), np.abs(yy - dc[1]))
        sq = np.clip((half - q) / (Rs * .035), 0, 1)
        h -= 0.14 * sq
        relief = relief * sq
    h += relief * flan
    # gentle wear and surface
    h -= 0.05 * np.clip(h - 0.36, 0, None) * (1 + smooth_noise(S, S, Rs * .4, rng))
    h += 0.0018 * smooth_noise(S, S, Rs * .12, rng) + 0.0003 * rng.standard_normal((S, S))
    cav = np.clip(nd.gaussian_filter(h, Rs * .03) - h, 0, None)
    crust_amt = 0.0 if spec["metal"] in ("gold", "silver_bright") else 1.0
    crust = np.clip((smooth_noise(S, S, Rs * .15, rng) * 0.8 + cav * 14 - 0.55) * 2.0, 0, 1) * flan * crust_amt
    h += 0.02 * crust
    # lighting
    gy, gx = np.gradient(h * Rs * 1.35)
    nrm = np.dstack([-gx, -gy, np.ones_like(h)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    Lv = np.array(light, float); Lv /= np.linalg.norm(Lv)
    lam = np.clip((nrm * Lv).sum(2), 0, 1)
    Hv = Lv + np.array([0, 0, 1.0]); Hv /= np.linalg.norm(Hv)
    specl = np.clip((nrm * Hv).sum(2), 0, 1) ** 30
    cav = np.clip(nd.gaussian_filter(h, Rs * .02) - h, 0, None)
    ao = np.clip(1 - cav * 9, 0.4, 1)
    M = METALS[spec["metal"]]
    base, shad, spc, crc = (np.array(M[k], float) / 255 for k in ("base", "shadow", "spec", "crust"))
    col = np.broadcast_to(base, (S, S, 3)).copy()
    for t in M["tones"]:
        w = np.clip(smooth_noise(S, S, Rs * rng.uniform(.35, .7), rng) * 1.2 - 0.15, 0, 1)[..., None]
        rim = np.clip((dist / Rs) - 0.4, 0, 1)[..., None]
        k = M["tone_k"] * w * (0.5 + 0.5 * rim)
        col = col * (1 - k) + np.array(t) / 255 * k
    if M["patina"]:
        pat = np.clip(cav * 22 + 0.4 * smooth_noise(S, S, Rs * .25, rng), 0, 1)[..., None] * M["patina"]
        col = col * (1 - pat) + np.array(M["tones"][0]) / 255 * pat
    cm = (crust * 0.8)[..., None]
    col = col * (1 - cm) + crc * cm
    shine = specl * (1 - crust) * (1 - 0.6 * M["patina"])
    rgb = shad + (col - shad) * (0.28 + 0.9 * lam[..., None]) * ao[..., None] + spc * shine[..., None] * 0.6
    out = np.dstack([np.clip(rgb, 0, 1), flan])
    im = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
    return im.resize((S // ss, S // ss), Image.LANCZOS)

# ---------------------------------------------------------------- backings
def baize_dark(W, H, seed=10):
    rng = np.random.default_rng(seed)
    fuzz = nd.gaussian_filter(rng.standard_normal((H, W)), 1.0); fuzz /= np.abs(fuzz).max()
    nap = nd.gaussian_filter(rng.standard_normal((H, W)), (0.6, 2.2)); nap /= np.abs(nap).max()
    lum = 0.17 + 0.035 * fuzz + 0.02 * nap + 0.035 * smooth_noise(H, W, 420, rng) + 0.015 * smooth_noise(H, W, 60, rng)
    rgb = lum[..., None] * np.array([0.50, 1.0, 0.62])
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def sand(W, H, seed=8, pebbles=True):
    rng = np.random.default_rng(seed)
    lum = 0.74 + 0.07 * rng.standard_normal((H, W)) + 0.05 * smooth_noise(H, W, 140, rng) + 0.03 * smooth_noise(H, W, 500, rng)
    lum = nd.gaussian_filter(lum, 0.6)
    # faint ripples left by a trowel
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    lum += 0.015 * np.sin((yy * .9 + xx * .25 + smooth_noise(H, W, 300, rng) * 40) / 9)
    im = Image.fromarray((np.clip(lum[..., None] * np.array([1.0, 0.89, 0.70]), 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    if pebbles:
        d = ImageDraw.Draw(im, "RGBA")
        for _ in range(int(W * H / 5200)):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            r = rng.uniform(1.5, 4.5)
            t = int(rng.uniform(150, 215))
            d.ellipse([x + .8, y + 1.2, x + r * 2 + .8, y + r * 1.6 + 1.2], fill=(110, 90, 64, 45))
            d.ellipse([x, y, x + r * 2, y + r * 1.6], fill=(t, int(t * .9), int(t * .76), 255))
    return im

def place(bg, ci, cx, cy, shadow=0.6, blur=7, dx=6, dy=9):
    a = ci.split()[3]
    sh = Image.new("RGBA", ci.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * shadow)))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    w, h = ci.size
    bg.alpha_composite(sh, (int(cx - w / 2 + dx), int(cy - h / 2 + dy)))
    bg.alpha_composite(ci, (int(cx - w / 2), int(cy - h / 2)))

if __name__ == "__main__":
    names = list(COINS)
    for mode, bgf in (("night", baize_dark), ("day", sand)):
        W, H = 1500, 560
        bg = bgf(W, H)
        for i, n in enumerate(names):
            ci = coin(110, n, seed=i + 3)
            place(bg, ci, 135 + i * 246, 280 + (-26 if i % 2 else 26), 0.75 if mode == "night" else 0.5, 9, 6, 10)
        bg.convert("RGB").save(f"{OUT}/c3_{mode}.jpg", quality=90)
        print(mode)
