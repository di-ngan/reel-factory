# reel-factory

Vertical (1080x1920, 30 fps) Death Note commentary reels for YouTube Shorts and Instagram Reels.
Run `/make-reel` (skill in .claude/skills/make-reel) - it holds the whole workflow and its two approval stops.

- Python: `.venv/bin/python` (numpy, pillow). Everything else is stdlib + ffmpeg.
- `reelkit/engine.py` renders `reels/<id>/reel.json` (format in reels/README.md). `reelkit/common.py`: config, .env, episode lookup.
- `tools/`: `subs.py` (subtitle search, fact-checking), `tts.py` (ElevenLabs + word timings), `sheet.py` (contact sheets),
  `qa.py`, `publish_youtube.py`, `publish_instagram.py` (dry run unless `--confirm`).
- Episodes: `episodes_dir` in config.json (stream a:0 English, a:1 Japanese, s:0 English subs).
- Secrets live in `.env` and `secrets/` only. Never print or paste keys or tokens.
- House style: cuts 2 frames before the word; show audio -18 dB under the voice; key show lines in the clear
  (gap + English track); no text over faces at meme moments; end on a hold + question card; -14 LUFS.
