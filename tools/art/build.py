"""Re-render every generated image used by the site into assets/images/site/.

    pip install numpy scipy pillow
    python tools/art/build.py

Nothing here uses an image model: coins, the name plate, the lamp and the frame are height
maps lit like metal or clay (see coins3.py, relics.py, relics2.py, frames.py); the cloths
are filtered noise that tiles seamlessly.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "images", "site"))
os.makedirs(os.path.join(SITE, "coins"), exist_ok=True)
os.environ["ART_OUT"] = SITE
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image
from scipy import ndimage as nd

import coins3, relics, relics2, frames

# ---- coins (seeds give each coin its particular wear, toning and shape)
SEEDS = {"Forecasting": 3, "Writing": 4, "Tea": 5, "Carbon capture": 6, "Research": 7, "Community": 8}
SLUG = {"Forecasting": "forecasting", "Writing": "writing", "Tea": "tea", "Carbon capture": "carbon",
        "Research": "research", "Community": "community"}
for name, seed in SEEDS.items():
    im = coins3.coin(200, name, seed=seed)
    im.crop(im.getbbox()).save(os.path.join(SITE, "coins", f"coin-{SLUG[name]}.webp"), quality=86, method=6)

# ---- name plate, lamp, picture frame
relics2.tabula()                    # -> name-tabula.webp
os.replace(os.path.join(SITE, "name-tabula.webp"), os.path.join(SITE, "nameplate.webp"))
relics.oil_lamp()                   # -> lamp.webp
relics.flame()                      # -> flame.webp
frames.moulding_corners("palmette") # -> frame-bronze-palmette.webp
os.replace(os.path.join(SITE, "frame-bronze-palmette.webp"), os.path.join(SITE, "frame.webp"))
frames.mat_paper()                  # -> mat.jpg

# ---- cloths (tileable)
def wn(rng, T, sig):
    n = nd.gaussian_filter(rng.standard_normal((T, T)), sig, mode="wrap")
    return n / np.abs(n).max()

def linen(T=512, seed=11):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:T, 0:T].astype(float)
    warpth = 0.5 + 0.5 * np.sin(2 * np.pi * xx / 4 + wn(rng, T, 3) * 0.8)
    weftth = 0.5 + 0.5 * np.sin(2 * np.pi * yy / 4 + wn(rng, T, 3) * 0.8)
    over = (np.sin(2 * np.pi * xx / 8) * np.sin(2 * np.pi * yy / 8)) > 0
    weave = np.where(over, warpth * 0.7 + 0.3 * weftth, weftth * 0.7 + 0.3 * warpth)
    slubx = nd.gaussian_filter(rng.standard_normal((T, T)), (0.6, 14), mode="wrap"); slubx /= np.abs(slubx).max()
    sluby = nd.gaussian_filter(rng.standard_normal((T, T)), (14, 0.6), mode="wrap"); sluby /= np.abs(sluby).max()
    lum = (0.845 + 0.035 * weave + 0.022 * slubx + 0.022 * sluby + 0.02 * wn(rng, T, 40)
           + 0.012 * nd.gaussian_filter(rng.standard_normal((T, T)), 0.5, mode="wrap"))
    rgb = lum[..., None] * np.array([0.995, 0.965, 0.905])
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(SITE, "linen.jpg"), quality=84)

def baize(T=640, seed=3):
    rng = np.random.default_rng(seed)
    fuzz = wn(rng, T, 1.0)
    nap = nd.gaussian_filter(rng.standard_normal((T, T)), (0.6, 2.2), mode="wrap"); nap /= np.abs(nap).max()
    lum = 0.17 + 0.035 * fuzz + 0.02 * nap + 0.02 * wn(rng, T, 30) + 0.02 * wn(rng, T, 90)
    rgb = lum[..., None] * np.array([0.50, 1.0, 0.62])
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(SITE, "baize.jpg"), quality=84)

linen(); baize()
print("rendered into", SITE)

# ---- letter paper for the homepage (laid paper: fine laid lines, faint chain lines, fibres)
def paper(T=512, seed=21):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:T, 0:T].astype(float)
    laid = 0.5 + 0.5 * np.sin(2 * np.pi * yy / 4 + wn(rng, T, 20) * 0.6)          # 128 laid lines per tile
    chain = np.exp(-((((xx + wn(rng, T, 40) * 3) % 128) - 64) / 1.6) ** 2)       # a chain line every 128px
    fibres = nd.gaussian_filter(rng.standard_normal((T, T)), (0.5, 3.0), mode="wrap"); fibres /= np.abs(fibres).max()
    fibres2 = nd.gaussian_filter(rng.standard_normal((T, T)), (3.0, 0.5), mode="wrap"); fibres2 /= np.abs(fibres2).max()
    cloud = wn(rng, T, 50)
    lum = 0.955 + 0.008 * laid - 0.018 * chain + 0.01 * fibres + 0.008 * fibres2 + 0.014 * cloud
    rgb = lum[..., None] * np.array([1.0, 0.975, 0.925])
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(SITE, "paper.jpg"), quality=86)

paper()

# ---- link-preview card, favicon and touch icon (composited from the images above)
def cards():
    from PIL import ImageFilter
    def shadowed(canvas, im, xy, off=(5, 9), blur=7, alpha=110):
        a = im.split()[-1]
        sh = Image.new("RGBA", im.size, (60, 45, 20, 0)); sh.putalpha(a.point(lambda v: v * alpha // 255))
        pad = blur * 3
        big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.paste(sh, (pad, pad))
        big = big.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(big, (xy[0] - pad + off[0], xy[1] - pad + off[1])); canvas.alpha_composite(im, xy)
    lin = Image.open(os.path.join(SITE, "linen.jpg")).convert("RGBA")
    card = Image.new("RGBA", (1200, 630))
    for x in range(0, 1200, 512):
        for y in range(0, 630, 512): card.paste(lin, (x, y))
    plate = Image.open(os.path.join(SITE, "nameplate.webp")).convert("RGBA")
    plate = plate.resize((520, round(520 * plate.height / plate.width)), Image.LANCZOS).rotate(1.2, Image.BICUBIC, expand=True)
    shadowed(card, plate, ((1200 - plate.width) // 2, 60))
    order = ["forecasting", "writing", "tea", "carbon", "research", "community"]
    rots = [-7, 5, -4, 6, -9, 3]; dys = [0, -22, 8, -14, 12, -6]
    for i, (slug, r) in enumerate(zip(order, rots)):
        c = Image.open(os.path.join(SITE, "coins", f"coin-{slug}.webp")).convert("RGBA")
        c = c.resize((150, round(150 * c.height / c.width)), Image.LANCZOS).rotate(-r, Image.BICUBIC, expand=True)
        cx = 115 + i * 194
        shadowed(card, c, (cx - c.width // 2, 400 + dys[i] - c.height // 2))
    card.convert("RGB").save(os.path.join(SITE, "..", "og-card.jpg"), quality=88)
    fc = Image.open(os.path.join(SITE, "coins", "coin-forecasting.webp")).convert("RGBA")
    s = max(fc.size); sq = Image.new("RGBA", (s, s)); sq.paste(fc, ((s - fc.width) // 2, (s - fc.height) // 2))
    sq.resize((64, 64), Image.LANCZOS).save(os.path.join(SITE, "..", "favicon.png"))
    sq.resize((180, 180), Image.LANCZOS).save(os.path.join(SITE, "apple-touch-icon.png"))

cards()
