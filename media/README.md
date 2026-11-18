# Media

Your own video files. They stay on your machine: everything here except this README and the empty folders is
gitignored, so footage is never committed or pushed. Only **commentary** reels need media; animated reels don't.

```
media/
  episodes/   full episodes, one file per episode
  clips/      optional: clips you already cut (used by name in reel.json "sources")
```

## Episodes

- Keep them **whole** - the engine cuts what it needs, so there is no need to pre-clip.
- Name them so the episode number can be found. The default pattern (`config.json` → `episode_glob`) is
  `*S01E{ep:02d}.mkv`, which matches e.g. `Death Note S01E07.mkv`. Change the pattern in `config.local.json`
  if your files are named differently, e.g. `"episode_glob": "*Episode {ep:02d}*.mp4"`.
- Best results: an English audio track, a Japanese audio track and English subtitles inside the file
  (`audio_tracks` and `subtitle_stream` in the config say which stream is which). Then build the subtitle index once:
  `.venv/bin/python tools/subs.py extract`.

## Already have the episodes somewhere else?

No need to move or copy them. Point the config at their folder in `config.local.json`:

```json
{ "episodes_dir": "/path/to/your/episodes", "clips_dirs": ["/path/to/your/clips"] }
```
