# Reference reels

Reels whose **editing style** you want new reels to borrow: pacing, text style, zoom, sound effects.
Content, footage and wording are never copied - only how it is cut.

1. Add a row to the table in [`links.md`](links.md): name, link, what you like about it, where to use it
   (it has filled-in examples).
2. Save the video as `workspace/references/<name>/video.mp4` (or ask Claude to fetch it with `research/style.py --url`,
   which needs `yt-dlp`; only download reels you are allowed to save).
3. Run `research/style.py <name>`. It writes `analysis.json` (shot count, average and median
   shot length, cuts in the first 3 s, pace by third, loudness) and `sheet.jpg` (one still per shot).
4. Claude reads those once and writes:
   - `style.md` - what to copy: pace, hook, text size/position/colours, emoji use, zooms, SFX, ending;
   - `look.json` - engine settings (`zoom`, `freeze_zoom`, `card_y`, `bg_blur`, `bg_dim`, `sfx`, `sfx_db`).
5. Use it in a reel with `"style": "<name>"` in `reel.json` (a reel's own `"look"` still overrides it).

Everything in this folder except this README and `links.md` is gitignored (videos, sheets, styles).
`links.md` is committed with the repo, so your links are public if you push it.
