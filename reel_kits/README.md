# Reel kits

A kit is everything needed to turn a voiceover into a finished vertical video of one style. Each kit is one
folder here; nothing outside its folder needs to change to add one. `reel.py kits` lists what is installed.

| Kit | Reel types | Needs |
|---|---|---|
| [`commentary`](commentary/) | `commentary` - narration over show footage, text cards, graphics | episodes or clips |
| [`cartoon`](cartoon/) | `story`, `retelling` - 3D toon world, 2D cartoon cast, synthesized music and SFX | Node.js 22.6+ |

## What the rest of the project does for every kit
- **The skill** (`.claude/skills/make-reel`) finds the idea, writes and fact-checks the script, gets the voice
  approved, then hands over to the kit's `GUIDE.md`; after the render it runs QA and the posting steps.
- **`voice/tts.py`** makes `voice.mp3`, `words.json` (word starts) and `timing.txt` (phrases) in the reel folder.
- **`qa/qa.py`** checks `out/*.mp4` (loudness, peaks, frozen or black spans, a stills sheet).
- **`publish/`** posts `out/*.mp4` with `post.json`; **`auth/`** handles the sign-ins.
- **`core/common.py`** gives config (`CFG`), paths (`ROOT`, `WORK`), `reel_dir()`, `source()` for footage,
  `duration()` and `run()`.

So a kit only has to do one thing: **reel folder in, `out/<title>.mp4` out**.

## Adding a kit
```
reel_kits/<name>/
├── __init__.py        empty - makes the kit importable
├── kit.json           what it is (below)
├── GUIDE.md           how Claude makes this type: brief, shot plan, build, look check, render
├── README.md          for people: what it makes, reel.json fields, commands
├── <entry>.py         the renderer, run as `reel.py <reel> [stage ...]`
└── example/<reel>/    a finished example (small files only)
```

`kit.json`:
```jsonc
{
  "name": "<name>",                         // = folder name, written into reel.json "kit"
  "title": "One-line description",
  "types": {"<type>": "what the viewer gets"},   // the choices the skill offers; must be unique across kits
  "aliases": [],                            // optional older type names this kit also accepts
  "needs": ["what the user must have"],
  "entry": "<entry>",                       // module name: python -m reel_kits.<name>.<entry> <reel> [args]
  "stages": ["stage names, if any"],
  "guide": "GUIDE.md",
  "qa": "full",                             // "full" frame, or "clip" for the footage window only
  "example": "example/<reel>"
}
```

The entry script:
- takes the reel folder as its first argument (use `core.common.reel_dir(sys.argv[1])`) and optional stages after it;
- reads `reel.json` and `voice.mp3` from the folder; times are in the voice's timeline;
- writes intermediate files to `<reel>/work/` and the result to `<reel>/out/<title>.mp4` - 1080x1920, 30 fps,
  H.264 + AAC, −14 LUFS (`CFG["render"]`), so QA and posting work unchanged;
- puts `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` before `from core.common import ...`.

Downloads a kit fetches at setup go in its own `lib/` or `node_modules/` (gitignored for every kit). Keep the
user's files out of the kit: footage in `workspace/media`, reels in `workspace/reels`.

Check a new kit with `reel.py kits`, `reel.py new _test <type>`, a render, then `qa/qa.py _test`.
