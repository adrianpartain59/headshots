"""Settings, looked up in this order: $HEADSHOTS_CONFIG, ~/.config/headshots/config.json, defaults.

{"brand_name": "acme-blue", "brand_color": "#2563EB", "key_command": ["op", "run", "--"]}
key_command is optional: a command that puts GEMINI_API_KEY in the environment of whatever follows it.
"""
import json, os
PATH = os.path.expanduser(os.environ.get("HEADSHOTS_CONFIG", "~/.config/headshots/config.json"))
CFG = {"brand_name": "brand", "brand_color": "#2563EB", "key_command": []}
if os.path.exists(PATH): CFG.update(json.load(open(PATH)))
def hex_rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
BRAND, BRAND_RGB = CFG["brand_name"], hex_rgb(CFG["brand_color"])
COLORS = {"white": (255, 255, 255), BRAND: BRAND_RGB}
