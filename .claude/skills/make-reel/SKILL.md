---
name: make-reel
description: Make a vertical reel end to end with any installed reel kit (commentary over show footage, an original animated story, an animated retelling inspired by a series, or a kit added later) - then QA and (after approval) post to YouTube Shorts and Instagram Reels. Use for "make reel N", "next reel", "/make-reel", "start a series", a pasted reel idea or script, a voiceover mp3 for a planned reel, or "switch this series to ...".
---

# Make a reel

Python is `.venv/bin/python`; run everything from the project root. Each reel lives in `workspace/reels/reelNN/`
(next free number); every tool takes the short name (`reel10`). Keep the user's task list current.

## Project map
| Folder | What it does |
|---|---|
| `reel_kits/<kit>/` | one folder per kit: `kit.json` (its reel types), `GUIDE.md` (how to make it - follow it), engine, example |
| `reel.py` | runs a reel's kit: `reel.py kits`, `reel.py new reelNN <type>`, `reel.py reelNN [stage ...]` |
| `voice/tts.py` | ElevenLabs voice + word/phrase timing |
| `research/` | `subs.py` (subtitle search, fact-checks), `sheet.py` (contact sheets), `style.py` (reference reels) |
| `qa/qa.py` | checks a finished reel |
| `auth/`, `publish/` | YouTube/Instagram sign-in and token checks; posting |
| `workspace/` | the user's files: `reels/`, `media/`, `references/`, `subs/`, `content_bank.md`, `preferences.json` |

## Reel types
Run `reel.py kits` once per session: it lists every installed kit, the types it makes, what it needs and its guide.
Those types are the options - a kit someone adds to `reel_kits/` shows up there with no change to this skill.
Today: `commentary` (commentary kit; needs episodes in `workspace/media`), `story` and `retelling` (cartoon kit;
no footage). Start a reel's reel.json with `reel.py new reelNN <type>` (it records the kit), then follow that kit's
`GUIDE.md` from the brief onwards.

## Preferences (`workspace/preferences.json`, local; template `workspace/preferences.example.json`)
- **Before the first reel of a new series** (or the first reel ever, when `reel_type` is null): ask which type,
  with the types from `reel.py kits` as the options and the current default first. Save it under `series["<name>"]`
  (and as `reel_type` if it was the first). One question, then continue - never ask again for that series.
- Lookup order for a reel's type: what the user says now > `series[<series>]` > `reel_type`.
- "Switch <series> to animated", "default to commentary", "turn SFX on", "use style X": update the file, confirm in one line.
- Other keys: `voice` (`elevenlabs` or `own` - the user records/makes the mp3), `sfx`, `style` (a reference name),
  `length_s` (target range).

## Rules (all types)
- **Two approval stops, never skipped** (on an unattended run, stop there and report):
  1. the brief + tagged voiceover, before ElevenLabs credits or long renders;
  2. title, caption and hashtags, before anything is published (Instagram is public immediately).
- Facts are checked: show facts against the subtitles (`research/subs.py`); real-world stories with a web search,
  and anything disputed is framed as legend. Say what you corrected.
- Never edit or re-time the voice; the picture follows it.
- Original work only. A reference reel lends its *editing style*, never its script or shots. No real living people
  as characters, no brand mascots or logos. In a `retelling`, characters are new toon designs that nod to a role
  (a detective, a student with a notebook) - never copies of the official character designs, logos or footage.
- Spoiler tier from the bank: mid and endgame reels say "spoiler" in the first card or first line.

## Save credits (Claude usage and ElevenLabs)
- Text before images: subtitles, scripts and numbers are cheap; images are not. Look at each sheet once, keep notes
  in `work/notes.md`, and make sheets only of what is still in doubt (2 fps, a few seconds).
- One voice generation per reel, after approval. Self-made mp3: `voice/tts.py reelNN --timing-only`.
- Re-render only what changed. Cartoon: stills sheet first, full render only after it looks right (it takes minutes).
- A reference style is analysed once (`workspace/references/<name>/style.md`); later reels read the text.

## 1. Intake
Find the starting point from the message (ask only if unclear):
- **Nothing / "next reel"** → first `[ ]` idea in `workspace/content_bank.md` (create from `content_bank.example.md` there if missing).
  Bank empty or a new series → offer 10 ideas (below) and add the chosen one to the bank under its series.
- **An idea, beats or clips pasted** → the starting brief. **A script** → keep the wording, fix only facts.
- **A voiceover mp3** for a planned reel → save as `voice.mp3`, `voice/tts.py reelNN --timing-only`, then
  continue the kit guide from its voice step.
Resolve the type (Preferences), then follow the kit's `GUIDE.md`. Check `workspace/references/` for a style the user named.

**10 ideas** (commentary, retelling or story): each with a title (5-8 words, curiosity), the hook line (a surprising
fact stated flatly - no setup), three beats, the twist or closing question, spoiler tier or "true / legend", and the
2-3 big visual moments. Good ideas have a visible cause and effect and a payoff in the last line. Mix eras and themes
for stories; for series ideas, find the moments with `research/subs.py` before offering them.

## 2. Voice (all types)
- `vo.txt` = spoken words only, ElevenLabs v3 tags (`[serious]`, `[curious]`, `[dramatic pause]`), pauses as "...".
  No `<break>` tags. Numbers as words.
- After STOP 1: `voice/tts.py reelNN` → `voice.mp3`, `words.json`, `timing.txt`. Check the phrases match the
  script (tags must not be spoken). `voice: own` → give the script with recording tips and wait for the mp3.

## 3. Publish (all types)
- `post.json` from the brief: title (≤100 chars, hook + main hashtag), caption, 5-10 hashtags, `youtube.privacy`.
- Dry runs: `publish/youtube.py reelNN` and `publish/instagram.py reelNN`. Sign-in problems: `auth/youtube.py`,
  `auth/instagram.py`.
- **STOP 2:** show title, caption and hashtags; on yes, rerun both with `--confirm`. YouTube stays private until the
  API project is audited - tell the user to switch it in Studio.
- Mark the idea `[x]` in `workspace/content_bank.md` with the reel number and the links from `published.json`.

## Reference reels (when the user adds one)
Video in `workspace/references/<name>/video.mp4` (or `research/style.py --url <link> --name <name>` after the user confirms the
download). Run `research/style.py <name>`; read `analysis.json` and `sheet.jpg` once. Write
`style.md` (hook and first-3-s cuts, shot lengths and pace by third, text size/position/colours/emoji/words per card,
motion, SFX/music, ending) and `look.json` (engine settings for commentary: `zoom`, `freeze_zoom`, `card_y`, `bg_blur`,
`bg_dim`, `sfx`, `sfx_db`). For cartoons, apply `style.md` to the shot plan (shot length, camera energy, SFX density).

## A new kind of reel
If the user wants a reel no installed kit makes, build a new kit by `reel_kits/README.md`: everything goes inside
`reel_kits/<name>/`, it reuses `core/`, `voice/`, `qa/` and `publish/`, and `reel.py kits` must list it before the
first reel. Don't change other kits or the shared folders for one kit's needs without asking.
