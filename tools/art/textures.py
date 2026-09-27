"""Cloth and paper textures.

The tiles (linen, baize, paper) carry only fine detail, threads, fibres and nap, and nothing at a
large scale, so their repeats don't show. The large-scale life of the cloth, the soft undulations,
two creases where it was folded, a little uneven wear, lives in one small, un-tiled image,
cloth-shade.jpg, that is stretched over the whole table and blended in with soft-light. Tiles are
drawn at twice the size they are shown, for sharp threads on high-density screens.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.environ.get("ART_OUT", os.path.join(HERE, "out"))

def wn(rng, shape, sig):
    n = nd.gaussian_filter(rng.standard_normal(shape), sig, mode="wrap")
    return n / np.abs(n).max()

def save_jpg(lum_rgb, name, q):
    Image.fromarray((np.clip(lum_rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(OUTD, name), quality=q, optimize=True, progressive=True)

def linen(T=512, p=6, seed=11):
    """Plain-weave linen, thread by thread. Each thread has its own thickness and tone, and slubs
    (thick, slightly darker stretches) along its length; at each crossing one thread passes over the
    other and is rounded like a cylinder; the gaps between threads are dark."""
    rng = np.random.default_rng(seed)
    n = T // p                                          # threads per tile (T divisible by p)
    yy, xx = np.mgrid[0:T, 0:T].astype(float)
    def threads(along, across, idx_axis):
        # along: coordinate along the thread; across: coordinate across the set of threads
        i = (across // p).astype(int) % n
        f = (across % p) / p                            # 0..1 across one thread
        tone = rng.normal(0, .018, n)[i]
        # slubs: 1D noise along each thread, wrapped so the tile repeats seamlessly
        sl = nd.gaussian_filter1d(rng.standard_normal((n, T)), 9, axis=1, mode="wrap")
        sl = sl / np.abs(sl).max()
        slub = sl[i, along.astype(int) % T]
        width = .9 + .14 * np.clip(slub, 0, 1)         # thicker where slubbed
        prof = np.clip(1 - ((f - .5) / (width / 2)) ** 2, 0, 1)
        return prof, tone - .03 * np.clip(slub, 0, 1) + .012 * np.clip(-slub, 0, 1), i
    warp, wt, wi = threads(yy, xx, 1)
    weft, ft, fi = threads(xx, yy, 0)
    over = ((wi + fi) % 2 == 0)
    top = np.where(over, warp, weft)
    tone = np.where(over, wt, ft)
    # the thread on top humps where it crosses: brighter in the middle of each float
    along = np.where(over, (yy % p) / p, (xx % p) / p)
    hump = .5 + .5 * np.sin(np.pi * along)
    lum = .74 + .13 * np.sqrt(top) * (.8 + .2 * hump) + tone
    lum = np.where(top < .02, .69 + .1 * np.maximum(warp, weft), lum)      # gaps
    lum += .012 * nd.gaussian_filter(rng.standard_normal((T, T)), .6, mode="wrap")
    lum = nd.gaussian_filter(lum, .55, mode="wrap")
    rgb = lum[..., None] * np.array([1.0, .968, .905])
    save_jpg(rgb, "linen.jpg", 80)

def baize(T=512, seed=3):
    """Billiard-cloth green wool felt: fine fibres, a slight nap running one way, a few longer fibres."""
    rng = np.random.default_rng(seed)
    fuzz = wn(rng, (T, T), .8)
    nap = nd.gaussian_filter(rng.standard_normal((T, T)), (.5, 2.4), mode="wrap"); nap /= np.abs(nap).max()
    fib = np.zeros((T, T))
    for _ in range(900):                                # stray longer fibres catching the light
        x, y = rng.integers(0, T, 2); L = rng.integers(6, 18); a = rng.uniform(0, np.pi)
        for t in range(L):
            fib[int(y + t * np.sin(a)) % T, int(x + t * np.cos(a)) % T] += 1
    fib = nd.gaussian_filter(fib, .5, mode="wrap")
    lum = .17 + .03 * fuzz + .02 * nap + .03 * np.clip(fib, 0, 1)
    rgb = lum[..., None] * np.array([.50, 1.0, .62])
    save_jpg(rgb, "baize.jpg", 78)

def paper(T=512, seed=21):
    """Laid paper: fine laid lines, a chain line every 128 px, fibres, no large-scale cloudiness."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:T, 0:T].astype(float)
    laid = .5 + .5 * np.sin(2 * np.pi * yy / 4 + wn(rng, (T, T), 20) * .6)
    chain = np.exp(-((((xx + wn(rng, (T, T), 40) * 3) % 128) - 64) / 1.6) ** 2)
    f1 = nd.gaussian_filter(rng.standard_normal((T, T)), (.5, 3.0), mode="wrap"); f1 /= np.abs(f1).max()
    f2 = nd.gaussian_filter(rng.standard_normal((T, T)), (3.0, .5), mode="wrap"); f2 /= np.abs(f2).max()
    lum = .955 + .008 * laid - .016 * chain + .01 * f1 + .008 * f2 + .005 * wn(rng, (T, T), 12)
    rgb = lum[..., None] * np.array([1.0, .975, .925])
    save_jpg(rgb, "paper.jpg", 84)

def cloth_shade(W=480, H=320, seed=5):
    """Neutral grey (128 = no change under soft-light) with the cloth's large-scale shape: gentle
    undulations where it lies unevenly, two old fold creases (one down the middle, one across),
    and faint uneven wear."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    u, v = xx / W, yy / H
    warp = nd.gaussian_filter(rng.standard_normal((H, W)), 40); warp /= np.abs(warp).max()
    und = np.sin((u * 2.2 + v * 1.1 + .35 * warp) * 2 * np.pi) * .5 + np.sin((u * -1.3 + v * 2.6 + .5 * warp) * 2 * np.pi + 1.3) * .5
    val = 9 * und
    # creases: a ridge seen under light from the upper left is bright on its left/top face, dark on the other
    for pos, axis in ((.5 + .01 * warp, 'x'), (.42 + .012 * warp, 'y')):
        d = (u - pos) * W if axis == 'x' else (v - pos) * H
        val += -14 * d / 2.2 * np.exp(-(d / 2.2) ** 2) * 1.2 + 5 * np.exp(-(d / 10) ** 2) * np.sign(-d)
    val += 5 * wn(rng, (H, W), 25)
    save_jpg(np.repeat(((128 + val) / 255)[..., None], 3, axis=2), "cloth-shade.jpg", 82)

if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    linen(); baize(); paper(); cloth_shade()
    for f in ("linen.jpg", "baize.jpg", "paper.jpg", "cloth-shade.jpg"):
        print(f, os.path.getsize(os.path.join(OUTD, f)))
