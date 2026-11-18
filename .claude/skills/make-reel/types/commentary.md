# Commentary reels

Show footage in a 1080x720 window over a blurred fill, text cards above, voice on top of the show's own audio.
Engine: `reelkit/engine.py`. Format: `reels/README.md`. Full example: `examples/reel09/` (brief, reel.json, post).

## Brief (before STOP 1)
- Locate each clip: bank times are approximate (`≈` can be a minute off). Confirm with `subs.py search/show`, then a
  small sheet if needed. Episodes stay whole - the engine cuts from them; pre-made clips in `clips_dirs` work too.
- Write `brief.md`:
  - **Clips** A, B, C... - `EPnn m:ss-m:ss`, what happens, the key line.
  - **Beats** with target times: `[0:00-0:02] Hook. Clip B` → *On screen* (≤6 words, caps, key word red/yellow,
    optional emoji) → *Voiceover*. Then 3 beats, then the close: question card with 👇 and a tease of the next part.
  - **Editing**: show lines in the clear, graphics (meter, FAKE stamp, arrow, HUD, counter), split screens.
  - **Caption** + 5-10 hashtags from the bank list. **Fact check**: claim → subtitle line and time.
- Script: hook is sentence one. Plain spoken English, 8-15 word sentences, contractions; escalate each beat; the twist
  or question is the last line; don't narrate what the viewer sees. ~2.4 words/s with tags (45-60 s ≈ 110-145 words).
- A show line in the clear: end the sentence before it (a gap opens there).
- **STOP 1**: show `brief.md` and the tagged `vo.txt`. Then the voice (SKILL.md step 2).

## Shots and reel.json
- One shot per phrase. Exact source second from `subs.py show` + a 2 fps sheet of that moment
  (`tools/sheet.py EP10 240 8 --out reels/reelNN/work/s3.jpg`). Note picks in `work/notes.md`.
- Avoid fades (start 0.5 s in), faces at the frame edge (centre crop: 720 of 848 px), reused shots, text on a face at
  a meme moment.
- `reel.json`: cut times = phrase starts from `timing.txt`; show line in the clear = `gaps` entry in the pause before it
  + a cut on track `"en"` at +10-12 dB; end with `freeze` and the question card.
- Style and sound: `"style": "<name>"` (or `preferences.style`) applies `references/<name>/look.json` - follow its
  `style.md` too. `"look": {"sfx": true}` (or `preferences.sfx`) adds whoosh/hit/ting under the voice; extra cues with
  `"sfx": [[t, "whoosh"|"hit"|"ting"]]`.

## Render and QA
- Look check: `... -m reelkit.engine reels/reelNN text`, view 3-4 `frames_txt/tNNNN.png` at the busiest moments.
- `.venv/bin/python -m reelkit.engine reels/reelNN` (~1 min), then `tools/qa.py reels/reelNN`.
- Read `work/qa.jpg` once: dark/blank shots, cropped faces, cards on faces, wrong shot for a line. Re-render only the
  stage needed (`text`, `video`, `audio`, `finish`).
- Send the mp4 (SendUserFile) with a short shot table, then publish (SKILL.md step 3).
