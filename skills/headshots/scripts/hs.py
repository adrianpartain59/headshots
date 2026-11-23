#!/usr/bin/env python3
"""Headshot toolkit. macOS + Python 3.9+ with Pillow and numpy; nothing to download.

  hs.py check   PHOTO...                      grade a source photo and say what to retake
  hs.py frame   PHOTO OUT.jpg                 square crop with the head at the house size and spot (pads what's missing)
  hs.py like    SOURCE TAKE...                how close each take's face is to the source
  hs.py faces   OUT.jpg SOURCE TAKE...        aligned face crops, side by side
  hs.py sheet   OUT.jpg IMG... [--h 640]      labelled contact sheet
  hs.py background white|brand OUT.txt        write the background prompt (brand colour comes from the config)
  hs.py finish  BASE OUT_PREFIX --white EDIT [--brand EDIT] [--mode full|outfit] [--clothes neutral|keep] [--keep-blue]
                                              exact-colour finals: OUT_PREFIX-white and OUT_PREFIX-<brand> (.png and .jpg)
  hs.py widen   HEADSHOT.png OUT.jpg          put a finished, too-tight white headshot on a wider white square
  hs.py widen-finish CANVAS_WHITE.jpg GENERATED OUT_PREFIX   keep the old pixels, take only the new sleeves
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.expanduser("~/.cache/headshots"); BIN = f"{CACHE}/vision"
# House framing (fractions of the square's side).
HOUSE = dict(h=.577, w=.434, iod=.142, cx=.500, cy=.406)
sys.path.insert(0, HERE)
from config import BRAND, BRAND_RGB, CFG, COLORS
LW = np.array([.21, .72, .07], np.float32); lum = lambda x: x @ LW; lin = lambda x: (np.maximum(x, 0) / 255) ** 2.2

def vision(*args):
    src = f"{HERE}/vision.swift"
    if not os.path.exists(BIN) or os.path.getmtime(BIN) < os.path.getmtime(src):
        os.makedirs(CACHE, exist_ok=True); subprocess.run(["swiftc", "-O", src, "-o", BIN], check=True, stderr=subprocess.DEVNULL)
    return subprocess.run([BIN, *args], capture_output=True, text=True).stdout
def rgb(p): return ImageOps.exif_transpose(Image.open(p)).convert("RGB")
def tmp(im, ext="png"):
    f = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False).name; im.save(f, quality=97) if ext == "jpg" else im.save(f); return f
def landmarks(im):
    f = tmp(im) if not isinstance(im, str) else im; d = json.loads(vision("landmarks", f).splitlines()[0])
    if not isinstance(im, str): os.unlink(f)
    return d
def mask(im, kind="person"):
    f, o = tmp(im), tempfile.mktemp(suffix=".png"); vision("mask", kind, f, o); m = Image.open(o).convert("L"); m.load(); os.unlink(f); os.unlink(o); return m
def head(im, d=None, m=None):
    """Head box: hair top to chin, widest row between hair and mouth."""
    d = d or landmarks(im)
    if not d.get("faces"): sys.exit("No face found.")
    m = np.array(m or mask(im)) > 127; chin = max(p[1] for p in d["all"]); el, er = np.array(d["leftEye"]).mean(0), np.array(d["rightEye"]).mean(0)
    iod = float(np.linalg.norm(el - er)); rows = np.where(m.sum(1) > .6 * iod)[0]; top = int(rows.min()) if len(rows) else 0
    y1 = int(min(p[1] for p in d["outerLips"])); xs = [np.where(m[y])[0] for y in range(top, y1, max(1, (y1 - top) // 200))]; xs = [x for x in xs if len(x)]
    L, R = np.percentile([x.min() for x in xs], 3), np.percentile([x.max() for x in xs], 97)
    return dict(top=float(top), chin=float(chin), L=float(L), R=float(R), h=float(chin - top), w=float(R - L), iod=iod, eyex=float((el[0] + er[0]) / 2), cx=float((L + R) / 2), cy=float((top + chin) / 2),
                roll=float(np.degrees(np.arctan2(er[1] - el[1], er[0] - el[0]))))
def side_for(h): return float(np.mean([h[k] / HOUSE[k] for k in ("h", "w", "iod")]))
def circle_crop(a):
    """True when the photo is a round avatar on a flat background."""
    H, W = a.shape[:2]; n = max(4, min(H, W) // 60); c = [a[:n, :n], a[:n, -n:], a[-n:, :n], a[-n:, -n:]]
    flat = all(x.reshape(-1, 3).std(0).max() < 4 for x in c); cm = np.array([x.reshape(-1, 3).mean(0) for x in c])
    mids = np.array([a[H // 2 - n:H // 2 + n, W // 2 - n:W // 2 + n].mean((0, 1)), a[int(H * .2), W // 2], a[int(H * .5), int(W * .15)], a[int(H * .5), int(W * .85)]])
    return flat and np.abs(cm - cm.mean(0)).max() < 6 and np.abs(mids - cm.mean(0)).max(1).min() > 18

# ---------- check ----------
def check(p):
    im = rgb(p); W, H = im.size; a = np.array(im).astype(np.float32); ex = Image.open(p).getexif(); sub = ex.get_ifd(0x8769); d = landmarks(im); bad, warn, ok = [], [], []
    print(f"\n{os.path.basename(p)}  {W}x{H}")
    if not d.get("faces"): print("  RETAKE: no face found."); return
    m = mask(im); h = head(im, d, m); side = side_for(h)
    def add(cond_bad, cond_warn, msg_bad, msg_warn, msg_ok): (bad if cond_bad else warn if cond_warn else ok).append(msg_bad if cond_bad else msg_warn if cond_warn else msg_ok)
    hp = h["h"]; add(hp < 350, hp < 700, f"head is only {hp:.0f}px tall: the model will invent skin and hair detail. Get the original file, not a screenshot or avatar.", f"head {hp:.0f}px tall: usable, but 900+ keeps more of the real person", f"head {hp:.0f}px tall")
    f35 = sub.get(0xA405)
    if f35 and not (ex.get(0x010E) or "").lower().startswith("screenshot"):
        dist = float(f35) * np.hypot(W, H) / 43.27 * .063 / h["iod"]; ft = dist * 3.281
        add(dist < .7, dist < 1.2, f"shot from about {ft:.1f} ft: the nose and middle of the face are enlarged. Retake from 5 to 6.5 ft.", f"shot from about {ft:.1f} ft: slight widening of the face. 5 to 6.5 ft is better.", f"shot from about {ft:.1f} ft (lens {int(f35)}mm equivalent): no face warping")
    else: warn.append("no lens data (screenshot or stripped file), so distance is unknown: judge warping by eye (big nose, ears tucked back)")
    P = np.array(d["all"]); x0, y0 = P.min(0).astype(int); x1, y1 = P.max(0).astype(int); f = a[max(0, y0):y1, max(0, x0):x1]; Y = lum(f)
    med = float(np.median(Y)); hot = float((f.max(-1) > 250).mean() * 100); dark = float((Y < 25).mean() * 100)
    add(med < 60 or med > 225, med < 85 or med > 205, f"face brightness {med:.0f}/255: badly exposed", f"face brightness {med:.0f}/255: a bit {'dark' if med < 120 else 'bright'}", f"face brightness {med:.0f}/255")
    if hot > 2: (bad if hot > 8 else warn).append(f"{hot:.0f}% of the face is blown out (flash or direct sun): shiny spots the relight has to rebuild")
    gray = float(np.abs(a - a.mean(-1, keepdims=True)).mean()) < 2.5
    if gray: warn.append("black and white: hair, eye and skin colours would be guesses. Ask for a colour photo or the real colours.")
    else:
        sk = f[(Y > np.percentile(Y, 40)) & (Y < np.percentile(Y, 85))].mean(0); rb = float(sk[0] / max(sk[2], 1))
        if rb > 2.0: warn.append(f"strong orange/red room light on the skin (red is {rb:.1f}x blue): daylight gives truer colour")
    q = (x1 - x0) // 5; cy = int(np.mean([p[1] for p in d["nose"]])); l, r = Y[max(0, cy - y0 - q):cy - y0 + q, q // 2:q * 3 // 2].mean(), Y[max(0, cy - y0 - q):cy - y0 + q, -q * 3 // 2:-q // 2].mean(); ratio = float((max(l, r) / max(min(l, r), 1)) ** 2.2)
    add(ratio > 8, ratio > 4.5, f"one side of the face is {ratio:.0f}x brighter: hard side light", f"one side of the face is {ratio:.1f}x brighter", f"light is even enough across the face ({ratio:.1f}:1)")
    c = im.crop((int(max(0, x0)), int(max(0, y0)), int(x1), int(y1))); s = 200 / h["iod"]; g = np.array(c.resize((max(8, int(c.width * s)), max(8, int(c.height * s))), Image.LANCZOS).convert("L")).astype(np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]; sharp = float(lap.std())
    add(sharp < 3, sharp < 5, f"face is blurry (sharpness {sharp:.1f})", f"face is a little soft (sharpness {sharp:.1f})", f"face is sharp ({sharp:.1f})")
    if abs(h["roll"]) > 10: warn.append(f"head tilted {abs(h['roll']):.0f} degrees: fine if it's their look, but it leans in every version")
    if h["top"] < .01 * H: bad.append("top of the hair is cut off")
    if d["faces"] > 1: warn.append(f"{d['faces']} faces in frame: crop or pick a photo of one person")
    if circle_crop(a): warn.append("round avatar crop: the corners (shoulders, backdrop) have to be invented")
    miss = max(0, side - W) / side * 100
    if miss > 3: (bad if miss > 35 else warn).append(f"too tight: about {miss:.0f}% of the final square's width (shoulders) has to be invented. Step back next time.")
    if H - h["chin"] < .25 * h["h"]: warn.append("chest barely in frame: leave room down to mid-chest")
    v = "RETAKE if you can" if bad else "USABLE" if len(warn) > 1 else "GOOD"; print(f"  {v}")
    for t, L in (("x", bad), ("!", warn), ("ok", ok)):
        for s_ in L: print(f"   {t:>2}  {s_}")

# ---------- frame ----------
def frame(p, out, size=2048):
    im = rgb(p); a = np.array(im).astype(np.float32)
    if circle_crop(a):   # fill outside the circle with the wall tone so the model sees a normal photo
        H, W = a.shape[:2]; c = a[:4, :4].reshape(-1, 3).mean(0); diff = np.abs(a - c).max(-1) > 14; xs, ys = np.where(diff.sum(0) > H * .02)[0], np.where(diff.sum(1) > W * .02)[0]
        cx, cy, R = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min() + ys.max() - ys.min()) / 4; yy, xx = np.mgrid[0:H, 0:W]; o = np.hypot(xx - cx, yy - cy) > R * .99
        ang = np.arctan2(yy - cy, xx - cx); f = a.copy(); sx, sy = np.clip((cx + np.cos(ang) * R * .975).round().astype(int), 0, W - 1), np.clip((cy + np.sin(ang) * R * .975).round().astype(int), 0, H - 1); f[o] = a[sy, sx][o]
        b = np.array(Image.fromarray(f.astype("uint8")).filter(ImageFilter.GaussianBlur(R / 30))).astype(np.float32); f[o] = b[o]; im = Image.fromarray(f.clip(0, 255).astype("uint8")); print("round avatar: corners filled as a placeholder, use the CIRCLE line in the prompt")
    h = head(im); S = side_for(h); x0, y0 = (h["cx"] + h["eyex"]) / 2 - S * HOUSE["cx"], h["cy"] - S * HOUSE["cy"]
    pad = [max(0, int(np.ceil(v))) for v in (-x0, x0 + S - im.width, -y0, y0 + S - im.height)]
    A = Image.fromarray(np.pad(np.array(im), ((pad[2], pad[3]), (pad[0], pad[1]), (0, 0)), mode="edge"))
    A.crop((round(x0 + pad[0]), round(y0 + pad[2]), round(x0 + pad[0] + S), round(y0 + pad[2] + S))).resize((size, size), Image.LANCZOS).save(out, quality=96)
    print(f"square side {S:.0f}px of the source; padding the model must rebuild: left {pad[0]/S:.0%}, right {pad[1]/S:.0%}, top {pad[2]/S:.0%}, bottom {pad[3]/S:.0%}")
    if max(pad) > 0: print("use the PADDING line in the relight prompt")

# ---------- likeness, faces, sheet ----------
def sim(A, B):
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb; U, S, Vt = np.linalg.svd(b.T @ a); R = U @ Vt; s = S.sum() / (a ** 2).sum(); return s, R, mb - s * (R @ ma)
def like(src, takes):
    s = landmarks(rgb(src)); A = np.array(s["all"]); iod = np.linalg.norm(np.array(s["leftEye"]).mean(0) - np.array(s["rightEye"]).mean(0))
    op = lambda x, k: (lambda P: (P[:, 1].max() - P[:, 1].min()) / (P[:, 0].max() - P[:, 0].min()))(np.array(x[k]))
    gap = lambda x: np.mean([np.linalg.norm(np.array(x[b]).mean(0) - np.array(x[e]).mean(0)) for b, e in (("leftBrow", "leftEye"), ("rightBrow", "rightEye"))]) / np.linalg.norm(np.array(x["leftEye"]).mean(0) - np.array(x["rightEye"]).mean(0))
    for t in takes:
        d = landmarks(rgb(t)); 
        if not d.get("faces"): print(os.path.basename(t), "no face"); continue
        k, R, o = sim(np.array(d["all"]), A); e = np.linalg.norm((k * (R @ np.array(d["all"]).T)).T + o - A, axis=1).mean() / iod * 100; z = k * d["w"] / s["w"]
        print(f"{os.path.basename(t):28} face off by {e:.1f}% of eye distance   eyes open {op(d,'leftEye')/op(s,'leftEye'):.2f} / {op(d,'rightEye')/op(s,'rightEye'):.2f}   brow gap {gap(d)/gap(s):.2f}   zoom {z:.2f}{'   <- ZOOMED OUT' if z > 1.04 else ''}")
def faces(out, files, w=800):
    ds = [(f, rgb(f)) for f in files]; ds = [(f, i, landmarks(i)) for f, i in ds]; A = np.array(ds[0][2]["all"]); x0, y0 = A.min(0); x1, y1 = A.max(0); pw, ph = x1 - x0, y1 - y0
    bx = (x0 - .12 * pw, y0 - .3 * ph, x1 + .12 * pw, y1 + .08 * ph); size = (w, int(w * (bx[3] - bx[1]) / (bx[2] - bx[0]))); k = (bx[2] - bx[0]) / w; c = Image.new("RGB", ((w + 6) * len(ds), size[1] + 22), "white"); dr = ImageDraw.Draw(c)
    for n, (f, im, d) in enumerate(ds):
        s, R, t = sim(A, np.array(d["all"])); M = s * R * k; o = s * (R @ np.array(bx[:2])) + t
        c.paste(im.transform(size, Image.AFFINE, (M[0, 0], M[0, 1], o[0], M[1, 0], M[1, 1], o[1]), Image.BICUBIC), (n * (w + 6), 22)); dr.text((n * (w + 6) + 4, 5), os.path.basename(f), fill="black")
    c.save(out, quality=93)
def sheet(out, files, h=640):
    ims = [(f, rgb(f)) for f in files]; ims = [(f, i.resize((round(i.width * h / i.height), h), Image.LANCZOS)) for f, i in ims]; c = Image.new("RGB", (sum(i.width + 8 for _, i in ims), h + 22), "white"); d = ImageDraw.Draw(c); x = 0
    for f, i in ims: c.paste(i, (x, 22)); d.text((x + 4, 5), os.path.basename(f), fill="black"); x += i.width + 8
    c.save(out, quality=92)

# ---------- finish ----------
N = 4096
def blur(a, r):
    k = max(1, int(r // 6)); H, W = a.shape; x = np.array(Image.fromarray(a.astype(np.float32)).resize((W // k, H // k), Image.BOX)); rr = r / k; n = int(3 * rr) + 1
    g = np.exp(-.5 * (np.arange(-n, n + 1) / rr) ** 2); g /= g.sum(); x = np.pad(x, n, mode="edge"); x = np.apply_along_axis(lambda v: np.convolve(v, g, "valid"), 0, x); x = np.apply_along_axis(lambda v: np.convolve(v, g, "valid"), 1, x)
    return np.array(Image.fromarray(x.astype(np.float32)).resize((W, H), Image.BICUBIC))
def big(p): return rgb(p).resize((N, N), Image.LANCZOS)
def up(im): return np.array(im.resize((N, N), Image.BILINEAR))
def cutout(Ei, chin, backdrop):
    """Alpha, clean backdrop colour and local subject colour for an edit shot on a flat backdrop."""
    E = np.array(Ei).astype(np.float32); fg = mask(Ei, "fg"); s4 = fg.resize((N // 4, N // 4), Image.BOX); white = backdrop == "white"
    bg = up(s4.filter(ImageFilter.MaxFilter(61))) < 8; solid = up(s4.filter(ImageFilter.MinFilter(23))) > 247; B = np.median(E[bg], axis=0) if bg.sum() > 1e4 else np.array(COLORS[backdrop], np.float32)
    w = solid.astype(np.float32); wb, wc = blur(w, 55) + 1e-4, blur(w, 250) + 1e-6; m = np.clip(wb * 20, 0, 1)
    Fc = np.stack([blur(E[..., k] * w, 55) / wb * m + blur(E[..., k] * w, 250) / wc * (1 - m) for k in range(3)], -1); d = Fc - B
    al = np.clip(((E - B) * d).sum(-1) / np.maximum((d * d).sum(-1), 50), 0, 1); dist = np.abs(E - B).max(-1); lo, hi = (5, 14) if white else (12, 30); al *= np.clip((dist - lo) / (hi - lo), 0, 1)
    al = np.where(solid, 1, al); al = np.where(bg & (dist < (20 if white else 40)), 0, al)
    ed = np.array(fg.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255; inside = np.clip((ed - .5) / .4, 0, 1)
    sk = np.array(Image.fromarray((np.clip((E[..., 0] - E[..., 2] - 22) / 15, 0, 1) * np.clip((E.mean(-1) - 45) / 25, 0, 1) * 255).astype("uint8")).filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    al = np.maximum(al, inside * np.clip((dist - 35) / 35, 0, 1) * np.clip(sk * 1.6, 0, 1))           # ears and skin stay solid
    al = np.maximum(al, inside * np.clip((np.arange(N)[:, None] - chin - 60) / 60, 0, 1))               # clothes stay solid
    if not white: al = np.maximum(al, np.clip((lum(B) - 32 - lum(E)) / 45, 0, 1) * (~bg))              # dark hair and cloth can't be see-through on a mid-tone backdrop
    return E, al, B, Fc, sk, s4
def finish(base, prefix, edits, mode="full", clothes="neutral", keep_blue=False):
    Si = big(base); S = np.array(Si).astype(np.float32); d = landmarks(Si.resize((2048, 2048), Image.LANCZOS)); d = {k: ([[x * 2, y * 2] for x, y in v] if isinstance(v, list) else v) for k, v in d.items()}; h = head(Si, d, mask(Si)); chin = h["chin"]; yy = np.arange(N)[:, None].astype(np.float32); cache = {}
    for name, T in COLORS.items():
        src = name if edits.get(name) else "white"
        if src not in cache:
            E, al, B, Fc, sk, s4 = cutout(big(edits[src]), chin, src)
            c = Image.fromarray((al * 255).astype("uint8")).resize((N // 4, N // 4), Image.BOX).point(lambda v: 255 if v > 225 else 0).filter(ImageFilter.MedianFilter(9)).filter(ImageFilter.MinFilter(15))
            c = Image.fromarray(np.minimum(np.array(c), np.array(s4.point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.MinFilter(9))))); core = np.clip((np.array(c.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255 - .1) / .8, 0, 1)
            if mode == "outfit":   # only the real head is pasted back; the clothes come from the outfit take
                P = np.array(sorted(d["contour"])); lip = max(p[1] for p in d["outerLips"]); jaw = np.interp(np.arange(N), P[:, 0], P[:, 1], left=lip, right=lip) - 45; j = Image.fromarray(((yy < jaw[None, :]) * 255).astype("uint8")).resize((N // 4, N // 4), Image.BOX).filter(ImageFilter.GaussianBlur(10)).resize((N, N), Image.BICUBIC); core *= np.clip((np.array(j).astype(np.float32) / 255 - .05) / .9, 0, 1)
            cw = (core > .95).astype(np.float32); cb = blur(cw, 90) + 1e-4; LS, LE = lin(S), lin(E); g = np.stack([np.clip((blur(LS[..., k] * cw, 90) + 2e-4 * cb) / (blur(LE[..., k] * cw, 90) + 2e-4 * cb), .5, 1.6) for k in range(3)], -1)
            sel = (cw > 0) & (sk > .8) & (np.abs(yy - chin) < 900); gs = np.median(LS[sel][::97] / np.maximum(LE[sel][::97], 1e-4), axis=0) if sel.sum() > 1000 else np.ones(3); far = gs if mode == "outfit" else np.median(g[cw > 0][::997], axis=0); conf = np.clip(cb * 8, 0, 1)[..., None]; g = g * conf + far * (1 - conf)
            if mode == "outfit": g = 1 + (g - 1) * np.maximum(np.clip((chin - 60 - yy) / 120, 0, 1), np.clip(blur(sk, 10) * 1.3, 0, 1))[..., None]
            a = al[..., None]; F = np.clip(np.where(a > .04, (E - (1 - a) * B) / np.maximum(a, .04), Fc), 0, 255); F = 255 * np.clip(lin(F) * g, 0, 1) ** (1 / 2.2)
            if mode == "outfit" and clothes == "neutral":   # new clothes come back purple; black, charcoal and white should be neutral
                cl = np.clip((yy - chin + 40) / 60, 0, 1) * (1 - np.clip(blur(sk, 6) * 1.5, 0, 1)); bl = blur(np.clip((E[..., 2] - np.maximum(E[..., 0], E[..., 1]) - 14) / 16, 0, 1) * np.clip((95 - lum(E)) / 20, 0, 1), 6) if keep_blue else 0
                k = (cl * (1 - np.clip(bl, 0, 1)) * .92)[..., None]; F = F * (1 - k) + lum(F)[..., None] * np.array([.995, 1, 1.01], np.float32) * k
            r = (slice(int(h["top"] + .03 * h["h"]), int(h["top"] + .17 * h["h"])), slice(int(h["cx"] - .22 * h["w"]), int(h["cx"] + .22 * h["w"]))); px = S[r][core[r] > .9]; Lp = lum(px); lo_, hi_ = np.percentile(Lp, (20, 90)); px = px[(Lp > lo_) & (Lp < hi_)]; hue = px.mean(0) / lum(px.mean(0)); cap = float(np.clip(np.percentile(Lp, 95) * 1.2, 90, 175))
            fl = lum(F); skin = np.clip((F[..., 0] - F[..., 2] - 20) / 20, 0, 1) * np.clip((fl - cap * .9) / 25, 0, 1); z = (np.clip((chin + .06 * h["h"] - yy) / 150, 0, 1) * (1 - skin) * np.clip((.985 - al) / .13, 0, 1))[..., None]
            F = F * (1 - z) + np.minimum(fl, cap)[..., None] * hue * z; F = F * (1 - core[..., None]) + S * core[..., None]; cache[src] = (F, a, gs)
        F, a, gs = cache[src]; T = np.array(T, np.float32); O = np.where(a > 0, a * F + (1 - a) * T, T); O[-14:] = O[-15:-14]; im = Image.fromarray(np.clip(O + .5, 0, 255).astype("uint8"))
        im.save(f"{prefix}-{name}.png", optimize=True); im.save(f"{prefix}-{name}.jpg", quality=96, subsampling=0); print(f"{prefix}-{name}.jpg  from the {src} edit  corner #{'%02X%02X%02X' % im.getpixel((60, 60))}")

def background(which, out):
    t = open(f"{HERE}/../assets/prompts/background.txt").read(); c = "pure white (#FFFFFF)" if which == "white" else f"solid colour, exactly hex {CFG['brand_color']} (RGB {BRAND_RGB[0]}, {BRAND_RGB[1]}, {BRAND_RGB[2]}),"
    open(out, "w").write(t.replace("{COLOUR}", c)); print(out)
    if which == "brand" and lum(np.array(BRAND_RGB)) < 70: print("dark brand colour: dark hair would vanish into it. Skip this edit and let `finish` place the white cutout on it.")

# ---------- widen a finished, too-tight headshot ----------
def widen(p, out):
    im = rgb(p); h = head(im); S = side_for(h); x0, y0 = (h["cx"] + h["eyex"]) / 2 - S * .5, h["cy"] - S * HOUSE["cy"]; k = N / S; c = Image.new("RGB", (N, N), "white")
    c.paste(im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS), (round(-x0 * k), round(-y0 * k))); c.save(out, quality=97, subsampling=0); json.dump(dict(x0=round(-x0 * k), x1=round(-x0 * k) + round(im.width * k)), open(out + ".json", "w")); print("now run assets/prompts/outpaint.txt on", out)
def widen_finish(canvas, gen, prefix):
    box = json.load(open(canvas + ".json")); C = np.array(big(canvas)).astype(np.float32); Gi = big(gen); h = head(Image.fromarray(C.astype("uint8"))); G, al, B, Fc, sk, s4 = cutout(Gi, h["chin"], "white"); X0, X1 = box["x0"], box["x1"]; y = slice(int(h["chin"] + .1 * N), N - 10)
    ref = [(C[y, s].reshape(-1, 3), G[y, s].reshape(-1, 3), al[y, s].reshape(-1)) for s in (slice(max(0, X0) + 10, max(0, X0) + 260), slice(min(N, X1) - 260, min(N, X1) - 10))]; gl, gr = [np.median(lin(c[q > .99]), axis=0) / np.maximum(np.median(lin(v[q > .99]), axis=0), 1e-5) for c, v, q in ref]
    a = al[..., None]; F = np.clip((G - (1 - a) * B) / np.maximum(a, .05), 0, 255); xx = np.arange(N)[None, :, None].astype(np.float32) / N; F = 255 * np.clip(lin(F) * (gl * (1 - xx) + gr * xx), 0, 1) ** (1 / 2.2); x = np.arange(N).astype(np.float32); k = np.clip(np.minimum(x - X0 - 4, X1 - 4 - x) / 150., 0, 1); K = (k * k * (3 - 2 * k))[None, :, None]
    # alpha of the old picture on white, so it can move to blue as well
    _, ao, Bo, Fo, _, _ = cutout(Image.fromarray(C.astype("uint8")), h["chin"], "white"); A_ = ao[..., None]; FO = np.clip(np.where(A_ > .04, (C - (1 - A_) * Bo) / np.maximum(A_, .04), Fo), 0, 255)
    for n, T in COLORS.items():
        T = np.array(T, np.float32); old = C if n == "white" else A_ * FO + (1 - A_) * T; O = old * K + (a * F + (1 - a) * T) * (1 - K); O[-14:] = O[-15:-14]; im = Image.fromarray(np.clip(O + .5, 0, 255).astype("uint8")); im.save(f"{prefix}-{n}.png"); im.save(f"{prefix}-{n}.jpg", quality=96, subsampling=0); print(f"{prefix}-{n}.jpg")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="c", required=True)
    q = sp.add_parser("check"); q.add_argument("f", nargs="+"); q = sp.add_parser("frame"); q.add_argument("f"); q.add_argument("out"); q = sp.add_parser("like"); q.add_argument("src"); q.add_argument("takes", nargs="+")
    q = sp.add_parser("faces"); q.add_argument("out"); q.add_argument("f", nargs="+"); q = sp.add_parser("sheet"); q.add_argument("out"); q.add_argument("f", nargs="+"); q.add_argument("--h", type=int, default=640)
    q = sp.add_parser("background"); q.add_argument("which", choices=["white", "brand"]); q.add_argument("out"); q = sp.add_parser("finish"); q.add_argument("base"); q.add_argument("prefix"); q.add_argument("--white", required=True); q.add_argument("--brand"); q.add_argument("--mode", choices=["full", "outfit"], default="full"); q.add_argument("--clothes", choices=["neutral", "keep"], default="neutral"); q.add_argument("--keep-blue", action="store_true")
    q = sp.add_parser("widen"); q.add_argument("f"); q.add_argument("out"); q = sp.add_parser("widen-finish"); q.add_argument("canvas"); q.add_argument("gen"); q.add_argument("prefix"); a = ap.parse_args()
    if a.c == "check": [check(f) for f in a.f]
    elif a.c == "frame": frame(a.f, a.out)
    elif a.c == "like": like(a.src, a.takes)
    elif a.c == "faces": faces(a.out, a.f)
    elif a.c == "sheet": sheet(a.out, a.f, a.h)
    elif a.c == "background": background(a.which, a.out)
    elif a.c == "finish": finish(a.base, a.prefix, {"white": a.white, BRAND: a.brand}, a.mode, a.clothes, a.keep_blue)
    elif a.c == "widen": widen(a.f, a.out)
    elif a.c == "widen-finish": widen_finish(a.canvas, a.gen, a.prefix)
