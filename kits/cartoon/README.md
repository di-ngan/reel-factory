# Cartoon kit

The engine behind the animated reel types (`story`, `retelling`). Driven by `reelkit/cartoon.py`; the full workflow
is in [`.claude/skills/make-reel/types/cartoon.md`](../../.claude/skills/make-reel/types/cartoon.md).

- `engine/` - `main.js` (renderer, toon materials, ink pass, depth of field, grade), `paint.js` (painted textures),
  `roman.js` (cast: outfits, poses, faces, props), `motion.js` (cameras, easing, idle, walks), `index.html`.
  `setup` copies these into each reel's `web/`, where they are edited for that story.
- `vendor/toon.ts` - the Pen / head / face library, adapted from mromidev/claude-animated-shorts (MIT).
- `sound.py` - music beds and SFX synths; a reel's `audio.py` writes stems with it, and the mixer locks the levels.
- `render.mjs` - Playwright: `renderFrame(f)` → JPEG frames (`GPU=1` tries Metal/GPU, `RESUME=1` skips done frames).
- `example/soldier/` - "The Soldier Who Never Left": `story.js` (shot plan, cameras, lights, world, actors),
  `audio.py` (cue sheet), `stills.jpg`.

Downloaded at setup (gitignored): `lib/three.module.js` (three.js r160) and `node_modules/` (Playwright).
