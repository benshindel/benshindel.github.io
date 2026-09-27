# Site art generators

Every image in `assets/images/site/` (coins, the bronze name plate, the terracotta oil lamp and its flame, the picture frame, the linen and baize cloths and the letter paper) is drawn by these Python scripts. No image model is involved: each object is a height map, shaded with reflections of a simple room plus one soft key light, which is what makes the metal read as metal.

```
pip install numpy scipy pillow
python tools/art/build.py
```

- `coins4.py` has the six coins, rendered at 340 px and at 520 px (`-2x`) for high-density screens. Each has its own `d_*` design function, built from layered, rounded relief; a metal (base colour, toning, what collects in the recesses); and a visible sliver of edge. It writes two files per coin: `coin-*.webp`, the coin lit by daylight, and `coin-*-mat.webp`, a material sheet (colour, normals, roughness) that `assets/js/coins.js` uses to re-light the coin live, by the lamp at night and as the pointer tilts it. The `shade()` function here and the shader in `coins.js` are the same model; change one, change the other.
- `relics3.py` has the lamp, the flame, the name plate (`tabula`) and the picture frame (`frame`, a bronze moulding with a cast rosette over each mitre, used as a CSS border-image with a slice of 108).
- `textures.py` has the linen, baize and paper tiles (fine detail only, so the repeats don't show) and `cloth-shade.jpg`, the soft folds and creases stretched over the whole table.
- `frames.py` has the mat (and the earlier frame studies).
- `build.py` re-renders everything the site uses, plus the link-preview card and icons.
- `coins3.py`, `relics.py`, `relics2.py` and `sketch.py` are the earlier versions and studies (a few helpers are still imported from them).
- `fonts/` holds Cinzel, Uncial Antiqua and IM Fell English SC, all under the SIL Open Font License. They're used for the lettering on the coins.

This folder is excluded from the Jekyll build in `_config.yml`.
