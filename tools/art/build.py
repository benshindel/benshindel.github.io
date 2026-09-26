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
