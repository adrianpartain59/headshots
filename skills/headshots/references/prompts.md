# Filling in the prompts

Templates are in `assets/prompts/`. Copy one into the working folder and replace every `{PLACEHOLDER}`
(`gen.py` refuses to run while any is left). Describe what is really in the photo: the model uses these lines to
decide what not to touch, so a wrong one (eye colour, "clean-shaven") changes the person.

## relight.txt

| Placeholder | Example |
|---|---|
| `{SUBJECT}` | The man / The woman / The person |
| `{SOURCE_PROBLEMS}` | harsh frontal flash, shiny hot spots on forehead and nose, red cast, hard wall shadow |
| `{FACIAL_HAIR}` | Stubble stays as short, fine, light and sparse as in the source. / Clean-shaven: do not add stubble. |
| `{EYES}` | dark brown eye colour |
| `{EXPRESSION}` | the closed-mouth smile with the same one-sided lift / the open smile with the same visible teeth |
| `{HAIR}` | the messy light-brown hair with the same shape, volume and loose spikes |
| `{CLOTHES}` | black crew-neck t-shirt, thin silver chain |

Optional lines, pasted before FRAMING:

- **Padding** (`frame` said so): `The outer edges of the frame are smeared padding (left about 5%, right about 6%): rebuild them as the natural continuation of the shoulders and the backdrop, with believable proportions and no streaks.`
- **Circle** (round avatar): `The source was a circular avatar. The corners are a placeholder: rebuild them so the result is a normal full square photo with no trace of the circle. In the lower corners continue the shoulders and upper sleeves of the same clothing; upper corners are plain backdrop.`
- **Black and white**: `COLOUR: make it a natural full-colour photograph. {real hair, brow, eye, skin, clothing colours}. Realistic and neutral, no tint.` Ask for the real colours; if nobody answers, say they're guesses.
- **Another person in frame**: `Remove the other person's sleeve in the lower-left corner and continue the subject's own clothing there.`
- **Flat result last round**: replace "about 2:1" with "about 2.5:1" and add to `{SOURCE_PROBLEMS}`: `flat, grey, dull light`.

Already well lit? Use a gentler key ("open soft fill, about 1.8:1") and lead with quality, or it over-processes.

## outfit.txt

Write the garment as a photographer would see it. These worked:

- Suit: `a well-tailored dark charcoal wool suit jacket with notch lapels, a crisp white dress shirt with a neat spread collar, and a slim solid dark navy silk tie with a clean knot. No necklace visible, no pocket square.` (finish with `--mode outfit --keep-blue`)
- Quarter-zip: `a fine ribbed-knit quarter-zip sweater in black with a stand collar, half unzipped with a small silver zip pull, over a black crew-neck t-shirt. No necklace visible.`
- Navy for recolour.txt: `a dark navy blue (a deep, clearly blue navy, around RGB 30, 42, 78 in the lit areas, darker in the folds)`. Finish with `--clothes keep`, or the neutraliser turns it grey.

Always edit from the **white-background** take. The "CROP IS LOCKED" paragraph goes first. Without it one person's
four takes all came back 30% zoomed out (another person's were fine). With it, two of six held the crop, so run
3 takes per outfit, check `zoom`, and run more if none is at 1.00.

## Wording that backfires

| Don't write | What happens | Write |
|---|---|---|
| "real pores, freckles, individual stubble hairs" | Invented moles, dark spots, coarse drawn-on stubble | "only marks visible in the source", "fine, soft, sparse" |
| "keep the same wall" (relight) | Light stays as flat as the wall | light grey studio backdrop |
| "softbox" with no guard | A softbox appears in the corner | "nothing else in frame: no softbox, no equipment" |
| "no whitening" alone | Teeth keep the orange room light | "natural tooth colour" with a neutral white balance |
| "catchlights" without the eye colour | Eyes drift blue-grey | name the real eye colour |
| Nothing about crop on outfits | Zooms out to show the clothes | CROP IS LOCKED first and last |

## Models

Both are in `gen.py` and both have produced the winning take, so run both.

| | Nano Banana Pro (`gemini-3-pro-image`) | Nano Banana 2.1 (`gemini-nano-banana-2.1`) |
|---|---|---|
| Price at 4K | about $0.24 | about $0.08 |
| Better at | Skin, studio light, suits | Likeness of shape, hair edges, staying at the same zoom |
| Watch for | Softbox in frame, wider eyes | Darker freckles, coarser stubble |

Other image models were not tested.
