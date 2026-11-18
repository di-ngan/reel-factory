# Shows

One folder per show you make reels about (gitignored - your research stays yours):

```
shows/<show>/
  show.json         name, episodes folder and numbering, audio/subtitle tracks, hashtags (reel.py show new / scan)
  content_bank.md   reference facts and reel ideas (the content-bank skill writes it; template in
                    .claude/skills/content-bank/template.md)
  subs/             subtitles, EP01.srt ... (research/subs.py extract)
```

`reel.py show list` shows them; `reel.py show use <show>` picks the active one (saved in `preferences.json`). A reel
records its show in reel.json `"show"`, so old reels keep rendering after you move on to the next show. A show can
have no footage at all (`"episodes_dir": null`): an "Originals" show holds the ideas for animated stories.
