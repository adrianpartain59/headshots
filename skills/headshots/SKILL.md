---
name: headshots
description: Turns an ordinary photo of a real person (phone photo, selfie, old avatar, black-and-white picture) into professional headshots that still look exactly like them. Relights it like a studio shot, frames it as a square with every head at the same size and spot, puts it on exact white and a brand colour, swaps outfits (suit, quarter-zip, original clothes), widens a too-tight headshot, and makes before/after images for social posts. Also grades the source photo first and explains how to take a good one (distance, lens, light, framing). Use whenever someone sends a photo and asks for a headshot, profile picture, avatar, team photo, LinkedIn or X picture, "make this look professional", "fix the lighting", "put me on a blue background", "now do it with this person", "zoom it out", "put him in a suit", or asks how to take a photo for a headshot, whether a photo is good enough, or for a before and after of headshots, even if they never say "skill" or "headshot". Do NOT use for AI-generated people, ad creative, product photos or app screens.
---

# Headshots

The output is a photo of **this exact person**, as if a professional had taken it. Friends and family should see
better light and a better camera, and nothing else. Everything below serves that: the image model is used for
light, background, clothes and missing shoulders, and the approved face is pasted back over every later edit,
because each extra pass through a model drifts the face and shifts skin towards pink.

Needs macOS (Apple Vision, Xcode command line tools), Python 3.9+ with Pillow and numpy, Chrome for
before/afters, and a Gemini API key. No other installs. Commands below use:

```bash
S=<this skill's folder>/scripts
python3 -W ignore $S/hs.py --help
```

**First run:** if `~/.config/headshots/config.json` is missing, ask for the brand colour and write it (see
`scripts/config.py`): `{"brand_name": "acme-blue", "brand_color": "#2563EB", "key_command": []}`. The API key comes
from `GEMINI_API_KEY`, or from `key_command` (a secrets manager that runs the rest of the line). Never ask the user
to paste a key into the chat. Check the team's own notes too: they may already say which colour and key to use.

## The steps

Work in a fresh scratch folder, one per person.

### 1. Grade the source photo

```bash
python3 -W ignore $S/hs.py check photo.jpg
```

Look at the photo yourself too. Tell the user in one or two lines what limits it. Ask for the **original file**
if this is a screenshot or a cropped avatar (`mdfind -name IMG_1234` often finds it on their Mac).

- `GOOD` / `USABLE`: go on.
- `RETAKE`: say what's wrong and what a better photo would fix, send the short message from
  [references/source-photo-guide.md](references/source-photo-guide.md), and carry on with this photo unless
  they'd rather wait. A warped, blurry or half-hidden face can't be fixed later; bad light can.
- Black and white: hair, eye and skin colours would be guesses. Say so up front and ask for the real colours.

When someone only asks how to take the photo, or whether one is good enough, the guide is the whole answer.

### 2. Frame it square

```bash
python3 -W ignore $S/hs.py frame photo.jpg square.jpg
```

Head at the house size and spot (see "House framing"). It prints how much shoulder is missing, and fills the
corners of round avatars. Framing first means the model rebuilds missing shoulders in the same pass as the
relight, so nothing has to be widened afterwards.

### 3. Relight, then let the user pick

Say what it will cost before the first paid call. Fill in `assets/prompts/relight.txt`
([references/prompts.md](references/prompts.md) says how, and has the extra lines for padding, round crops and
black and white), then:

```bash
python3 $S/gen.py square.jpg relight.txt r --pro 3 --nb 2     # 5 takes, 1-3 minutes
python3 -W ignore $S/hs.py like square.jpg r_*.jpg            # face error, eye opening, brow gap, zoom
python3 -W ignore $S/hs.py sheet takes.jpg square.jpg r_*.jpg
python3 -W ignore $S/hs.py faces faces.jpg square.jpg r_*.jpg
```

Drop takes that are clearly someone else, changed the eyes, or added marks. **Send the sheet, say which you'd
use, and wait for the pick.** This is the one checkpoint worth the wait: in testing, two of five people's photos
were redone because the user came back with a different take ("this one looks the most like him"), and once three
takes measured within 1% of each other and only one looked right to the person in it. The number ranks takes;
someone who knows the face decides. Skip the wait if they said to just send them.

Flat result? Strengthen the LIGHT block (it's the part that gets ignored on a photo against a pale wall).

### 4. Backgrounds and outfits

Save the pick as `S.jpg` (4096 square, quality 97). Edit from it:

- **Same clothes:** `hs.py background white w.txt` and `hs.py background brand b.txt`, then one `--pro 1 --nb 1` each.
- **New outfit:** `outfit.txt` from the **white-background take**, `--pro 2 --nb 1` per outfit. Run `like`
  on every result: models love to zoom out to show a suit, and `ZOOMED OUT` takes can't be used.

Only change clothes that were asked for. If an outfit's colour wasn't given, ask or say what you picked. Recolour
with `recolour.txt` rather than redoing the outfit.

### 5. Finish

```bash
python3 -W ignore $S/hs.py finish S.jpg original --white w.jpg --brand b.jpg             # same clothes
python3 -W ignore $S/hs.py finish S.jpg suit --white suit.jpg --mode outfit --keep-blue  # navy tie stays blue
python3 -W ignore $S/hs.py finish S.jpg qzip --white navy.jpg --mode outfit --clothes keep
```

About 45 seconds each. It cuts the person out, matches the edit's colour back to the approved photo, pastes the
approved face (or the whole body, in `full` mode) over it and lands on the exact background colour. `--brand`
is optional: one white edit makes both colours and works well for short hair. For long, wavy or flyaway hair,
give it the brand-colour edit too.

### 6. Look once, send, save

Make one sheet of the finals and look at it at normal size. Fix something only if it's visible there. Then send
every file, name any small flaw you know about, and offer to fix it. Extra zoomed-in passes cost users time for
changes nobody saw.

- Keep JPG and PNG in `~/Pictures/headshots-<date>/<person>/` and copy the JPGs to `~/Downloads`.
- Say what was invented (shoulders, sleeves, colours from a black-and-white photo) and how close the face is.
- Never guess a name. Use the one given, or "person-2".
- These are AI-edited photos, and the models' invisible watermark (SynthID) stays in the pixels. Label them where
  a platform or employer asks for it, and don't present one as an untouched photo.

### 7. Before and after (when asked)

```bash
python3 -W ignore $S/before_after.py out alex=before.jpg,after.jpg sam=before.jpg,after.jpg
```

One person: 16:9, two squares. Several: post `all.jpg` (one 4:5 image, people as rows), because X crops the
first of three images to a tall slice.

## Widening a headshot that's already finished

Only when the old headshot must stay as it is: `hs.py widen` puts it on a wider white square,
`assets/prompts/outpaint.txt` fills the missing sleeves (`--pro 3 --nb 1`), and `hs.py widen-finish` keeps every
old pixel except a thin strip at the two seams. Don't change anything else about the photo.

## When the person says it isn't quite them

Full-frame passes redraw small features a little (teeth tidied, eyes wider, brows lower). If a pick is close but
off, don't re-roll the whole photo: use the face close-up pass in [references/lessons.md](references/lessons.md).

## House framing

So a team page lines up. Fractions of the square's side: head centre 50% across and 41% down; hair top to chin
58%; head width 43%; distance between the eyes 14%. Short or big hair shifts height and width, so `frame` averages
the three. Given a different reference photo, measure it with `head()` in `hs.py` and change `HOUSE`.

## Cost and time

About $0.90 for the relight round, $0.65 for two backgrounds, $0.55 per outfit (Gemini list prices, November
2026). Two backgrounds took 6 to 8 minutes a person; three outfits on both took 15 to 25, mostly waiting on the
models. The photo goes to Google's API, so only use photos of people who know about it.

## Read when needed

- [references/source-photo-guide.md](references/source-photo-guide.md): how to take the photo, why, a message to
  send people, and what can and can't be rescued
- [references/prompts.md](references/prompts.md): how to fill the prompts, the optional lines, wording that backfires
- [references/lessons.md](references/lessons.md): every failure seen so far with its fix and how the compositing
  works. Read it before changing a script or when a result looks off.
