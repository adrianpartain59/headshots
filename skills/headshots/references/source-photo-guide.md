# Taking a good source photo

The relight fixes light, colour, noise, background and clothes. It does not fix **the face itself**: whatever
shape, sharpness, expression and angle the photo has is what every headshot will have. So the photo needs two
things above all: **taken from far enough away**, and **half-decent light**.

## Message to send someone (copy, paste)

> For your headshot, can you send me a new photo? Takes 5 minutes:
> 1. Have someone else take it, or prop the phone up and use the timer. No selfies.
> 2. Phone 5 to 6 feet away, back camera, zoomed to **2x**, at your eye level. Not 0.5x.
> 3. Stand facing a big window in daytime, lights and flash off. Plain wall a few feet behind you.
> 4. Waist up, with space above your hair and on both sides of your shoulders.
> 5. Look into the lens. Take 10 or so with the expression you want; I can't change it later.
> 6. Wear a plain top, hair how you like it, and wipe the lens first.
> 7. Send the **original file** (AirDrop, or a Files/Drive link). No screenshots, no crops, no filters.

## What matters, in order

**1. Distance (the one that can't be fixed).** Up close, the nose is much nearer the lens than the ears, so it
comes out big and the face narrow and stretched. At 12 inches (arm's-length selfie) the nose measures about 30%
larger than with no distortion; at 5 feet there is essentially none
([JAMA Facial Plastic Surgery, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5876805)). Portrait
research puts good distance at about 1.4 to 2 m, 4.5 to 6.5 feet
([arXiv 1905.07515](https://ar5iv.arxiv.org/html/1905.07515)).
- It is the distance that warps, not the lens. Step back, then zoom in (2x, or 3x from further) to fill the frame.
- Never 0.5x, and not the selfie camera at arm's length.
- Signs of a too-close photo: big nose, ears hidden or pulled back, forehead or chin bulging towards you.
- `hs.py check` works out the distance from the lens data when the file is an original. The best source so far was
  shot from about 6 feet at 2x on an ordinary phone, in an ordinary room.

**2. Half-decent light.** Soft, from in front and a little to one side, bright enough that the face isn't grainy.
- Best: face a large window, 3 to 6 feet back, daytime, no direct sun. Outside: open shade.
- Turn the room lights off if they're yellow; mixed light gives patchy skin.
- No flash: it puts shiny white spots on forehead, nose and cheeks, red skin, and a hard shadow on the wall.
- No window or lamp behind them, no ceiling light straight above (dark eye sockets).
- Flat and a bit dull is fine. Blown-out or nearly black is not: there's nothing there to rebuild.

**3. Enough pixels, in focus.** The head should be at least 900 pixels tall from hair to chin, and the eyes sharp.
Any recent phone does this from 6 feet at 2x. Screenshots, profile pictures and photos sent through chat apps
usually don't: at about 280 pixels the model made up the skin and hair detail.

**4. Room around the body.** Waist or mid-chest up, hair not cut off, both shoulders and some space outside them,
arms relaxed at the sides. A shoulder cut by the frame has to be invented. Nobody else's arm or hair in shot.

**5. The expression and pose they want to keep.** Eyes to the lens, camera at eye level, head straight or a small
natural tilt. A raised chin shows nostrils and a long neck in every version. Smile or not, choose now.

**6. Simple surroundings and clothes.** Plain wall that contrasts with the hair, 3 feet or more behind (no shadow
on it). Plain top without a logo. It ends up on white and on your brand colour, so avoid a white top and one close to your brand colour.
Glasses: tilt them slightly down so there's no window reflection.

**7. No processing.** Beauty filters off, portrait mode off (its fake blur eats hair edges), black and white off,
no edits, no AI upscaling (it leaves waxy skin and fuzzy hair). Wipe the lens. Take 10 or more.

Points 1 to 3 have a source above or decided the result in testing. The rest is standard portrait practice.

## How `check` grades it

| Line | Good | Warning | Retake |
|---|---|---|---|
| Head height | 700px+ (aim 900) | 350 to 700 | under 350 |
| Distance (originals only) | 4 ft+ (aim 5 to 6.5) | 2.3 to 4 ft | under 2.3 ft |
| Face brightness (0 to 255) | 85 to 205 | 60 to 85, 205 to 225 | outside that |
| Blown-out skin | under 2% | 2 to 8% | over 8% |
| One side brighter | up to 4.5:1 | 4.5 to 8:1 | over 8:1 |
| Sharpness | 5+ | 3 to 5 | under 3 |
| Shoulders to invent | under 3% | 3 to 35% | over 35% |

It also flags: no lens data, orange light, black and white, round crops, tilted heads, cut-off hair, two faces.
`RETAKE` means a better photo is worth asking for, not that this one can't be used.

## What each kind of source gave (seven people, November 2026)

| Source | Graded | What happened |
|---|---|---|
| iPhone, 2x, about 6 ft, room light, full body, 12 MP original | GOOD | One relight round, take 2 of 3. Nothing to rescue. |
| Studio suit portrait, 1024x1536 | not graded | Best kept closest by the face close-up pass; eye opening within 2.1%. |
| Square photo, already studio-lit, 1320px | USABLE | Closest faces (0.5%). Little left to improve: cleaner skin and hair. |
| Warm indoor photo, tight crop, someone else's arm in frame | USABLE | Good likeness (1%). Orange cast removed; about 12% of shoulder invented on each side. |
| Round avatar, colour, head 600px | USABLE | Good likeness (0.7%). Lower corners of the blazer invented. |
| Close frontal flash, 828px wide | RETAKE | Needed two relight rounds; the first came out flat. |
| Round black-and-white avatar, head 283px | RETAKE | Usable, but all colours guessed and fine detail invented. |

## What can and can't be rescued

| Rescued by the relight | Not rescued: ask for another photo |
|---|---|
| Dull, flat, orange or mixed light; flash shine; grain | Face warped from shooting too close |
| Messy background, other people at the edges | Blur, motion, closed eyes, hand or hair over the face |
| Shoulders cut off, round crops (invented, and say so) | Expression, gaze or chin angle they don't like |
| Clothes they don't want | Hair cut off at the top |
| Black and white, if you're told the real colours | Heavy beauty filter (the real face isn't in the file) |
