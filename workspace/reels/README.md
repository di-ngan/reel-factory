Each reel lives in its own folder here (`workspace/reels/reel10/`). The folders are local work and are not
committed. Tools take the short name: `reel.py reel10`, `publish/youtube.py reel10`.

# What a reel folder holds
| File | Made by | What it is |
|---|---|---|
| `brief.md`, `script.txt`, `vo.txt` | Claude (make-reel skill) | the plan, the beats, the spoken words with v3 tags |
| `voice.mp3`, `words.json`, `timing.txt` | `voice/tts.py` | the voice and its phrase/word times |
| `reel.json` | Claude | the edit; its `"kit"` picks the kit that renders it - format in `reel_kits/<kit>/README.md` |
| `out/<title>.mp4` | the kit (`reel.py <reel>`) | the finished reel |
| `work/` | kits, `qa/qa.py`, `research/sheet.py` | intermediate files, contact sheets, `qa.jpg` |
| `post.json` | Claude | title, caption, hashtags (below) |
| `published.json` | `publish/*.py` | links once posted; stops a reel being posted twice |

# post.json
```json
{"title": "...", "caption": "...", "hashtags": ["DeathNote", "Anime"],
 "youtube": {"privacy": "private", "publish_at": null}, "instagram": {}}
```
`published.json` is written after posting and stops a reel being posted twice.
