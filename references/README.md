# Reference reels

Reels whose **editing style** you want new reels to borrow: pacing, text style, zoom, sound effects.
Content, footage and wording are never copied - only how it is cut.

1. Add the reel to `links.md` (one line: name, link, what you like about it), e.g.
   `- fast-cuts | https://www.instagram.com/reel/... | cuts every second, yellow keywords, whoosh on every card`
2. Save the video as `references/<name>/video.mp4` (or ask Claude to fetch it with `tools/style.py --url`,
   which needs `yt-dlp`; only download reels you are allowed to save).
3. Run `tools/style.py references/<name>/video.mp4`. It writes `analysis.json` (shot count, average and median
   shot length, cuts in the first 3 s, pace by third, loudness) and `sheet.jpg` (one still per shot).
4. Claude reads those once and writes:
   - `style.md` - what to copy: pace, hook, text size/position/colours, emoji use, zooms, SFX, ending;
   - `look.json` - engine settings (`zoom`, `freeze_zoom`, `card_y`, `bg_blur`, `bg_dim`, `sfx`, `sfx_db`).
5. Use it in a reel with `"style": "<name>"` in `reel.json` (a reel's own `"look"` still overrides it).

Everything in this folder except this README is gitignored.
