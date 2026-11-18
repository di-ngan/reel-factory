---
name: make-reel
description: Make a vertical Death Note commentary reel end to end - pick an idea from content_bank.md (or use the one the user gives), fact-check and write the voiceover, generate it with ElevenLabs, cut it from the episodes, QA it, and (after approval) post to YouTube Shorts and Instagram Reels. Use for "make reel N", "next reel", "/make-reel", or when the user pastes a reel idea.
---

# Make a reel

Work in `reels/reelNN/` (next free number). Python is `.venv/bin/python`. Run every tool from the project root.
Two hard stops need the user's yes in chat: **before generating the voice** (costs ElevenLabs credits) and
**before publishing** (public). Never skip them, even on a schedule - on an unattended run, stop at the gate and report.

## 1. Idea
- If the user gave an idea/beats/clips, use that. Otherwise take the first idea in `content_bank.md` marked `[ ]`
  (create it from `content_bank.example.md` if missing).
- Create `reels/reelNN/`.

## 2. Fact-check and script
- Check every claim and quote against the subtitles: `tools/subs.py search "<regex>"` and `tools/subs.py show <ep> <m:ss> <m:ss>`.
  The subtitles are the source of truth for wording; say what you corrected and why.
- Write `script.txt` (beats, on-screen text, footage notes with EP times) and `vo.txt` (only the spoken words,
  with ElevenLabs v3 tags like `[serious]`, `[curious]`; pauses with "..." - `<break>` tags do not work in v3).
- Target 45-60 s: about 2.4 words per second of spoken text.
- If a show line must play in the clear, end the sentence before it - a gap is opened there in step 5.
- **STOP: show the script to the user and wait for approval.**

## 3. Voice
- `tools/tts.py reels/reelNN` -> `voice.mp3`, `words.json`, `timing.txt` (phrase and word start times).
- If the user supplies their own mp3 instead: copy it to `voice.mp3` and run `tools/tts.py reels/reelNN --timing-only`.
- Check the phrase count matches the script (tags must not be spoken).

## 4. Shots
- Make sheets of the scenes: `tools/sheet.py EP10 240 55 --out reels/reelNN/work/s1.jpg`, then Read them.
  Labels are seconds into the episode. Prefer full episodes (`"EP10"`) over clip files.
- Pick one shot per phrase. Avoid: fades (start 0.5 s after), people at the frame edge (the clip is centre-cropped
  to 720 px wide of 848), reusing a shot. Find exact English line times with `subs.py show` and, if needed,
  an RMS envelope of track 0.

## 5. reel.json
Format: `reels/README.md`; a full example is `examples/reel09/reel.json`. Rules:
- Times are in the original `voice.mp3` timeline. Every cut starts at a phrase start (the engine lands it 2 frames early).
- Show line in the clear: add `[at, seconds]` to `gaps` inside the pause before it, and a cut with track `"en"` and +10-12 dB.
- Cards sit above the clip - never put text over a face at a meme moment. Max ~6 words, key word in R or Y.
- End with `freeze` (hold with slow push) and a question card with 👇.
- Optional graphics: `meter` (lifespan/suspicion %), `stamps` (FAKE), `arrow`, `hud`, `count` cards, `music`.

## 6. Render and QA
- `.venv/bin/python -m reelkit.engine reels/reelNN` (about 1 min), then `tools/qa.py reels/reelNN`.
- Read `work/qa.jpg` and fix: dark/blank shots, faces cropped out, cards covering faces, wrong shot for the line.
  Re-render only the stages needed (`... engine reels/reelNN video`, then `audio`, `finish`).
- Send the mp4 to the user (SendUserFile) with a shot table and the cards.

## 7. Publish
- Write `post.json`: title (<=100 chars), caption, 5-10 hashtags, `youtube.privacy`.
- Dry runs: `tools/publish_youtube.py reels/reelNN` and `tools/publish_instagram.py reels/reelNN`.
- **STOP: show the title, caption and hashtags and wait for the user's yes**, then rerun each with `--confirm`.
- Mark the idea `[x]` in `content_bank.md` with the reel number and links from `published.json`.
