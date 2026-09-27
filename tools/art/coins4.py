"""Coins, round 4: sculpted relief and real metal.

Each coin is modelled as a height field (rounded, layered relief rather than flat plateaus), then
given materials: base colour with toning, grime in the recesses and polished high points, a
roughness map, and a visible edge wall (the page is seen from a little in front, so each coin
shows a sliver of its thickness along the bottom). Shading is image-based: the surface reflects a
simple room (ceiling, walls, the cloth) plus one soft key light, which is what makes metal read as
metal rather than as painted plaster.

Outputs, per coin:
  coin-<slug>.webp      the coin lit by daylight (what the page shows first, and without WebGL)
  coin-<slug>-mat.webp  a material sheet for live relighting in coins.js:
                        left half RGB = base colour, A = coverage; right half RG = normal xy, B = roughness
The shader in assets/js/coins.js is a line-for-line port of shade() below.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from coins3 import F, text_arc, text_line
from sketch import smooth_noise

OUT_S = 340          # output image size (square)
R_OUT = 154          # coin radius in the output image
WALL = 0.034
RELIEF = 1.5         # overall relief exaggeration         # visible edge thickness, in coin radii

# ---------------------------------------------------------------- helpers
def sstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)

class Relief:
    """Accumulates a height field (in pixels) from drawn layers with rounded, sculpted profiles."""
    def __init__(self, S, ss, W=None):
        self.S, self.W, self.ss = S, W or S, ss
        self.h = np.zeros((S, self.W))
        self.design = np.zeros((S, self.W))     # where there is raised design (for materials)

    def layer(self):
        im = Image.new("L", (self.W, self.S), 0)
        return im, ImageDraw.Draw(im)

    def profile(self, im, edge, dome=0.0, dome_w=None):
        m = np.asarray(im, float) / 255
        dt = nd.distance_transform_edt(m > 0.5) + (m - 0.5).clip(0, None) * (m <= 0.5)
        x = np.clip(dt / max(edge, 1e-6), 0, 1)
        prof = 1 - (1 - x) ** 2                              # bull-nose shoulder
        if dome:
            y = np.clip(dt / dome_w, 0, 1)
            prof = (1 - dome) * prof + dome * (1 - (1 - y) ** 2.2)
        return nd.gaussian_filter(prof, 0.45 * self.ss), m

    def add(self, im, height, edge, dome=0.0, dome_w=None):
        p, m = self.profile(im, edge, dome, dome_w)
        self.h += RELIEF * height * p
        self.design = np.maximum(self.design, np.clip(p * 1.5, 0, 1))

    def cut(self, im, depth, edge):
        p, m = self.profile(im, edge)
        self.h -= RELIEF * depth * p

# ---------------------------------------------------------------- the designs
# Every design gets (rel, c, R): the relief, the centre of the die and the die radius (ss px).
# Heights are in fractions of R.

# Legends are cut bolder than a die-sinker would, since they are read at a few hundred pixels: Cinzel
# at its heaviest, the thin faces thickened, the letters a little taller and more crisply edged.
def LF(kind, size):
    size = int(size * 1.08)
    if kind in ("greek", "roman"):
        from PIL import ImageFont
        f = ImageFont.truetype(os.path.join(HERE, "fonts", "Cinzel.ttf"), size); f.set_variation_by_axes([900]); return f
    return F(kind, size)

def _bold(im, kind, R):
    from PIL import ImageFilter
    k = 5 if kind in ("medieval", "modern") else 3
    return im.filter(ImageFilter.MaxFilter(k))

def legend_arc(rel, c, R, text, kind, size, centre_deg, bottom=False, track=1.12, r=.8, height=.03):
    im, _ = rel.layer()
    text_arc(im, c[0], c[1], R * r, text, LF(kind, R * size), centre_deg, bottom=bottom, track=track)
    rel.add(_bold(im, kind, R), R * height, R * .007, dome=.25, dome_w=R * .018)
    rel.legend = np.maximum(getattr(rel, "legend", 0), np.asarray(im, float) / 255)

def legend_line(rel, x, y, R, text, kind, size, angle=0, track=1.12, height=.03):
    im, _ = rel.layer()
    text_line(im, x, y, text, LF(kind, R * size), angle=angle, track=track)
    rel.add(_bold(im, kind, R), R * height, R * .007, dome=.25, dome_w=R * .018)

def beads(rel, c, Rr, n, r, height, R):
    im, d = rel.layer()
    for i in range(n):
        a = i * 2 * math.pi / n
        x, y = c[0] + Rr * math.cos(a), c[1] + Rr * math.sin(a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    rel.add(im, height, r * .5, dome=.8, dome_w=r)

def ring(rel, c, Rr, w, height, R):
    im, d = rel.layer()
    d.ellipse([c[0] - Rr, c[1] - Rr, c[0] + Rr, c[1] + Rr], outline=255, width=max(1, int(w)))
    rel.add(im, height, w * .45, dome=.6, dome_w=w * .5)

def d_forecasting(rel, c, R):
    """Greek tetradrachm: a paper fortune-teller seen from above (four folded peaks), an augur's
    lituus and a crescent, the legend running clockwise down the right-hand side."""
    x, y = c[0] - R * .04, c[1] + R * .02
    k = R * .5
    S = rel.S
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    u, v = (xx - x) / k, (yy - y) / k
    inside = (np.abs(u) + np.abs(v)) < 1
    # four peaks, one per quadrant of the diamond; each is a little square pyramid (L-inf distance)
    h = np.zeros((S, S))
    for sx, sy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pu, pv = u - sx * .5, v - sy * .5
        # rotate 45 degrees so the pyramid's base matches the diamond's quadrant
        a, b = (pu + pv) / math.sqrt(2), (pu - pv) / math.sqrt(2)
        pyr = np.clip(1 - np.maximum(np.abs(a), np.abs(b)) / (.5 / math.sqrt(2)), 0, 1)
        h = np.maximum(h, pyr)
    h = h * inside
    # soften the outer edge of the diamond and the folds a touch
    edge = sstep((1 - (np.abs(u) + np.abs(v))) / .05)
    h = nd.gaussian_filter(h * edge, 0.8 * rel.ss)
    rel.h += R * .07 * h + R * .02 * edge * inside
    rel.design = np.maximum(rel.design, inside * 1.0)
    # the paper's printed divisions: fine incised lines on the facets
    im, d = rel.layer()
    for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        d.line([(x + sx * k * .5, y), (x, y + sy * k * .5)], fill=255, width=max(1, int(R * .008)))
    d.line([(x - k, y), (x + k, y)], fill=255, width=max(1, int(R * .01)))
    d.line([(x, y - k), (x, y + k)], fill=255, width=max(1, int(R * .01)))
    rel.cut(im, R * .012, R * .006)
    # lituus: a staff ending in a spiral crook, upper left
    im, d = rel.layer()
    w = max(2, int(R * .04))
    cx_, cy_ = c[0] - R * .52, c[1] - R * .48
    r0 = R * .12
    d.line([(c[0] - R * .74, c[1] + R * .36), (cx_ - r0, cy_)], fill=255, width=w)
    spiral = []
    for i in range(160):
        t = i / 159 * 2.3 * math.pi
        r = r0 * (1 - t / (2.7 * math.pi))
        a_ = math.pi + t
        spiral.append((cx_ + r * math.cos(a_), cy_ + r * math.sin(a_)))
    d.line(spiral, fill=255, width=w, joint="curve")
    for p in (spiral[-1], (c[0] - R * .74, c[1] + R * .36)):
        d.ellipse([p[0] - w * .55, p[1] - w * .55, p[0] + w * .55, p[1] + w * .55], fill=255)
    rel.add(im, R * .03, w * .5, dome=.7, dome_w=w * .55)
    # crescent, lower left
    im, d = rel.layer()
    d.ellipse([c[0] - R * .64, c[1] + R * .46, c[0] - R * .40, c[1] + R * .70], fill=255)
    d.ellipse([c[0] - R * .60, c[1] + R * .42, c[0] - R * .37, c[1] + R * .63], fill=0)
    rel.add(im, R * .03, R * .02, dome=.6, dome_w=R * .035)
    legend_arc(rel, c, R, "FORECASTING", "greek", .15, 2, track=1.02, r=.79)
    beads(rel, c, R * .93, 64, R * .02, R * .022, R)

def d_writing(rel, c, R):
    """Roman sestertius: a typewriter with its fan of typebars, S C in the field, legend round."""
    x, y = c[0], c[1] + R * .1
    s = R * .5
    # sheet of paper rising from the platen, with lines of type
    im, d = rel.layer()
    d.polygon([(x - s * .44, y - s * .98), (x + s * .44, y - s * 1.02), (x + s * .46, y - s * .34), (x - s * .44, y - s * .34)], fill=255)
    rel.add(im, R * .018, R * .01, dome=.3, dome_w=R * .08)
    im, d = rel.layer()
    for i in range(5):
        yl = y - s * .88 + i * s * .11
        d.line([(x - s * .32, yl), (x + s * (.3 if i < 4 else 0), yl - s * .01)], fill=255, width=max(1, int(R * .012)))
    rel.cut(im, R * .006, R * .004)
    # platen roller with knobs
    im, d = rel.layer()
    d.rounded_rectangle([x - s * .82, y - s * .42, x + s * .82, y - s * .22], radius=s * .1, fill=255)
    rel.add(im, R * .03, R * .03, dome=.9, dome_w=s * .1)
    im, d = rel.layer()
    for kx in (-.94, .94):
        d.ellipse([x + s * kx - s * .11, y - s * .43, x + s * kx + s * .11, y - s * .21], fill=255)
    rel.add(im, R * .036, R * .02, dome=.9, dome_w=s * .11)
    # body: a trapezoid that swells toward the keys
    im, d = rel.layer()
    body = [(x - s * .76, y - s * .18), (x + s * .76, y - s * .18), (x + s * 1.0, y + s * .76), (x - s * 1.0, y + s * .76)]
    d.polygon(body, fill=255)
    rel.add(im, R * .03, R * .012, dome=.6, dome_w=R * .12)
    # the fan of typebars, incised
    im, d = rel.layer()
    for i in range(15):
        a = math.radians(-160 + i * 10)
        d.line([(x + s * .12 * math.cos(a), y - s * .02 + s * .12 * math.sin(a)),
                (x + s * .42 * math.cos(a), y - s * .02 + s * .42 * math.sin(a))], fill=255, width=max(1, int(R * .01)))
    rel.cut(im, R * .01, R * .005)
    # three staggered rows of round keys, each a little domed button
    im, d = rel.layer()
    for row, (yy, n, off) in enumerate(((y + s * .2, 9, 0), (y + s * .38, 9, .09), (y + s * .56, 8, 0))):
        for i in range(n):
            xx = x + (i - (n - 1) / 2) * s * .19 + off * s
            d.ellipse([xx - s * .07, yy - s * .07, xx + s * .07, yy + s * .07], fill=255)
    rel.add(im, R * .02, s * .03, dome=.8, dome_w=s * .07)
    im, d = rel.layer()
    d.rounded_rectangle([x - s * .46, y + s * .66, x + s * .46, y + s * .73], radius=s * .03, fill=255)
    rel.add(im, R * .016, s * .03, dome=.7, dome_w=s * .035)
    legend_line(rel, c[0] - R * .64, c[1] + R * .12, R, "S", "roman", .19)
    legend_line(rel, c[0] + R * .64, c[1] + R * .12, R, "C", "roman", .19)
    legend_arc(rel, c, R, "WRITING", "roman", .18, -90, track=1.16, r=.8)
    legend_arc(rel, c, R, "BS·DETECTOR", "roman", .12, 90, bottom=True, track=1.1, r=.815)
    beads(rel, c, R * .95, 76, R * .016, R * .02, R)
    ring(rel, c, R * .9, R * .012, R * .014, R)

def d_tea(rel, c, R):
    """Archaic electrum: a cup and saucer with steam, inside an incuse square."""
    x, y = c[0], c[1] + R * .16
    s = R * .4
    im, d = rel.layer()
    d.ellipse([x - s * 1.08, y + s * .52, x + s * 1.08, y + s * .86], fill=255)          # saucer
    rel.add(im, R * .02, R * .015, dome=.6, dome_w=s * .15)
    im, d = rel.layer()
    d.chord([x - s * .72, y - s * .64, x + s * .72, y + s * .82], 0, 180, fill=255)      # cup bowl
    d.rectangle([x - s * .72, y - s * .1, x + s * .72, y + s * .1], fill=255)
    d.ellipse([x - s * .72, y - s * .22, x + s * .72, y + s * .02], fill=255)
    rel.add(im, R * .035, R * .012, dome=.8, dome_w=s * .55)
    im, d = rel.layer()
    d.ellipse([x + s * .56, y - s * .06, x + s * 1.02, y + s * .42], outline=255, width=max(3, int(s * .11)))   # handle
    rel.add(im, R * .03, s * .05, dome=.8, dome_w=s * .055)
    im, d = rel.layer()
    d.ellipse([x - s * .62, y - s * .19, x + s * .62, y - s * .03], fill=255)             # the tea, sunk into the rim
    rel.cut(im, R * .03, R * .012)
    # a band of tiny leaves round the cup
    im, d = rel.layer()
    for i in range(7):
        lx, ly = x - s * .5 + i * s * .166, y + s * .3
        ang = 0.55 if i % 2 else -0.55
        pts = []
        for t in np.linspace(0, 2 * math.pi, 24):
            px_, py_ = s * .085 * math.cos(t), s * .035 * math.sin(t)
            pts.append((lx + px_ * math.cos(ang) - py_ * math.sin(ang), ly + px_ * math.sin(ang) + py_ * math.cos(ang)))
        d.polygon(pts, fill=255)
    rel.add(im, R * .01, s * .02, dome=.8, dome_w=s * .03)
    # steam: three tapering S-curves
    im, d = rel.layer()
    for i, off in enumerate((-.32, .04, .38)):
        pts = [(x + s * off + s * .11 * math.sin(t * .55 + i * 1.3), y - s * .34 - t * s * .1) for t in np.linspace(0, 8, 40)]
        for j in range(len(pts) - 1):
            wj = max(2, int(s * (.075 - .05 * j / len(pts))))
            d.line([pts[j], pts[j + 1]], fill=255, width=wj)
    rel.add(im, R * .02, s * .03, dome=.8, dome_w=s * .04)
    legend_line(rel, c[0], c[1] - R * .5, R, "TEA", "greek", .22, track=1.5)

def d_carbon(rel, c, R):
    """Eighteenth-century crown: a works in a landscape, smoke curling from its stacks; dated."""
    x, y = c[0], c[1] + R * .06
    s = R * .56
    # exergue: ground line and hatched ground
    im, d = rel.layer()
    d.rectangle([x - s * 1.08, y + s * .5, x + s * 1.08, y + s * .57], fill=255)
    rel.add(im, R * .022, R * .008)
    im, d = rel.layer()
    for i in range(-20, 21):
        d.line([(x + i * s * .055, y + s * .6), (x + i * s * .055 - s * .05, y + s * .82)], fill=255, width=max(1, int(R * .007)))
    rel.add(im, R * .008, R * .004)
    # the works: a sawtooth-roofed hall
    hall = [(x - s * .92, y + s * .5), (x - s * .92, y + s * .02)]
    for i in range(4):
        x0 = x - s * .92 + i * s * .3
        hall += [(x0 + s * .3, y - s * .24), (x0 + s * .3, y + s * .02)]
    hall += [(x + s * .3, y + s * .5)]
    im, d = rel.layer(); d.polygon(hall, fill=255)
    rel.add(im, R * .035, R * .01, dome=.25, dome_w=R * .1)
    im, d = rel.layer()
    for i in range(4):   # each roof pitch catches light differently: slight step down per bay
        x0 = x - s * .92 + i * s * .3
        d.polygon([(x0, y + s * .02), (x0 + s * .3, y - s * .24), (x0 + s * .3, y + s * .02)], fill=255)
    rel.add(im, R * .008, R * .01)
    im, d = rel.layer()
    for i in range(4):
        d.rectangle([x - s * .84 + i * s * .3, y + s * .2, x - s * .72 + i * s * .3, y + s * .4], fill=255)
    rel.cut(im, R * .02, R * .006)
    # stacks
    im, d = rel.layer()
    for sx, hgt in ((.52, 1.06), (.82, .86)):
        d.polygon([(x + s * sx - s * .09, y + s * .5), (x + s * sx - s * .07, y - s * hgt),
                   (x + s * sx + s * .07, y - s * hgt), (x + s * sx + s * .09, y + s * .5)], fill=255)
    rel.add(im, R * .04, R * .012, dome=.6, dome_w=s * .07)
    im, d = rel.layer()
    for sx, hgt in ((.52, 1.06), (.82, .86)):
        for j in range(6):
            yj = y - s * hgt + (j + 1) * s * (hgt + .5) / 7
            d.line([(x + s * sx - s * .09, yj), (x + s * sx + s * .09, yj)], fill=255, width=max(1, int(R * .006)))
    rel.cut(im, R * .006, R * .003)
    # smoke: a chain of domed puffs drifting left and shrinking
    im, d = rel.layer()
    for (px, py, r) in ((.52, -1.16, .1), (.34, -1.08, .09), (.16, -1.04, .075), (0, -1.02, .06), (-.14, -1.02, .045)):
        d.ellipse([x + s * (px - r), y + s * (py - r), x + s * (px + r), y + s * (py + r)], fill=255)
    rel.add(im, R * .025, R * .01, dome=.9, dome_w=s * .09)
    # a tree on the left: the landscape the works sits in
    im, d = rel.layer()
    tx = x - s * .98
    d.rectangle([tx - s * .02, y + s * .1, tx + s * .02, y + s * .5], fill=255)
    rel.add(im, R * .02, R * .006)
    im, d = rel.layer()
    for (px, py, r) in ((0, -.06, .1), (-.07, .02, .07), (.07, .02, .07)):
        d.ellipse([tx + s * (px - r), y + s * (py - r), tx + s * (px + r), y + s * (py + r)], fill=255)
    rel.add(im, R * .028, R * .01, dome=.9, dome_w=s * .08)
    legend_line(rel, c[0], c[1] + R * .66, R, "2022", "modern", .14, track=1.2)
    legend_arc(rel, c, R, "CARBON · CAPTURE", "modern", .165, -90, track=1.06, r=.77)
    # crown: raised flat rim with a fine beaded circle inside it
    im, d = rel.layer()
    d.ellipse([c[0] - R * .99, c[1] - R * .99, c[0] + R * .99, c[1] + R * .99], outline=255, width=int(R * .075))
    rel.add(im, R * .03, R * .012)
    beads(rel, c, R * .87, 100, R * .011, R * .014, R)

def d_research(rel, c, R):
    """Medieval penny: a voided long cross with pellets in the angles, a flask at the centre."""
    x, y = c
    w = R * .075
    im, d = rel.layer()
    for a in (0, 90):
        ar = math.radians(a)
        for s_ in (-1, 1):
            p0 = (x + s_ * R * .2 * math.cos(ar), y + s_ * R * .2 * math.sin(ar))
            p1 = (x + s_ * R * .92 * math.cos(ar), y + s_ * R * .92 * math.sin(ar))
            d.line([p0, p1], fill=255, width=int(w))
    rel.add(im, R * .03, R * .012, dome=.3, dome_w=w * .5)
    im, d = rel.layer()          # "voided": a groove down each arm
    for a in (0, 90):
        ar = math.radians(a)
        for s_ in (-1, 1):
            p0 = (x + s_ * R * .22 * math.cos(ar), y + s_ * R * .22 * math.sin(ar))
            p1 = (x + s_ * R * .9 * math.cos(ar), y + s_ * R * .9 * math.sin(ar))
            d.line([p0, p1], fill=255, width=max(1, int(w * .32)))
    rel.cut(im, R * .02, R * .008)
    im, d = rel.layer()
    for qa in (45, 135, 225, 315):
        ar = math.radians(qa)
        px, py = x + R * .4 * math.cos(ar), y + R * .4 * math.sin(ar)
        for dx, dy in ((0, 0), (math.cos(ar) * .075, 0), (0, math.sin(ar) * .075)):
            qx, qy = px + R * dx, py + R * dy
            d.ellipse([qx - R * .036, qy - R * .036, qx + R * .036, qy + R * .036], fill=255)
    rel.add(im, R * .03, R * .02, dome=.9, dome_w=R * .036)
    # the flask sits in a sunken roundel
    im, d = rel.layer()
    d.ellipse([x - R * .21, y - R * .21, x + R * .21, y + R * .21], fill=255)
    rel.cut(im, R * .012, R * .01)
    ring(rel, c, R * .21, R * .016, R * .018, R)
    s = R * .16
    im, d = rel.layer()
    d.polygon([(x - s * .2, y - s * .95), (x + s * .2, y - s * .95), (x + s * .2, y - s * .3), (x + s * .82, y + s * .8),
               (x - s * .82, y + s * .8), (x - s * .2, y - s * .3)], fill=255)
    rel.add(im, R * .03, R * .01, dome=.6, dome_w=s * .4)
    im, d = rel.layer()
    d.polygon([(x - s * .46, y + s * .2), (x + s * .46, y + s * .2), (x + s * .7, y + s * .7), (x - s * .7, y + s * .7)], fill=255)
    rel.cut(im, R * .008, R * .006)
    legend_arc(rel, c, R, "+RESEARCH+", "roman", .18, -90, track=1.08, r=.79)
    legend_arc(rel, c, R, "SORBENTS", "medieval", .14, 90, bottom=True, track=1.1, r=.8)
    beads(rel, c, R * .955, 84, R * .014, R * .018, R)
    beads(rel, c, R * .64, 56, R * .012, R * .016, R)

def d_community(rel, c, R):
    """Broad, thin Byzantine-style gold: a round table with eight stools, radiant; legend round."""
    x, y = c
    s = R * .42
    im, d = rel.layer()
    for i in range(24):
        a = i * math.pi / 12
        d.line([(x + s * 1.04 * math.cos(a), y + s * 1.04 * math.sin(a)),
                (x + s * (1.3 if i % 2 == 0 else 1.2) * math.cos(a), y + s * (1.3 if i % 2 == 0 else 1.2) * math.sin(a))],
               fill=255, width=max(1, int(R * .013)))
    rel.add(im, R * .012, R * .006)
    im, d = rel.layer()
    d.ellipse([x - s * .5, y - s * .5, x + s * .5, y + s * .5], fill=255)
    rel.add(im, R * .03, R * .012, dome=.5, dome_w=s * .3)
    im, d = rel.layer()      # table top: a moulded edge
    d.ellipse([x - s * .4, y - s * .4, x + s * .4, y + s * .4], outline=255, width=max(1, int(R * .01)))
    rel.cut(im, R * .006, R * .004)
    im, d = rel.layer()
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        px, py = x + s * .82 * math.cos(a), y + s * .82 * math.sin(a)
        d.ellipse([px - s * .15, py - s * .15, px + s * .15, py + s * .15], fill=255)
    rel.add(im, R * .03, R * .015, dome=.85, dome_w=s * .15)
    im, d = rel.layer()
    for a in (-62, -118):
        ar = math.radians(a)
        px, py = x + R * .57 * math.cos(ar), y + R * .57 * math.sin(ar)
        for j in range(6):
            b = j * math.pi / 3
            d.line([(px, py), (px + R * .05 * math.cos(b), py + R * .05 * math.sin(b))], fill=255, width=max(1, int(R * .016)))
    rel.add(im, R * .02, R * .008)
    legend_arc(rel, c, R, "COMMUNITY", "greek", .17, -90, track=1.18, r=.8)
    legend_arc(rel, c, R, "· GATHERINGS ·", "greek", .12, 90, bottom=True, track=1.12, r=.82)
    beads(rel, c, R * .955, 120, R * .009, R * .012, R)
    ring(rel, c, R * .915, R * .008, R * .01, R)

# ---------------------------------------------------------------- metals
# base: clean metal colour; tone(s): what it tones or corrodes toward; dirt: what collects in recesses.
METALS = {
    "silver":        dict(base=(.86, .86, .85), tones=[(.58, .54, .50), (.52, .58, .74), (.86, .70, .46)], tone_k=.7, dirt=(.28, .26, .24), rough=.30, crust=0),
    "silver_bright": dict(base=(.86, .87, .88), tones=[(.80, .74, .62), (.64, .66, .74)], tone_k=.35, dirt=(.36, .35, .34), rough=.16, crust=0),
    "bronze":        dict(base=(.66, .44, .30), tones=[(.34, .44, .34), (.46, .30, .20)], tone_k=.55, dirt=(.20, .26, .20), rough=.42, crust=.6, crust_col=(.40, .50, .40)),
    "electrum":      dict(base=(.90, .78, .52), tones=[(.76, .58, .34), (.86, .80, .60)], tone_k=.45, dirt=(.40, .30, .18), rough=.34, crust=0),
    "billon":        dict(base=(.66, .64, .62), tones=[(.44, .42, .38), (.52, .50, .44)], tone_k=.6, dirt=(.20, .19, .18), rough=.46, crust=.4, crust_col=(.50, .46, .40)),
    "gold":          dict(base=(.96, .74, .34), tones=[(.92, .64, .30), (.98, .82, .46)], tone_k=.3, dirt=(.44, .30, .12), rough=.22, crust=0),
}

COINS = {
    "forecasting": dict(draw=d_forecasting, metal="silver", irregular=.9, offc=.02, cracks=1, seed=3),
    "writing":     dict(draw=d_writing, metal="bronze", irregular=.35, offc=.015, seed=4),
    "tea":         dict(draw=d_tea, metal="electrum", irregular=1.3, offc=.04, cracks=2, incuse=True, seed=5),
    "carbon":      dict(draw=d_carbon, metal="silver_bright", irregular=0, offc=0, reeded=True, seed=6),
    "research":    dict(draw=d_research, metal="billon", irregular=.8, offc=.025, cracks=1, seed=7),
    "community":   dict(draw=d_community, metal="gold", irregular=.15, offc=.008, thin=True, seed=8),
}

# ---------------------------------------------------------------- lighting (mirrored in coins.js)
# dir: the key light; col: its colour; win: a broad soft lobe around it (the window, or the lamp's
# glow on the walls); sky/hor/gnd: the rest of the room above, around and below.
DAY = dict(dir=unit((-.50, -.60, .62)), col=np.array([1.30, 1.25, 1.15]), win=np.array([.95, .93, .88]),
           sky=np.array([.54, .53, .51]), hor=np.array([.30, .29, .27]), gnd=np.array([.62, .58, .52]))
NIGHT = dict(dir=unit((.55, -.55, .45)), col=np.array([2.4, 1.85, 1.2]), win=np.array([.9, .7, .45]),
             sky=np.array([.42, .32, .21]), hor=np.array([.20, .15, .10]), gnd=np.array([.05, .09, .06]))

def env(v, L):
    z = v[..., 2]
    t1 = sstep((z + .15) / .45)[..., None]
    t2 = sstep((z - .3) / .7)[..., None]
    col = L["gnd"] * (1 - t1) + L["hor"] * t1
    col = col * (1 - t2) + L["sky"] * t2
    w = np.clip((v * L["dir"]).sum(-1), 0, 1)[..., None] ** 3
    return col + L["win"] * w

def shade(alb, n, rough, L):
    nx, ny, nz = n[..., 0], n[..., 1], n[..., 2]
    r = np.dstack([2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1])
    Er, En = env(r, L), env(n, L)
    ro = rough[..., None]
    E = Er * (1 - ro) + En * ro * .9
    p = np.exp2(9 * (1 - rough) + 1)
    rl = np.clip((r * L["dir"]).sum(-1), 0, 1)
    spec = np.minimum(rl ** p * (p + 2) / 8, 6)[..., None]
    lam = np.clip((n * L["dir"]).sum(-1), 0, 1)[..., None]
    metal = sstep((.92 - rough) / .3)[..., None]
    col_m = alb * (E + L["col"] * spec)
    col_d = alb * (L["col"] * lam * .9 + En * .6)
    col = col_d * (1 - metal) + col_m * metal
    over = np.clip(col - .8, 0, None)
    return np.where(col > .8, .8 + over / (1 + over * 2.5), col)

# ---------------------------------------------------------------- build one coin
def make(slug, ss=3):
    spec = COINS[slug]
    M = METALS[spec["metal"]]
    rng = np.random.default_rng(spec["seed"])
    S = OUT_S * ss
    R = R_OUT * ss
    c = S / 2 - WALL * R * .5            # centre the coin plus its wall
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    th = np.arctan2(yy - c, xx - S / 2)
    ir = spec["irregular"]
    ph = rng.uniform(0, 6.3, 4)
    def outline(theta):
        return R * (1 + ir * (.024 * np.cos(2 * (theta - ph[3])) + .014 * np.sin(3 * theta + ph[0]) + .008 * np.sin(5 * theta + ph[1])))
    redge = outline(th)
    # flan cracks: thin tapering splits from the edge
    cracks = []
    for _ in range(spec.get("cracks", 0)):
        ca = rng.uniform(0, 2 * math.pi); ln = rng.uniform(.07, .13); wd = rng.uniform(.012, .02)
        cracks.append((ca, ln, wd))
    dist = np.hypot(xx - S / 2, yy - c)
    def face_mask(dy=0.0):
        d_ = np.hypot(xx - S / 2, yy - c - dy)
        t_ = np.arctan2(yy - c - dy, xx - S / 2)
        re = outline(t_)
        m = np.clip((re - d_) / (1.2 * ss), 0, 1)
        for ca, ln, wd in cracks:
            # a V-shaped split: angular half-width shrinks linearly as it goes inward
            depth = np.clip((d_ - re * (1 - ln)) / (re * ln), 0, 1)
            ang = np.abs(np.angle(np.exp(1j * (t_ - ca))))
            m = m * np.clip((ang - wd * depth ** 1.5) * d_ / (1.0 * ss), 0, 1) ** (depth > 0)
        if spec.get("clip"):
            a, depth = spec["clip"]
            proj = (xx - S / 2) * math.cos(math.radians(a)) + (yy - c - dy) * math.sin(math.radians(a))
            m = np.minimum(m, np.clip((R * (1 - depth) - proj) / (1.2 * ss), 0, 1))
        return m
    face = face_mask()
    wall_m = np.clip(face_mask(WALL * R) - face, 0, 1)
    alpha = np.maximum(face, face_mask(WALL * R))
    # flan: slightly domed, rounded off at the edge; the die struck a little off centre
    inner = nd.distance_transform_edt(face > .5)
    h = R * .03 * sstep(inner / (R * .06)) ** .6 + R * .006 * smooth_noise(S, S, R * .7, rng) * sstep(inner / (R * .1))
    if not spec.get("thin"):
        h += R * .01 * (1 - (dist / R) ** 2).clip(0, None)
    off = rng.normal(0, R * spec["offc"], 2) if spec["offc"] else np.zeros(2)
    dc = (S / 2 + off[0], c + off[1])
    rel = Relief(S, ss)
    Rd = R * (.8 if spec.get("incuse") else .95)
    spec["draw"](rel, dc, Rd)
    relief = rel.h
    if spec.get("incuse"):
        half = R * .66
        q = np.maximum(np.abs(xx - dc[0]), np.abs(yy - dc[1]))
        # the punch was a little irregular
        q = q + R * .015 * smooth_noise(S, S, R * .2, rng)
        sq = sstep((half - q) / (R * .04))
        h -= R * .045 * sq
        relief = relief * sq
    h = h + relief * sstep(inner / (R * .02))
    # wear: high points flattened slightly, surface gently uneven, a few nicks and hairlines
    hi = np.clip(relief - R * .03, 0, None)
    h -= .35 * hi * (0.6 + 0.4 * smooth_noise(S, S, R * .3, rng))
    h += R * .0006 * smooth_noise(S, S, R * .05, rng)
    nick = np.zeros((S, S))
    for _ in range(int(rng.integers(1, 4))):
        a = rng.uniform(0, 2 * math.pi); rr = R * rng.uniform(.5, .97)
        px, py = S / 2 + rr * math.cos(a), c + rr * math.sin(a)
        nick += np.exp(-(((xx - px) ** 2 + (yy - py) ** 2) / (R * rng.uniform(.01, .02)) ** 2))
    h -= R * .005 * nick
    hair = Image.new("L", (S, S), 0); hd = ImageDraw.Draw(hair)
    for _ in range(40):
        a = rng.uniform(0, math.pi); x0, y0 = rng.uniform(0, S, 2); L_ = R * rng.uniform(.1, .5)
        hd.line([(x0, y0), (x0 + L_ * math.cos(a), y0 + L_ * math.sin(a))], fill=int(rng.uniform(80, 255)), width=1)
    hair = np.asarray(hair, float) / 255
    h -= R * .0015 * nd.gaussian_filter(hair, .5 * ss)
    # normals
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    # the edge wall: a sliver of the coin's thickness, facing down-screen and outward
    wall_n = np.dstack([np.cos(th) * .8, np.sin(th) * .8 + .35, np.full_like(th, .3)])
    if spec.get("reeded"):
        wall_n[..., 0] += .5 * np.sin(th * 180) * np.abs(np.sin(th))
    n = n * (1 - wall_m[..., None]) + wall_n * wall_m[..., None]
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    # materials
    cav = np.clip(nd.gaussian_filter(h, R * .025) - h, 0, None) / (R * .02)
    cav2 = np.clip(nd.gaussian_filter(h, R * .008) - h, 0, None) / (R * .008)
    top = np.clip((h - nd.gaussian_filter(h, R * .05)) / (R * .015), 0, 1)
    rim = np.clip(dist / R - .45, 0, 1)
    alb = np.broadcast_to(np.array(M["base"]), (S, S, 3)).copy()
    for t in M["tones"]:
        w = np.clip(smooth_noise(S, S, R * rng.uniform(.3, .7), rng) * 1.3 - .1, 0, 1)
        k = (M["tone_k"] * w * (.35 + .65 * rim))[..., None]
        alb = alb * (1 - k) + np.array(t) * k
    grime = np.clip(cav * .9 + cav2 * .5 + .25 * smooth_noise(S, S, R * .08, rng) - .1, 0, 1)
    grime *= (1 - top)
    alb = alb * (1 - grime[..., None] * .75) + np.array(M["dirt"]) * grime[..., None] * .75
    crust = np.zeros((S, S))
    if M["crust"]:
        crust = np.clip((smooth_noise(S, S, R * .12, rng) * .9 + cav * .8 - .5) * 2.2, 0, 1) * M["crust"] * (1 - top)
        alb = alb * (1 - crust[..., None]) + np.array(M["crust_col"]) * crust[..., None]
    # polished high points show clean, brighter metal
    alb = alb * (1 - top[..., None] * .35) + np.array(M["base"]) * 1.05 * top[..., None] * .35
    # The design and lettering stand out the way they do on a handled coin: everything raised is
    # rubbed bright and smooth, the field around it darker and duller with toning. This contrast in
    # the metal itself is what keeps the legends legible under any light, including the lamp's.
    raised = sstep(relief / (R * .014)) * (face > .5)
    fieldk = (1 - raised) * sstep(inner / (R * .03))
    alb = alb * (1 - .30 * fieldk[..., None])
    alb = alb * (1 - raised[..., None] * .45) + np.array(M["base"]) * 1.1 * raised[..., None] * .45
    rough = (M["rough"] + .06 * smooth_noise(S, S, R * .15, rng) + .25 * hair * .3
             - .10 * top - .12 * raised + .08 * fieldk + .30 * grime + .5 * crust)
    rough = np.where(wall_m > .5, M["rough"] + .15, rough)
    rough = np.clip(rough, .05, .95)
    alb = np.where(wall_m[..., None] > .5, alb * .85, alb)
    ao = np.clip(1 - cav * .35, .55, 1)
    alb = np.clip(alb * ao[..., None], 0, 1)
    # static daylight render, at the supersampled size, then box-downsampled
    lit = shade(alb, n, rough, DAY)
    def down(a):
        s = a.shape
        return a.reshape(s[0] // ss, ss, s[1] // ss, ss, *s[2:]).mean((1, 3))
    A = down(alpha)
    Ad = np.maximum(A, 1e-4)[..., None]
    lit_o = down(lit * alpha[..., None]) / Ad
    alb_o = down(alb * alpha[..., None]) / Ad
    n_o = down(n); n_o /= np.linalg.norm(n_o, axis=2, keepdims=True)
    r_o = down(rough)
    return dict(alpha=A, lit=lit_o, alb=alb_o, n=n_o, rough=r_o)

def save(slug, res, out):
    A = res["alpha"][..., None]
    lit = np.dstack([np.clip(res["lit"], 0, 1), A])
    Image.fromarray((lit * 255 + .5).astype(np.uint8), "RGBA").save(os.path.join(out, f"coin-{slug}.webp"), quality=84, method=6)
    left = np.dstack([np.clip(res["alb"], 0, 1), A])
    right = np.dstack([res["n"][..., 0] * .5 + .5, res["n"][..., 1] * .5 + .5, res["rough"], np.ones_like(A)])
    # where the coin isn't, keep the normal flat so compression doesn't bleed odd values in
    right[..., :2] = np.where(A > 0, right[..., :2], .5)
    sheet = np.concatenate([left, right], axis=1)
    Image.fromarray((np.clip(sheet, 0, 1) * 255 + .5).astype(np.uint8), "RGBA").save(
        os.path.join(out, f"coin-{slug}-mat.webp"), quality=86, method=6, exact=True)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    only = sys.argv[2:] or list(COINS)
    for slug in only:
        save(slug, make(slug), out)
        print(slug)
