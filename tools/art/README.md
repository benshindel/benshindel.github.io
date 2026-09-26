# Site art generators

Every image in `assets/images/site/` (coins, the bronze name plate, the terracotta oil lamp, the picture frame, and the linen and baize cloths) is drawn by these Python scripts. No image model is involved: each object is a height map lit like struck metal or fired clay.

```
pip install numpy scipy pillow
python tools/art/build.py
```

- `coins3.py` has the six coins. Each has its own `d_*` design function, metal and border.
- `relics.py` and `relics2.py` have the lamp and the name plate (`tabula`). The alternative name styles are also here.
- `frames.py` has the bronze moulding with palmette corners, plus the other frame and corner studies.
- `build.py` re-renders everything the site uses.
- `fonts/` holds Cinzel, Uncial Antiqua and IM Fell English SC, all under the SIL Open Font License. They're used for the lettering on the coins.

This folder is excluded from the Jekyll build in `_config.yml`.
