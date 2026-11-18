# Animated reels (`story` and `retelling`)

Flat 2D bean-head cartoon characters (canvas-drawn cards with plum ink outlines) in a colourful 3D world with black ink
edges, painted textures, depth of field and gliding cameras. 1080x1920, 30 fps, as long as the voice (+0.5 s).
Kit: `reel_kits/cartoon/`, driven by `reel.py reelNN <stage>` (`build.py`). Worked example: the Soldier
(`reel_kits/cartoon/example/soldier/`: `story.js`, `audio.py`, `stills.jpg`).

## Brief (before STOP 1)
- **Story**: one surprising event with a physical cause and effect you can show; an everyman character; stakes that
  escalate; a twist in the last line. Settings buildable from simple shapes + painted textures (towns, bridges, ships,
  castles, deserts, labs, palaces). Verify real events with a web search; say "legend says" when disputed.
- **Retelling**: one scene, rule or debate from the series, acted out. Facts from the subtitles and the bank's
  Reference; the toon cast are new designs that suggest the role (outfit, hair colour, a prop), not the official look.
- Script formula: hook (the absurd fact, no setup) → setting in 1-2 lines (when, where, who, one concrete detail) →
  2-4 escalating beats, one exaggeration joke → the pivot ("But when...", with an everyday analogy) → the twist as the
  last words. Plain spoken English, 8-15 word sentences, numbers as words. Default 20-30 s (≈ 60-90 words with v3
  tags); 45-60 s allowed. Never describe what the viewer already sees.
- `brief.md`: title, hook, the script, word count and estimated length, and a one-paragraph visual plan (the 6-10
  shots). Caption + hashtags. **STOP 1**, then the voice (SKILL.md step 2). No captions unless the user asks.

## Shot plan (`work/PLAN.md`, before code)
- `reel.py new reelNN story` (or `retelling`) writes `reel.json` (`"kit": "cartoon"`). Set the title; add
  `"inspired_by"` for a retelling and optionally `"music_db"`/`"sfx_db"` (default −6 = 50 % of the voice).
- `reel.py reelNN setup` copies the engine, the example story and audio.py, fetches three.js
  and Playwright, and prints TOTAL (frames). Phrase and word times come from `timing.txt` / `words.json`.
- One row per shot: frames, words, setting, light, camera move, characters/poses/expressions, effects, SFX cue.
  Usually one shot per phrase; merge tiny phrases. Frame 0 is the hook image.
- Illustrate each sentence literally; props carry the jokes. Vary sizes: hook MCU → wide reveal → two-shot → insert on
  the key object → reaction close-up → environment move for the payoff.
- Light tells the beat: day = normal, golden = decline/drama, night-blue = explanation. A time jump gets a 6-frame white
  flash. The twist gets a sting (music stops, low hit, push-in with a slight roll); the payoff lands on the final word.
- Every visual reaction lands 0-3 frames before its word.

## Build (`web/`)
- **World** (`main.js`): keep the engine sections (toon materials, ink, `add`/`tbox`, sky, lights, cards, passes,
  `applyLight`, `drawActors`, `swapForNd`, `renderFrame`); replace only between `// ---------- world ----------` and
  `// ---------- cards ----------`, plus the story parts of `worldState()`. Build from primitives with painted canvas
  textures (`paint.js`: planks, beams, rotten wood, stone, moss, grass, dirt, plaster, roof tiles, marble, banners,
  carved text; add painters in the same flat, dark-seam style). `tbox` keeps texel density; 2-step toon gradient;
  fog = horizon colour. Backgrounds: half-buried sphere hills, cone mountains with snow caps, cypress/pine trees,
  distant houses, painted cloud billboards. Set pieces (collapses, doors, falls) are pivoted groups driven by 0..1
  progress from `worldAt(f)`, eased and staggered. Curved text uses planar UVs - check it isn't mirrored.
- **Cast** (`roman.js`, rebuilt into `toon.js` automatically): `romanFront(p, outfitKey, opts)` on a 600x1000 canvas,
  soles at y=975; a card is 2.25 m tall (1 unit = 0.00225 m). Add outfits to `OUTFITS` (tunic, cape, armor, helmet,
  hair, cap, beard, apron, dress, toga, ...) and props in the same style. Arm poses: hang, spear, point, up, wave, hip,
  belly, temple, lift, reach, cheek, shield, cross, thumb. Faces: the FACE set plus snore, stubborn, squint. Render a
  character test still before using new designs. Billboards yaw only, with a contact blob and alpha-tested shadow.
  Card keys from `q()`-rounded values. A detached part (a lifted helmet) is its own card aligned with `headCenter`.
- **Motion** (`motion.js`): `camFromKeys(keys, f, {kicks})` - smootherstep glides (18-45 f), `easeOut` reveals,
  Catmull-Rom `path` via-points. Nothing is static for 4+ frames: holds creep, `idle(f, seed)` on every character,
  `blinkAt` blinks, head bobs on stressed words. Actions: anticipation → `back` overshoot → `spring` settle; a stamp is a
  2-frame dip + dust puff + camera kick. Prefer continuous moves (pull-back, rack focus, crane, push-in); hard cut only
  on a place/time jump, with a flash. Something always moves (cloth, leaves, dust, water). DOF on close and medium
  shots (focus on the eyes, cInf 8-14 px); wides sharp; racks ~14 f.

## Look check (before the full render)
- `reel.py reelNN stills 0,45,120,...` (each shot's middle + key actions) → read
  `work/stills.jpg` once, send it to the user with a one-line shot summary.
- Traps: the vertical frame is narrow (half-width = d·tan(hfov/2), hfov = 2·atan(tan(vfov/2)·0.5625); at 4 m and fov 40
  that's ±0.8 m - stage characters in depth); railings or posts across faces; cameras inside walls, roofs or bushes;
  foreground props closer than ~2 m; the hero hidden behind a pillar; mirrored text; detached parts offset the wrong way;
  missing ink (sky counts as far depth, not a card).

## Sound
- `audio.py` is a cue sheet on the kit's `sound.py`: one bed (`march`, `calm`, `drone`, layered as needed) and SFX
  on events (whoosh on big moves, thunk on stamps, rumble + crash on collapses, scrape, ting on reveals, sting on the
  twist, creak, snap, splash, snore, leaves, water, cuckoo). Write stems only - never mix in audio.py.
- `reel.py reelNN audio` mixes at locked levels (music −6 dB vs voice gated RMS, SFX −6 dB with
  peaks ≤ 0.7× the voice peak) and prints them - confirm. Lock picture timing first; a timing change means re-running it.

## Render and finish
- `reel.py reelNN render` with Bash `run_in_background` (about 0.5-1.5 s per frame; it resumes if
  interrupted). Don't run other heavy jobs meanwhile.
- `... finish` → `out/<title>.mp4` at −14 LUFS; `qa/qa.py reelNN` (full-frame freeze/black, loudness); read
  `work/qa.jpg` once. Send the mp4 with a few lines per shot, then publish (SKILL.md step 3).

## Engine gotchas (keep if editing the engine)
`#include <fog_vertex>` / `<fog_fragment>` on their own lines. The final pass writes `linearToOutputTexel(...)`
(render targets are linear HalfFloat). The normal+depth pass swaps materials per mesh (world → normal/depth, cards →
alpha-tested mask, blobs/clouds/sky hidden, water flat), with fog and shadows off. Ink only on the near side of depth
jumps; creases from the normal dot; card neighbours skipped; ink fades ~140-520 m. DOF: 48 taps with a per-sample CoC
test. Sun from az/el per light preset; the shadow camera centres on each shot's action.
