"""Re-render every generated image used by the site into assets/images/site/.

    pip install numpy scipy pillow
    python tools/art/build.py

Nothing here uses an image model. The coins (coins4.py), the name plate, the lamp and its flame
(relics3.py) and the frame (frames.py) are height maps shaded with reflections of a simple room and
a soft key light; the cloths and paper (textures.py) are filtered noise and woven threads that tile
seamlessly. Each coin also gets a material sheet (coin-*-mat.webp) that assets/js/coins.js uses to
re-light it live in the browser.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "images", "site"))
os.makedirs(os.path.join(SITE, "coins"), exist_ok=True)
os.environ["ART_OUT"] = SITE
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image

import coins4, relics3, frames, textures

# ---- coins: static daylight image + material sheet for each
for slug in coins4.COINS:
    coins4.save_all(slug, os.path.join(SITE, "coins"))

# ---- lamp, flame, name plate, picture frame
im, wick = relics3.lamp()
print("lamp wick at %.3f, %.3f of the image (the .flame and .halo positions in site.css)" % wick)
relics3.flame()
relics3.tabula()
relics3.frame()                     # -> frame.webp (border-image slice 108 in site.css)
frames.mat_paper()                  # -> mat.jpg

# ---- cloths, paper, and the large-scale shading laid over the cloth
textures.linen(); textures.baize(); textures.paper(); textures.cloth_shade()
print("rendered into", SITE)

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
    lin = Image.open(os.path.join(SITE, "linen.jpg")).convert("RGBA").resize((256, 256), Image.LANCZOS)   # as shown on the site
    card = Image.new("RGBA", (1200, 630))
    for x in range(0, 1200, 256):
        for y in range(0, 630, 256): card.paste(lin, (x, y))
    plate = Image.open(os.path.join(SITE, "nameplate.webp")).convert("RGBA")
    plate = plate.resize((520, round(520 * plate.height / plate.width)), Image.LANCZOS).rotate(1.2, Image.BICUBIC, expand=True)
    shadowed(card, plate, ((1200 - plate.width) // 2, 60))
    order = ["forecasting", "writing", "tea", "carbon", "research", "community"]
    rots = [-7, 5, -4, 6, -9, 3]; dys = [0, -22, 8, -14, 12, -6]
    for i, (slug, r) in enumerate(zip(order, rots)):
        c = Image.open(os.path.join(SITE, "coins", f"coin-{slug}.webp")).convert("RGBA")
        c = c.crop(c.getbbox())
        c = c.resize((150, round(150 * c.height / c.width)), Image.LANCZOS).rotate(-r, Image.BICUBIC, expand=True)
        cx = 115 + i * 194
        shadowed(card, c, (cx - c.width // 2, 400 + dys[i] - c.height // 2))
    card.convert("RGB").save(os.path.join(SITE, "..", "og-card.jpg"), quality=88)
    fc = Image.open(os.path.join(SITE, "coins", "coin-forecasting.webp")).convert("RGBA")
    fc = fc.crop(fc.getbbox())
    s = max(fc.size); sq = Image.new("RGBA", (s, s)); sq.paste(fc, ((s - fc.width) // 2, (s - fc.height) // 2))
    sq.resize((64, 64), Image.LANCZOS).save(os.path.join(SITE, "..", "favicon.png"))
    sq.resize((180, 180), Image.LANCZOS).save(os.path.join(SITE, "apple-touch-icon.png"))

cards()
