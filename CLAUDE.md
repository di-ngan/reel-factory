# reel-factory

Vertical (1080x1920, 30 fps) reels for YouTube Shorts and Instagram Reels, about any show the user has (or none).
Skills: `/setup` (first run), `content-bank` (research a show into ideas + facts), `/make-reel` (the workflow and its
two approval stops). `reel.py doctor` checks the setup.

- Python: `.venv/bin/python` (numpy, pillow, certifi). Everything else is stdlib + ffmpeg; the cartoon kit needs Node 22.6+.
- `reel.py`: `doctor`, `show new|list|use|scan`, `kits`, `new <reel> <type>`, `<reel> [stage ...]` (runs the reel's kit).
- `reel_kits/<kit>/`: `kit.json`, `GUIDE.md` (how to make it), `README.md` (reel.json format), engine, example.
  Today: `commentary`; `cartoon` (types `story`, `retelling`). New kits follow `reel_kits/README.md`, inside their folder.
- `core/`: `common.py` (config.json + config.local.json, .env, `WORK`, `reel_dir()`, episode/clip lookup),
  `shows.py` (show folders, episode numbering, track detection), `fonts.py`, `kits.py`, `doctor.py`.
- `voice/tts.py` · `research/` (`subs.py`, `sheet.py`, `style.py`) · `qa/qa.py` · `auth/` · `publish/` (dry run unless `--confirm`)
- `workspace/` (gitignored except READMEs and templates): `shows/<show>/` (`show.json`, `content_bank.md`, `subs/`),
  `reels/<reel>/`, `media/`, `references/<name>/`, `preferences.json` (active show, reel type per series).
- A **show** is the source (an anime); a **series** is a recurring reel format inside its bank.
- Tools take short reel names (`reel10` = `workspace/reels/reel10`).
- Secrets live in `.env` and `secrets/` only. Never print or paste keys or tokens.
- House style (commentary): cuts 2 frames before the word; show audio -18 dB under the voice; key show lines in the
  clear (gap + English track); no text over faces at meme moments; end on a hold + question card; -14 LUFS.
