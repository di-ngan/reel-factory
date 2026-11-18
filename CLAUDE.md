# reel-factory

Vertical (1080x1920, 30 fps) reels for YouTube Shorts and Instagram Reels, built for Death Note. Three types:
commentary (show footage, `reelkit/engine.py`), animated story and animated retelling (`reelkit/cartoon.py` + `kits/cartoon/`).
The user's type per series lives in `preferences.json`.
Run `/make-reel` (skill in .claude/skills/make-reel) - it holds the whole workflow and its two approval stops.

- Python: `.venv/bin/python` (numpy, pillow, certifi). Everything else is stdlib + ffmpeg; animated reels also need Node 22.6+.
- `reelkit/engine.py` renders `reels/<id>/reel.json` (format in reels/README.md, example in examples/reel09).
  `reelkit/common.py`: config (config.json + config.local.json), .env, episode lookup.
- `tools/`: `subs.py` (subtitle search, fact-checking), `tts.py` (ElevenLabs + word timings), `sheet.py` (contact sheets),
  `qa.py`, `publish_youtube.py`, `publish_instagram.py` (dry run unless `--confirm`), `ig_token.py`.
- Episodes: `episodes_dir` in config (stream a:0 English, a:1 Japanese, s:0 English subs; see `audio_tracks`).
- Secrets live in `.env` and `secrets/` only. Never print or paste keys or tokens.
- `references/<name>/`: reference reels, `style.md` + `look.json` (used via `"style"` in reel.json); `tools/style.py`.
- reels/ (except README), references/ (except README), media/, subs/, config.local.json and content_bank.md are local and gitignored.
- House style: cuts 2 frames before the word; show audio -18 dB under the voice; key show lines in the clear
  (gap + English track); no text over faces at meme moments; end on a hold + question card; -14 LUFS.
