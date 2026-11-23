# Lessons from the first seven people (November 2026)

## How people want it run

- Relight first, then backgrounds and outfits. Never change the person.
- Show the relit takes and let them choose. For two of five people the choice differed from mine: once the closest
  by the numbers (0.7%), once the loosest (2.3%) because it looked right to someone who knows the face.
- A little checking is good; a lot is not. One look at normal size, send, list the flaws.
- Recrops, new backgrounds and downloads are local edits. Use `finish`, `frame` or a plain crop; don't generate again.
- Keep the outfit unless asked. When outfits are asked for, "original" counts as one of them.
- "Zoom it out, don't change anything" means exactly that: only missing sleeves may be new.
- A reference photo for framing may show someone else. Check whose headshot is being made before starting.

## What goes wrong, and the fix

| Symptom | Cause | Fix |
|---|---|---|
| Moles, freckles, wiry stubble that aren't real | Prompt asked for pores and individual hairs | The SKIN block in relight.txt |
| Flat, grey light after relighting | Pale wall kept; light block too polite | "Obvious that a professional lit this", 2 to 2.5:1, grey backdrop |
| Skin pinker or lighter after a background edit | Every edit does this (blue +7 to +17, up to +18 brighter) | `finish` pastes the approved pixels back and matches the rest |
| New black or charcoal clothes look purple, shirts lavender | Same shift, and there's no original to paste | `--clothes neutral` (default); `--keep-blue` for a navy tie |
| Suit or quarter-zip take is zoomed out | Model wants to show the outfit | CROP IS LOCKED; discard takes with zoom above 1.04 |
| Ears go grey, hair tips green, blue or olive | Edge colour correction spilling onto skin, or the backdrop showing through hair | `finish` keeps skin solid and gives hair edges the hair's own colour |
| Eyes 7 to 17% wider, brows lower: "uncanny", more intense | Every full-frame relight leans this way | `like` shows eye opening and brow gap; name the exact eye opening in the prompt; choose the take nearest 1.00 |
| Adding a second photo of the person as a reference | Pulls the expression and props from it | One photo in, only words for the rest |
| Asking to fix a take "to match the real photo" | Over-corrects (eyes nearly shut) | "Keep this take's eyes; fix only X" |
| Vision mask drops a collar or leaves grey in a hair tuft | Cutting straight from the relit photo, no flat-backdrop edit | Use the background edits and `finish` |
| Hair under the ear or a collar notch takes the backdrop colour | Dark pixels read as see-through on a mid-tone backdrop | Dark-solid rule in `cutout()` |
| Haze with a straight edge at the crown | A line in the old wall seen through the hair | Say so in the background prompt and take 3 more; pick the clean one |
| Light line along the bottom edge | Model's last rows | `finish` repeats row -15 |
| Teeth yellow in a warm room photo | Teeth kept the room's colour | Neutral white balance in the prompt; only fix by hand if still visible |
| Round-avatar corners show | Circle not filled | `frame` fills it; CIRCLE line in the prompt |
| API hangs or cuts off | Seen three times in one afternoon | `gen.py` retries three times |
| Text in the way of a 3-image X post | X's grid crops the first image | One 4:5 image (`before_after.py`) |

## How `finish` works

1. Edit photo E is the approved photo S on a flat backdrop. Apple Vision gives a person mask; each edge pixel's
   opacity comes from where its colour sits between the backdrop and the nearest solid part of the person.
2. Skin, clothes and (on a mid-tone backdrop) dark pixels inside the mask are forced solid.
3. Interior pixels are replaced with S: the whole body in `full` mode, only above the jaw in `outfit` mode.
4. What's left of E (edges, neck, new clothes) is colour-matched to S.
5. Hair edges get the hair's own hue from S, so no backdrop tint survives.
6. Everything is laid on the exact colour. Corners are checked and printed.

Tested on four people (messy blond, cropped brown, wavy neck-length, textured black) and one suit. The whole flow
(check, frame, relight, backgrounds, finish), `widen` and `before_after.py` were each run once from this skill's files.

## Numbers worth trusting

- Face error (`like`): 0.5 to 1.2% of the eye distance is normal. Over 2% deserves a careful look (one 2.3% take was still the user's favourite).
- Eye opening between 0.95 and 1.05. Wider than 1.08 reads as a different expression.
- Background or outfit edits should stay under 0.7% from S, zoom 1.00.
- The numbers don't see colour: check eye, hair and skin colour by eye.

## Face close-up pass (strictest likeness)

For a pick that is nearly right, or a source where the face is small. A model can only keep what it sees enough
pixels of: full-frame relights matched the original's eyes, teeth and nose at 0.95 to 0.98; an upscaled face tile
at 0.97 to 0.99, with the real tooth shapes (measured on one portrait).

1. Crop the face from the source (about 560px across there), upscale to 2048, run it with a **restore-only** prompt
   (no light change), both models.
2. Put that face's fine detail into the relit photo inside eyes, brows, nose, lips and hair only. Keep plain skin
   from the full-frame take: the tile invents specks and pores there.
3. Take the light from the full-frame relight, and pull the skin's overall colour and the iris colour back to the
   source.
4. Check eye opening and brow gap again (that one ended at 2.1% and 1.6%).

This one has no script yet.

## Not done yet

- Long hair, glasses, beards longer than stubble, darker skin, bald heads and headwear: not tried. Check edges and
  skin tone with extra care, and add what you learn here.
- Any second person in the frame beyond an arm or a shoulder.
