# Headshots

A Claude Code skill that turns an ordinary photo of someone into professional headshots that still look exactly
like them.

Send Claude a photo and ask for a headshot. It:

1. **Grades the photo** (shooting distance, light, sharpness, framing) and tells you if a better one is worth taking.
2. **Frames it** as a square, with every head at the same size and spot, so a team page lines up.
3. **Relights it** like a studio portrait with Gemini's image models, in several takes, and measures how close each
   face is to the original. You pick the one that looks most like the person.
4. **Changes only what you ask for**: white and brand-colour backgrounds, a suit, a quarter-zip, or the same clothes.
5. **Finishes it** by pasting the approved face back over every edit, so the person never drifts, on the exact hex
   colour with clean hair edges.

It also widens headshots that are cropped too tight, makes before/after images, and has a
[guide to taking a good source photo](skills/headshots/references/source-photo-guide.md), with a message you can send
people.

## The short version of the photo guide

Phone 5 to 6 feet away, back camera at 2x, eye level, facing a window, lights and flash off, plain wall a few feet
behind, waist up with room around the shoulders. Send the original file. Distance is the one thing nobody can fix
later: at 12 inches the nose measures about 30% larger, at 5 feet essentially not at all
([JAMA Facial Plastic Surgery, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5876805)).

## Install

```bash
claude plugin marketplace add adrianpartain59/headshots
claude plugin install headshots@headshots
```

Or copy `skills/headshots/` into `~/.claude/skills/`.

Needs a Mac (it uses Apple's Vision framework for faces and cutouts, compiled on first run with Xcode's command line
tools), Python 3.9+ with `pillow` and `numpy`, Chrome for the before/after images, and a
[Gemini API key](https://aistudio.google.com/apikey).

## Set up

```bash
export GEMINI_API_KEY=...
mkdir -p ~/.config/headshots && cp config.example.json ~/.config/headshots/config.json
```

Put your brand colour in that file. If your key lives in a secrets manager, set `key_command` to the command that
runs another command with it, for example `["op", "run", "--"]`.

## Use

> Make me a headshot from ~/Downloads/IMG_1234.jpg, one on white and one on our blue

> Now do it with this person, in a suit and in what they're wearing

> Is this photo good enough for a headshot?

A person costs roughly $1.50 to $4 in Gemini calls (list prices, November 2026) and takes 6 to 25 minutes depending
on how many outfits you ask for.

## Scripts

All of them also work without Claude:

| Script | Does |
|---|---|
| `hs.py check` | Grades a source photo, including the distance it was shot from (original files only) |
| `hs.py frame` | Square crop at the house framing, fills round-avatar corners |
| `gen.py` | Runs a prompt through both image models, several takes at once, with retries |
| `hs.py like` / `faces` / `sheet` | How close each take is, aligned face crops, contact sheets |
| `hs.py background` / `finish` | The background prompts, and the exact-colour finals |
| `hs.py widen` / `widen-finish` | Zooms out a finished headshot without touching it |
| `before_after.py` | Before/after images, one per person and one for everybody |

## Good to know

- Photos are sent to Google's API. Only use photos of people who know about it.
- The results are AI-edited photos. The models' invisible watermark stays in the pixels; label them where a platform
  or employer asks.
- Developed on seven people with short to neck-length hair, light skin and little facial hair. Long hair, glasses,
  full beards, darker skin, bald heads and headwear have not been tried yet; check edges and skin tone with extra
  care, and please open an issue with what you find.

MIT licensed.
