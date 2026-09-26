"""Homepage concept sketches: a painted/generated scene fills the viewport, link-objects sit
in the scene, and the intro text flows around them. Renders desktop + phone for each concept."""
import math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
LORA_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"

def font(size, italic=False, bold=False):
    f = ImageFont.truetype(LORA_I if italic else LORA, size)
    try:
        f.set_variation_by_axes([700 if bold else 400])
    except Exception:
        pass
    return f

INTRO = ("Hi, I'm Ben. I'm a materials scientist who became a forecaster. I spent five years at "
         "Northwestern making sponges that pull heavy metals out of water and carbon dioxide out of "
         "the air, plus a side project on what tea leaves do to the water you brew them in. These days "
         "I mostly try to put numbers on the future. I forecast with RAND and Metaculus, I'm part of "
         "Samotsvety, and I write The BS Detector, a newsletter about science, AI, and claims that "
         "don't hold up. I also host gatherings for people who like thinking about what comes next, "
         "construct crosswords, and play pickup basketball at the county gym. "
         "Pick something below, or write to me at benshindel@gmail.com.")

LINKS = ["Forecasting", "Writing", "Tea", "Carbon capture", "Research", "Community"]

# ---------------------------------------------------------------- noise
def smooth_noise(h, w, scale, rng, octaves=3):
    out = np.zeros((h, w))
    amp = 1.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        small = rng.standard_normal((h // s + 3, w // s + 3))
        im = Image.fromarray(small.astype(np.float32), mode="F").resize((w + 2 * s, h + 2 * s), Image.BICUBIC)
        out += amp * np.array(im)[s:s + h, s:s + w]
        amp *= 0.5
    return out / (np.abs(out).max() + 1e-9)

# ---------------------------------------------------------------- text flow
def flow_text(draw, text, x0, x1, y0, y1, objs, fnt, lh, fill, pad=18, halo=None):
    """Place words line by line into the free intervals left by circular objects."""
    words = text.split()
    wi = 0
    y = y0
    space = draw.textlength(" ", font=fnt)
    while y + lh <= y1 and wi < len(words):
        # blocked intervals on this line (check both top and bottom of the line box)
        blocks = []
        for (cx, cy, r) in objs:
            rr = r + pad
            dy = min(abs(y - cy), abs(y + lh * .8 - cy)) if not (y <= cy <= y + lh) else 0
            if dy < rr:
                hw = math.sqrt(rr * rr - dy * dy)
                blocks.append((cx - hw, cx + hw))
        blocks.sort()
        free, cur = [], x0
        for a, b in blocks:
            if a > cur:
                free.append((cur, min(a, x1)))
            cur = max(cur, b)
        if cur < x1:
            free.append((cur, x1))
        # like CSS floats: text takes one run per line (the widest free interval)
        free = sorted(free, key=lambda ab: ab[1] - ab[0], reverse=True)[:1]
        for a, b in free:
            if b - a < 70:
                continue
            x = a
            while wi < len(words):
                wlen = draw.textlength(words[wi], font=fnt)
                if x + wlen > b:
                    break
                if halo:
                    draw.text((x, y), words[wi], font=fnt, fill=halo, stroke_width=3, stroke_fill=halo)
                draw.text((x, y), words[wi], font=fnt, fill=fill)
                x += wlen + space
                wi += 1
        y += lh
    return wi == len(words)

def chrome(draw, W, H, ink, phone, halo=None):
    """Name + small nav overlaid on the scene."""
    if phone:
        draw.text((22, 26), "Ben Shindel", font=font(30, bold=True), fill=ink)
        for k in range(3):
            draw.line([(W - 46, 36 + k * 8), (W - 24, 36 + k * 8)], fill=ink, width=2)
    else:
        draw.text((96, 58), "Ben Shindel", font=font(46, bold=True), fill=ink)
        x = W - 96
        cx0, cy0 = W - 96 - 9, 88
        draw.ellipse([cx0 - 9, cy0 - 9, cx0 + 9, cy0 + 9], outline=ink, width=2)
        draw.pieslice([cx0 - 9, cy0 - 9, cx0 + 9, cy0 + 9], 90, 270, fill=ink)
        x -= 48
        for item in reversed(["Blog", "Crosswords", "Cookbook"]):
            f = font(19)
            wl = draw.textlength(item, font=f)
            x -= wl
            draw.text((x, 76), item, font=f, fill=ink)
            x -= 30

def label(draw, cx, cy, text, size, fill, stroke=None):
    f = font(size, italic=True)
    lines = text.split(" ") if len(text) > 10 else [text]
    total = len(lines) * size * 1.1
    for i, ln in enumerate(lines):
        wl = draw.textlength(ln, font=f)
        draw.text((cx - wl / 2, cy - total / 2 + i * size * 1.1), ln, font=f, fill=fill,
                  stroke_width=(2 if stroke else 0), stroke_fill=stroke)

# ================================================================ concept A: raked gravel garden
def garden(W, H, objs, seed=1):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    sp = 13 if W > 600 else 9
    warp = smooth_noise(H, W, 180, rng) * 5
    # distance to nearest stone edge
    d = np.full((H, W), 1e9)
    for (cx, cy, r) in objs:
        d = np.minimum(d, np.hypot(xx - cx, yy - cy) - r * 1.08)
    ring_zone = sp * 5.5
    straight = (yy + 7 * np.sin(xx / 260) + warp) / sp
    rings = (d + warp * 0.6) / sp
    t = np.where(d < ring_zone, rings, straight)
    # blend band between ring zone and straight rake to avoid a hard seam
    f = t - np.floor(t)
    groove = -0.20 * np.exp(-((f - 0.5) / 0.13) ** 2) + 0.07 * np.exp(-((f - 0.25) / 0.10) ** 2)
    seam = np.clip((d - ring_zone) / 4, 0, 1) * np.clip((ring_zone + 10 - d) / 10, 0, 1)
    base = 0.80 + groove * (1 - 0.6 * seam) + 0.035 * smooth_noise(H, W, 400, rng)
    grain = rng.standard_normal((H, W)) * 0.035
    img = np.clip(base + grain, 0, 1)
    rgb = np.stack([img * 0.99, img * 0.975, img * 0.95], -1)
    im = Image.fromarray((rgb * 255).astype(np.uint8))
    # stones: irregular blobs with soft shadow and mottled surface
    sh = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sh)
    shapes = []
    for (cx, cy, r) in objs:
        ph = rng.uniform(0, 6.28, 3)
        pts = []
        for a in np.linspace(0, 2 * math.pi, 90, endpoint=False):
            rr = r * (1 + 0.07 * math.sin(3 * a + ph[0]) + 0.05 * math.sin(5 * a + ph[1]) + 0.03 * math.sin(2 * a + ph[2]))
            pts.append((cx + rr * math.cos(a) * 1.08, cy + rr * math.sin(a) * 0.92))
        shapes.append(pts)
        sd.polygon([(x + r * 0.10, y + r * 0.14) for x, y in pts], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    im = Image.composite(Image.new("RGB", (W, H), (70, 68, 66)), im, sh.point(lambda v: int(v * 0.55)))
    for (cx, cy, r), pts in zip(objs, shapes):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        tex = 0.36 + 0.10 * smooth_noise(H, W, max(8, r / 3), rng) + 0.05 * rng.standard_normal((H, W))
        # light from the upper left
        tex += 0.12 * np.clip(1 - np.hypot(xx - (cx - r * .35), yy - (cy - r * .4)) / (r * 1.5), 0, 1)
        stone = Image.fromarray((np.clip(np.stack([tex, tex * .99, tex * .97], -1), 0, 1) * 255).astype(np.uint8))
        im = Image.composite(stone, im, m.filter(ImageFilter.GaussianBlur(0.8)))
    return im

# ================================================================ concept B: pond with lily pads
def pond(W, H, objs, seed=2):
    rng = np.random.default_rng(seed)
    base = np.zeros((H, W, 3))
    n = smooth_noise(H, W, 300, rng)
    top = np.array([46, 58, 60]) / 255
    bot = np.array([28, 38, 42]) / 255
    g = np.linspace(0, 1, H)[:, None, None]
    base = top * (1 - g) + bot * g + n[..., None] * 0.05
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    pal = [(64, 82, 84), (86, 104, 102), (120, 136, 130), (38, 50, 54), (150, 162, 150), (98, 110, 118)]
    k = 1 if W > 600 else 0.6
    for _ in range(int(W * H / 90)):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        L = rng.uniform(10, 42) * k
        a = rng.normal(0, 0.08)
        c = pal[rng.integers(len(pal))]
        al = int(rng.uniform(25, 90))
        dr.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=c + (al,), width=int(rng.uniform(2, 6) * k) + 1)
    # sky reflection glints
    for _ in range(int(W * H / 2500)):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        L = rng.uniform(20, 70) * k
        dr.line([(x, y), (x + L, y + rng.normal(0, 1))], fill=(200, 206, 196, int(rng.uniform(30, 90))), width=2)
    im = Image.alpha_composite(im, layer.filter(ImageFilter.GaussianBlur(0.6)))
    # pads
    pads = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pads)
    for (cx, cy, r) in objs:
        notch = rng.uniform(0, 360)
        pd.ellipse([cx - r + 6, cy - r + 10, cx + r + 6, cy + r + 10], fill=(10, 16, 18, 110))
        col = tuple(int(v) for v in rng.choice([[96, 124, 92], [110, 132, 96], [84, 112, 88]]))
        pd.pieslice([cx - r, cy - r, cx + r, cy + r], notch + 18, notch + 360 - 18, fill=col + (255,))
        for a in np.linspace(0, 360, 16, endpoint=False):
            if abs(((a - notch + 180) % 360) - 180) < 22:
                continue
            ar = math.radians(a)
            pd.line([(cx, cy), (cx + r * .93 * math.cos(ar), cy + r * .93 * math.sin(ar))], fill=(140, 160, 118, 110), width=1)
        for _ in range(int(r * 3)):
            a = rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(rng.uniform(0, 1))
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            pd.line([(x, y), (x + rng.uniform(3, 9) * k, y)], fill=(150, 170, 120, 50), width=2)
    im = Image.alpha_composite(im, pads)
    # one pale flower
    (cx, cy, r) = objs[2]
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    for i, a in enumerate(np.linspace(0, 2 * math.pi, 9, endpoint=False)):
        px, py = cx + r * .95 + 18 * k * math.cos(a), cy - r * .75 + 18 * k * math.sin(a)
        fd.ellipse([px - 12 * k, py - 12 * k, px + 12 * k, py + 12 * k], fill=(232, 222, 214, 230))
    fd.ellipse([cx + r * .95 - 8 * k, cy - r * .75 - 8 * k, cx + r * .95 + 8 * k, cy - r * .75 + 8 * k], fill=(214, 186, 120, 255))
    im = Image.alpha_composite(im, fl)
    return im.convert("RGB")

# ================================================================ concept C: kites in a painted sky
def sky(W, H, objs, seed=3):
    rng = np.random.default_rng(seed)
    g = np.linspace(0, 1, H)[:, None, None]
    top = np.array([150, 170, 184]) / 255
    bot = np.array([226, 222, 210]) / 255
    base = top * (1 - g) + bot * g + smooth_noise(H, W, 400, rng)[..., None] * 0.02
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    k = 1 if W > 600 else 0.6
    # clouds: clusters of soft dabs, lit from above
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cl)
    for _ in range(9 if W > 600 else 5):
        ccx, ccy = rng.uniform(-100, W + 100), rng.uniform(H * .15, H * .95)
        cw = rng.uniform(220, 520) * k
        for _ in range(int(260 * k)):
            x = ccx + rng.normal(0, cw / 3)
            y = ccy + rng.normal(0, cw / 12) - abs(x - ccx) * 0.05
            s = rng.uniform(14, 40) * k
            shade = int(np.clip(250 - (y - ccy + cw / 10) * 1.6, 188, 252))
            cd.ellipse([x - s, y - s * .6, x + s, y + s * .6], fill=(shade, shade, shade + 2, int(rng.uniform(20, 55))))
    im = Image.alpha_composite(im, cl.filter(ImageFilter.GaussianBlur(3)))
    # kites
    kt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kd = ImageDraw.Draw(kt)
    cols = [((164, 74, 58), (196, 150, 84)), ((52, 72, 110), (208, 196, 170)), ((72, 96, 72), (214, 184, 96)),
            ((150, 60, 70), (230, 214, 190)), ((60, 60, 64), (190, 170, 120)), ((112, 72, 104), (216, 200, 170))]
    for i, (cx, cy, r) in enumerate(objs):
        tilt = rng.uniform(-0.25, 0.25)
        def rot(px, py):
            return (cx + px * math.cos(tilt) - py * math.sin(tilt), cy + px * math.sin(tilt) + py * math.cos(tilt))
        T, R, B, L = rot(0, -r * 1.05), rot(r * .78, -r * .18), rot(0, r * 1.25), rot(-r * .78, -r * .18)
        C = rot(0, -r * .18)
        a, b = cols[i % len(cols)]
        kd.polygon([T, R, C], fill=a + (255,)); kd.polygon([T, C, L], fill=b + (255,))
        kd.polygon([L, C, B], fill=a + (255,)); kd.polygon([C, R, B], fill=b + (255,))
        kd.line([T, B], fill=(60, 50, 40, 200), width=2); kd.line([L, R], fill=(60, 50, 40, 200), width=2)
        # tail with bows
        pts = [B]
        for t in range(1, 30):
            pts.append((B[0] + 10 * k * math.sin(t / 3 + i) * t / 6, B[1] + t * 5 * k))
        kd.line(pts, fill=(70, 60, 50, 170), width=1)
        for t in (8, 16, 24):
            x, y = pts[t]
            kd.polygon([(x - 7 * k, y - 4 * k), (x, y), (x - 7 * k, y + 4 * k)], fill=a + (230,))
            kd.polygon([(x + 7 * k, y - 4 * k), (x, y), (x + 7 * k, y + 4 * k)], fill=a + (230,))
        # string running down out of frame
        kd.line([C, (C[0] - W * .15, H + 20)], fill=(90, 80, 70, 90), width=1)
    im = Image.alpha_composite(im, kt)
    return im.convert("RGB")

# ================================================================ layouts
DESK = dict(W=1440, H=900, x0=96, x1=900, y0=170, y1=860, fs=21, lh=34,
            objs=[(860, 250, 90), (150, 420, 76), (1150, 640, 72), (1170, 330, 112), (700, 700, 84), (330, 760, 72)])
PHONE = dict(W=390, H=844, x0=22, x1=368, y0=92, y1=830, fs=15, lh=24,
             objs=[(318, 150, 48), (60, 300, 48), (322, 440, 44), (68, 590, 52), (300, 712, 50), (100, 780, 44)])

def render(name, scene, ink, labfill, labstroke, halo=None):
    for dev, L in (("desktop", DESK), ("phone", PHONE)):
        W, H = L["W"], L["H"]
        im = scene(W, H, L["objs"])
        dr = ImageDraw.Draw(im)
        chrome(dr, W, H, ink, dev == "phone", halo)
        flow_text(dr, INTRO, L["x0"], L["x1"], L["y0"], L["y1"], L["objs"], font(L["fs"]), L["lh"], ink, halo=halo,
                  pad=16 if dev == "phone" else 24)
        for (cx, cy, r), lab in zip(L["objs"], LINKS):
            label(dr, cx, cy, lab, max(14, int(r * .27)), labfill, labstroke)
        im.save(f"{OUT}/{name}_{dev}.jpg", quality=86)
        print(name, dev)

if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["garden", "pond", "sky"]
    if "garden" in which:
        render("garden", garden, (34, 32, 30), (236, 232, 224), None, halo=(214, 210, 202))
    if "pond" in which:
        render("pond", pond, (232, 228, 214), (246, 242, 228), (40, 54, 40))
    if "sky" in which:
        render("sky", sky, (30, 36, 44), (250, 246, 236), (40, 36, 30), halo=None)
