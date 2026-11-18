---
name: make-reel
description: Make a vertical anime commentary reel (built for Death Note) end to end - idea from content_bank.md or the user, fact-checked brief and voiceover, ElevenLabs voice, cuts straight from the episode files, QA, then (after approval) YouTube Shorts and Instagram Reels. Use for "make reel N", "next reel", "/make-reel", a pasted reel idea, or a voiceover mp3 for a planned reel.
---

# Make a reel

Python is `.venv/bin/python`; run tools from the project root. Work in `reels/reelNN/` (next free number).
Keep the user's task list current.

## Rules
- **Two approval stops, never skipped** (on an unattended run, stop there and report):
  1. the brief + tagged voiceover, before any ElevenLabs credits are spent;
  2. title, caption and hashtags, before anything is published (Instagram is public immediately).
- Facts and quotes come from the subtitles (`tools/subs.py`), never from memory or the bank alone.
  Rules the anime never shows go in on-screen text, not as a show clip. Say what you corrected.
- Never edit or re-time the voice. The picture follows it: cuts land 2 frames before their word (the engine does this).
- Original commentary only. A reference reel lends its *editing style*, never its script, footage choices or wording.
- Spoiler tier from the bank: mid and endgame reels say "spoiler" in the first card.

## Save credits (Claude usage and ElevenLabs)
- **Text before images.** Find moments with `subs.py search/show` (cheap). Make a contact sheet only for the few
  seconds you still need to see, at 2 fps, around the subtitle time. Never sheet a whole episode.
- **Read each image once**; note what you learned in `work/notes.md` instead of reopening it.
- Episodes stay whole: the engine cuts from them directly, so the user never needs to pre-clip.
  If the user already has clips (`clips_dirs`), use them as sources - they're just shorter episodes.
- **One voice generation per reel.** The script is approved first. For a small fix to a self-made mp3,
  re-time with `--timing-only` instead of regenerating.
- Re-render only the stage that changed (`... engine reels/reelNN video|audio|finish`).
- A style is analysed once (`references/<name>/style.md`); later reels read that text, not the video.

## 1. Intake
Work out where the user is starting, without asking if it's obvious from the message:
- **Nothing / "next reel"** → first `[ ]` idea in `content_bank.md` (make it from `content_bank.example.md` if
  missing). Bank empty → offer 10 new ideas (format below), append the chosen one to the bank.
- **An idea, beats or clips pasted** → use them as the starting brief.
- **A script** → skip to the brief, keep their wording except for factual fixes.
- **A voiceover mp3** for a planned reel → save it as `voice.mp3`, run `tools/tts.py reels/reelNN --timing-only`
  (aligns `vo.txt` to the audio, ~0.1-0.3 s), go to step 4.
Also check `references/` for a style the user named or `links.md` entries without a `style.md`.

**New ideas** (when needed): exactly 10, each with a title (5-8 words, curiosity), the hook line (a surprising fact
stated flatly, no setup), three beats, the closing question, spoiler tier, and 2-4 clips found with `subs.py`.
Prefer ideas with a visible cause and effect on screen and a twist in the last line.

## 2. Brief and voiceover
- Locate each clip: bank times are approximate (`≈` can be a minute off). Confirm with `subs.py`, then a small sheet.
- Write `brief.md` (model: `examples/reel09/brief.md`):
  - **Clips** A, B, C... - `EPnn m:ss-m:ss`, what happens, the key line.
  - **Beats** with target times: `[0:00-0:02] Hook. Clip B` → *On screen* (≤6 words, caps, key word red/yellow,
    optional emoji) → *Voiceover*. Then 3 beats, then the close: question card with 👇 and a tease of the next part.
  - **Editing**: show lines to play in the clear, graphics (meter, FAKE stamp, arrow, HUD, counter), split screens.
  - **Caption** + 5-10 hashtags from the bank list. **Fact check**: claim → subtitle line and time.
- Script craft: hook is sentence one (no "In this video"). Spoken, plain English, 8-15 word sentences, contractions.
  Escalate each beat; the twist or question is the last line. Don't narrate what the viewer already sees.
  Write numbers as words for TTS. ~2.4 words/s with tags → 45-60 s ≈ 110-145 words.
- If a show line plays in the clear, end the sentence before it (a gap opens there in step 4).
- `vo.txt` = spoken words only, ElevenLabs v3 tags (`[serious]`, `[curious]`, `[dramatic pause]`), pauses as "...".
  No `<break>` tags (not supported in v3).
- **STOP 1:** show the brief and the tagged voiceover; wait for approval.

## 3. Voice
- `tools/tts.py reels/reelNN` → `voice.mp3`, `words.json`, `timing.txt` (phrase and word start times).
- Check the phrase list matches the script (tags must not be spoken). User's own mp3: `--timing-only` (step 1).

## 4. Shots and reel.json
- One shot per phrase. For each, get the exact source second from `subs.py show` + a 2 fps sheet of that moment
  (`tools/sheet.py EP10 240 8 --out reels/reelNN/work/s3.jpg`). Note picks in `work/notes.md`.
- Avoid: fades (start 0.5 s in), faces at the frame edge (the clip is a centre crop, 720 of 848 px wide),
  reusing a shot, text over a face at a meme moment.
- Write `reel.json` (format: `reels/README.md`, full example: `examples/reel09/reel.json`):
  cut times = phrase starts from `timing.txt`; a show line in the clear = a `gaps` entry in the pause before it +
  a cut on track `"en"` at +10-12 dB; end with `freeze` and the question card.
- Style: `"style": "<name>"` applies `references/<name>/look.json`; apply its `style.md` too (pace, card wording).
  Without a reference, the house style is the default. Sound effects: `"look": {"sfx": true}` (whoosh on cards,
  hit on stamps, ting on meter drops, −8 dB under the voice) and `"sfx": [[t, "whoosh"|"hit"|"ting"]]` for extras.

## 5. Look check, render, QA
- Render the text layer first (`... engine reels/reelNN text`) and check 3-4 frames
  (`frames_txt/tNNNN.png`) at the busiest moments: card size, wrap, meter/HUD overlap.
- Full render (`.venv/bin/python -m reelkit.engine reels/reelNN`, about 1 min), then `tools/qa.py reels/reelNN`.
- Read `work/qa.jpg` once: dark or blank shots, faces cropped, cards on faces, wrong shot for the line. Fix and
  re-render only the stage needed.
- Send the mp4 (SendUserFile) with a short shot table.

## 6. Publish
- `post.json` from the brief: title (≤100 chars, hook + #DeathNote), caption, hashtags, `youtube.privacy`.
- Dry runs: `tools/publish_youtube.py reels/reelNN` and `tools/publish_instagram.py reels/reelNN`.
- **STOP 2:** show title, caption and hashtags; on yes, rerun both with `--confirm`.
  YouTube uploads stay private until the API project is audited - tell the user to switch it in Studio.
- Mark the idea `[x]` in `content_bank.md` with the reel number and the links from `published.json`.

## Reference reels (when the user adds one)
- Video in `references/<name>/video.mp4` (or `tools/style.py --url <link> --name <name>` after the user confirms
  the download). Run `tools/style.py references/<name>/video.mp4`; read `analysis.json` and `sheet.jpg` once.
- Write `style.md`: hook pattern and first-3-s cut count; average/median shot length and how pace changes by third;
  text size, position, colours, emoji, word count per card; zoom/motion; SFX and music; ending. Map what the engine
  can do into `look.json`; list the rest as manual notes (e.g. "cut on every rally hit").
