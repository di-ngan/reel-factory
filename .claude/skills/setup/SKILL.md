---
name: setup
description: First-time setup of reel-factory on this computer - check and install the software, find fonts, set up the user's show (episodes folder, numbering, audio and subtitle tracks) or an originals channel, pick the default reel type and voice, then hand over to the content bank and the first reel. Use for "set up", "install", "get started", a freshly cloned repo, or when reel.py doctor reports problems.
---

# Set up reel-factory

Run from the project root. Be brief: one question at a time only where the answer changes what you do.

## 1. Software
- No `.venv`: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- `.venv/bin/python reel.py doctor`. It creates `.env`, `workspace/preferences.json` and the workspace folders, finds
  fonts, and marks problems `XX` (blocking) or `--` (only some reel types need it).
- Missing ffmpeg or Node: give the exact command doctor printed for this system. Installing system software changes
  the computer - ask before running it (e.g. `brew install ffmpeg`). Node is only needed for animated reels.
- No font found (usually Linux): suggest the distro's package (e.g. `fonts-dejavu`, `fonts-noto-color-emoji`), or
  ask for paths and write them to `config.local.json` under `"fonts"`.

## 2. What they will make
Ask: **commentary on a show they have episodes of**, **animated stories (no footage)**, **animated retellings of a
show**, or a mix. Then:
- **A show with episodes**: ask its name and the folder. `reel.py show new "<Name>" --episodes "<folder>"` (`--clips`
  for a folder of ready clips, `--tags` for hashtags). Show the user the printed numbering and tracks and ask
  whether they are right; fix wrong ones in `workspace/shows/<slug>/show.json` (`episodes`, `audio_tracks`,
  `under_track` = the language under the voice, `clear_track` = the one for lines played in the clear), or rename the
  files and `reel.py show scan`. Then `research/subs.py extract`; no subtitle track → `.srt` files can be dropped
  into the show's `subs/` as `EP01.srt` ...
- **A show without footage** (retellings only): `reel.py show new "<Name>"`.
- **No show**: `reel.py show new "Originals"`.
- Save `reel_type` in `workspace/preferences.json` (`commentary`, `story` or `retelling`; `reel.py kits` lists all).

## 3. Voice
ElevenLabs, or their own recordings (`"voice": "own"` in preferences - each reel's script comes with recording tips,
and `voice/tts.py <reel> --timing-only` times the mp3, no account needed). ElevenLabs: point them to README >
Account setup > ElevenLabs; they paste the key and voice ID into `.env` themselves - never ask for keys in chat, never
print them.

## 4. Posting (can wait)
YouTube and Instagram are only needed to publish; reels are finished mp4 files before that. Point to README >
Account setup when they want it; after they finish the console steps, run `auth/youtube.py` / `auth/instagram.py`
to confirm.

## 5. Hand over
`reel.py doctor` once more. Then offer the content bank (the `content-bank` skill) and, once it exists, the first
reel (`/make-reel`).
