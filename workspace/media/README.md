# Media

Your own video files. They stay on your machine: everything here except this README and the empty folders is
gitignored, so footage is never committed or pushed. Only **commentary** reels need media; animated reels don't.

```
media/
  episodes/   full episodes, one file per episode (or keep them anywhere and point the show at that folder)
  clips/      optional: clips you already cut (used by name in reel.json "sources")
```

## Episodes

- Keep them **whole** - the engine cuts what it needs, so there is no need to pre-clip.
- Any common naming works: `Show S01E07.mkv`, `1x07`, `Episode 7 - Title.mp4`, `[Group] Show - 07 [1080p].mkv`.
  `reel.py show new "<Show>" --episodes <folder>` numbers them and prints the result to check. With one season,
  EP7 is episode 7; with several, EP numbers count across seasons in watch order (the list is in `show.json`).
- Audio and subtitle tracks are found by their language tags: the original language goes under the voice, English
  is used for lines played in the clear. One audio track is fine. No subtitles inside the files: put `.srt` files in
  `workspace/shows/<show>/subs/` as `EP01.srt`, `EP02.srt` ...; otherwise run `research/subs.py extract` once.
