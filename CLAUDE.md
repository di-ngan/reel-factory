# reel-factory

Vertical (1080x1920, 30 fps) reels for YouTube Shorts and Instagram Reels, built for Death Note. Each style of reel
is a **kit** in `reel_kits/` (today: `commentary`; `cartoon` for the `story` and `retelling` types). `reel.py kits`
lists them. Run `/make-reel` (skill in .claude/skills/make-reel) - it holds the workflow and its two approval stops.

- Python: `.venv/bin/python` (numpy, pillow, certifi). Everything else is stdlib + ffmpeg; the cartoon kit needs Node 22.6+.
- `reel.py`: `kits`, `new <reel> <type>`, `<reel> [stage ...]` (runs the kit named in the reel's reel.json).
- `reel_kits/<kit>/`: `kit.json`, `GUIDE.md` (how to make it), `README.md` (reel.json format), engine, example.
  New kits follow `reel_kits/README.md` and stay inside their folder.
- `core/`: `common.py` (config.json + config.local.json, .env, `WORK`, `reel_dir()`, episode/clip lookup), `kits.py`.
- `voice/tts.py` (ElevenLabs + word timings) · `research/` (`subs.py`, `sheet.py`, `style.py`) · `qa/qa.py`
- `auth/` (`youtube.py` sign-in, `instagram.py` token check) · `publish/` (`youtube.py`, `instagram.py`; dry run unless `--confirm`)
- `workspace/`: the user's files - `reels/<reel>/`, `media/`, `references/<name>/` (`style.md` + `look.json`), `subs/`,
  `content_bank.md`, `preferences.json` (reel type per series). Gitignored except READMEs and templates.
- Tools take short reel names (`reel10` = `workspace/reels/reel10`).
- Episodes: `episodes_dir` in config (stream a:0 English, a:1 Japanese, s:0 English subs; see `audio_tracks`).
- Secrets live in `.env` and `secrets/` only. Never print or paste keys or tokens.
- House style (commentary): cuts 2 frames before the word; show audio -18 dB under the voice; key show lines in the
  clear (gap + English track); no text over faces at meme moments; end on a hold + question card; -14 LUFS.
