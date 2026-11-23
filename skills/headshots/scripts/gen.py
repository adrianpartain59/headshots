#!/usr/bin/env python3
"""Run one prompt on one photo through the image models, several takes at once.

  gen.py PHOTO PROMPT.txt OUT_PREFIX [--pro 3] [--nb 2] [--aspect 1:1]

Writes OUT_PREFIX_pro_a.jpg, OUT_PREFIX_nb_a.jpg ... at 4K. Reads GEMINI_API_KEY from the environment, or
re-runs itself under the config's key_command when it isn't set. Get a key at https://aistudio.google.com/apikey
List price per 4K image (checked 2026-11-23): pro about $0.24, nb about $0.08.
"""
import argparse, base64, json, os, shutil, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CFG
from concurrent.futures import ThreadPoolExecutor
MODELS = {"pro": "gemini-3-pro-image", "nb": "gemini-nano-banana-2.1"}

def one(args):
    tag, src, prompt, out, aspect = args
    mt = "image/png" if src.lower().endswith("png") else "image/jpeg"
    body = {"contents": [{"role": "user", "parts": [
        {"inlineData": {"mimeType": mt, "data": base64.b64encode(open(src, "rb").read()).decode()}}, {"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": aspect, "imageSize": "4K"}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELS[tag]}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    t = time.time()
    for attempt in range(3):   # the API sometimes hangs or cuts a response short
        try:
            r = json.load(urllib.request.urlopen(req, timeout=200)); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:200]; time.sleep(8)
            if e.code in (400, 403, 404): return f"{os.path.basename(out)}: HTTP {e.code} {msg}"
        except Exception as e:
            msg = type(e).__name__; time.sleep(3)
    else:
        return f"{os.path.basename(out)}: failed after 3 tries ({msg})"
    for c in r.get("candidates", []):
        for p in (c.get("content") or {}).get("parts", []):
            if not p.get("thought") and "inlineData" in p:
                open(out, "wb").write(base64.b64decode(p["inlineData"]["data"])); return f"{os.path.basename(out)}: ok {time.time()-t:.0f}s"
    why = (r.get("candidates") or [{}])[0].get("finishReason") or r.get("promptFeedback")
    return f"{os.path.basename(out)}: no image ({why})"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("photo"); ap.add_argument("prompt"); ap.add_argument("out")
    ap.add_argument("--pro", type=int, default=3); ap.add_argument("--nb", type=int, default=2); ap.add_argument("--aspect", default="1:1")
    a = ap.parse_args()
    if not os.environ.get("GEMINI_API_KEY"):
        kc = CFG["key_command"]
        if os.environ.get("HS_REEXEC") or not kc or not shutil.which(kc[0]): sys.exit("GEMINI_API_KEY is not set. Export it, or set key_command in ~/.config/headshots/config.json")
        os.environ["HS_REEXEC"] = "1"; os.execvp(kc[0], kc + [sys.executable] + sys.argv)
    prompt = open(a.prompt).read(); jobs = []
    if "{" in prompt and "}" in prompt: sys.exit("The prompt still has {PLACEHOLDERS}; fill them in first.")
    for tag, n in (("pro", a.pro), ("nb", a.nb)):
        jobs += [(tag, a.photo, prompt, f"{a.out}_{tag}_{'abcdefgh'[i]}.jpg", a.aspect) for i in range(n)]
    with ThreadPoolExecutor(len(jobs)) as ex:
        for line in ex.map(one, jobs): print(line, flush=True)
