# Cartoon kit

The engine behind the animated reel types (`story`, `retelling`). Driver: `build.py`; how Claude makes one:
[`GUIDE.md`](GUIDE.md).

```bash
.venv/bin/python reel.py new reel11 story      # reel.json with "kit": "cartoon"
.venv/bin/python reel.py reel11 setup          # then: stills 0,90,180 | render | audio | finish
```

reel.json: `{"kit": "cartoon", "type": "story" | "retelling", "title": "...", "voice": "voice.mp3"}`, plus
`"inspired_by"` for a retelling and optional `"music_db"` / `"sfx_db"` (default -6 = 50 % of the voice),
`"frames"` (default: voice length + `"tail"` 0.5 s) - the rest of the story lives in the reel's `web/` and `audio.py`.

- `engine/` - `main.js` (renderer, toon materials, ink pass, depth of field, grade), `paint.js` (painted textures),
  `roman.js` (cast: outfits, poses, faces, props), `motion.js` (cameras, easing, idle, walks), `index.html`.
  `setup` copies these into each reel's `web/`, where they are edited for that story.
- `vendor/toon.ts` - the Pen / head / face library, adapted from mromidev/claude-animated-shorts (MIT).
- `build.py` - stages: `setup` (copy engine + example, fetch three.js and Playwright), `stills`, `render`, `audio`
  (level-locked mix), `finish` (encode at -14 LUFS).
- `sound.py` - music beds and SFX synths; a reel's `audio.py` writes stems with it, and the mixer locks the levels.
- `render.mjs` - Playwright: `renderFrame(f)` → JPEG frames (`GPU=1` tries Metal/GPU, `RESUME=1` skips done frames).
- `example/soldier/` - "The Soldier Who Never Left": `story.js` (shot plan, cameras, lights, world, actors),
  `audio.py` (cue sheet), `stills.jpg`.

Downloaded at setup (gitignored): `lib/three.module.js` (three.js r160) and `node_modules/` (Playwright).
