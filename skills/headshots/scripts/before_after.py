#!/usr/bin/env python3
"""Before/after images for a social post.

  before_after.py OUT_DIR  name1=BEFORE,AFTER  name2=BEFORE,AFTER ...

One person   -> OUT_DIR/<name>.jpg, 16:9, two squares.
Two or more  -> also OUT_DIR/all.jpg, one 4:5 image (people as rows). Post that one: X crops the first image of a 3-image grid.
Each before is cropped so the head sits where it does in the after, as far as the photo allows.
"""
import os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hs import head, rgb
from PIL import Image
CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
out = sys.argv[1]; os.makedirs(f"{out}/img", exist_ok=True); names = []
for arg in sys.argv[2:]:
    n, v = arg.split("=", 1); bf, af = v.split(","); A, B = rgb(af), rgb(bf); a, b = head(A), head(B); W, H = B.size
    want = float(np.mean([b["iod"] / a["iod"], b["h"] / a["h"]])) * A.width; s = min(want, W, H)
    x0, y0 = min(max(b["eyex"] - a["eyex"] / A.width * s, 0), W - s), min(max(b["cy"] - a["cy"] / A.height * s, 0), H - s)
    B.crop((round(x0), round(y0), round(x0 + s), round(y0 + s))).resize((1480, 1480), Image.LANCZOS).save(f"{out}/img/{n}-before.jpg", quality=95)
    A.resize((1480, 1480), Image.LANCZOS).save(f"{out}/img/{n}-after.jpg", quality=95); names.append(n)
    if s < want * .97: print(f"{n}: before photo is too narrow to zoom out fully, so the head looks {want/s-1:.0%} larger there")
CSS = "<!doctype html><meta charset=utf-8><link href='https://fonts.googleapis.com/css2?family=League+Gothic&display=swap' rel=stylesheet><style>html,body{margin:0;background:#121212}.l{font-family:'League Gothic';font-weight:400;letter-spacing:2px;text-transform:uppercase;color:#F4F3F0;text-align:center}img{display:block}"
def render(name, html, w, h):
    f = f"{out}/{name}.html"; open(f, "w").write(html)
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2", "--virtual-time-budget=8000", f"--window-size={w},{h}", f"--screenshot={os.path.abspath(out)}/{name}.png", f"file://{os.path.abspath(f)}"], stderr=subprocess.DEVNULL, check=True)
    im = Image.open(f"{out}/{name}.png").convert("RGB"); im.save(f"{out}/{name}.jpg", quality=92, subsampling=0); os.unlink(f"{out}/{name}.png"); print(f"{out}/{name}.jpg {im.size}")
for n in names:
    render(n, CSS + f".w{{display:flex;gap:40px;padding:32px 40px 36px}}.l{{font-size:72px;line-height:72px;margin-bottom:20px}}img{{width:740px;height:740px}}</style><div class=w><div><div class=l>Before</div><img src=img/{n}-before.jpg></div><div><div class=l>After</div><img src=img/{n}-after.jpg></div></div>", 1600, 900)
if len(names) > 1:
    th = min(588, int((1876 - 24 * (len(names) - 1) - 148) / len(names))); rows = "".join(f"<img src=img/{n}-before.jpg style='object-position:50% 20%'><img src=img/{n}-after.jpg style='object-position:50% 40%'>" for n in names)
    render("all", CSS + f".g{{display:grid;grid-template-columns:680px 680px;gap:24px;justify-content:center;padding-top:36px}}.l{{font-size:88px;line-height:88px}}img{{width:680px;height:{th}px;object-fit:cover}}</style><div class=g><div class=l>Before</div><div class=l>After</div>{rows}</div>", 1600, 2000)
