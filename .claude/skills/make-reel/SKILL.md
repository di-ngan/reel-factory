---
name: make-reel
description: Make a vertical reel end to end in one of three types - commentary over show footage, an original animated story, or an animated retelling inspired by a series - then QA and (after approval) post to YouTube Shorts and Instagram Reels. Use for "make reel N", "next reel", "/make-reel", "start a series", a pasted reel idea or script, a voiceover mp3 for a planned reel, or "switch this series to ...".
---

# Make a reel

Python is `.venv/bin/python`; run tools from the project root. Each reel lives in `reels/reelNN/` (next free number).
Keep the user's task list current.

## Reel types
| Type | What it is | Needs | Guide |
|---|---|---|---|
| `commentary` | narrated breakdown over show footage, text cards, graphics | episodes in `media/` | `types/commentary.md` |
| `story` | original animated short: 3D toon world, cartoon cast, music + SFX | nothing | `types/cartoon.md` |
| `retelling` | animated short inspired by a series: its scenes, rules or debates acted by an original toon cast | subtitles help for facts; no footage | `types/cartoon.md` |

`story` and `retelling` share the cartoon engine (`reel.json` `"type": "cartoon"`, plus `"inspired_by"` for a retelling).

## Preferences (`preferences.json`, local; template `preferences.example.json`)
- **Before the first reel of a new series** (or the first reel ever, when `reel_type` is null): ask which type,
  with the table above as the options and the current default first. Save it under `series["<name>"]`
  (and as `reel_type` if it was the first). One question, then continue - never ask again for that series.
- Lookup order for a reel's type: what the user says now > `series[<series>]` > `reel_type`.
- "Switch <series> to animated", "default to commentary", "turn SFX on", "use style X": update the file, confirm in one line.
- Other keys: `voice` (`elevenlabs` or `own` - the user records/makes the mp3), `sfx`, `style` (a reference name),
  `length_s` (target range).

## Rules (all types)
- **Two approval stops, never skipped** (on an unattended run, stop there and report):
  1. the brief + tagged voiceover, before ElevenLabs credits or long renders;
  2. title, caption and hashtags, before anything is published (Instagram is public immediately).
- Facts are checked: show facts against the subtitles (`tools/subs.py`); real-world stories with a web search,
  and anything disputed is framed as legend. Say what you corrected.
- Never edit or re-time the voice; the picture follows it.
- Original work only. A reference reel lends its *editing style*, never its script or shots. No real living people
  as characters, no brand mascots or logos. In a `retelling`, characters are new toon designs that nod to a role
  (a detective, a student with a notebook) - never copies of the official character designs, logos or footage.
- Spoiler tier from the bank: mid and endgame reels say "spoiler" in the first card or first line.

## Save credits (Claude usage and ElevenLabs)
- Text before images: subtitles, scripts and numbers are cheap; images are not. Look at each sheet once, keep notes
  in `work/notes.md`, and make sheets only of what is still in doubt (2 fps, a few seconds).
- One voice generation per reel, after approval. Self-made mp3: `tools/tts.py reels/reelNN --timing-only`.
- Re-render only what changed. Cartoon: stills sheet first, full render only after it looks right (it takes minutes).
- A reference style is analysed once (`references/<name>/style.md`); later reels read the text.

## 1. Intake
Find the starting point from the message (ask only if unclear):
- **Nothing / "next reel"** → first `[ ]` idea in `content_bank.md` (create from `content_bank.example.md` if missing).
  Bank empty or a new series → offer 10 ideas (below) and add the chosen one to the bank under its series.
- **An idea, beats or clips pasted** → the starting brief. **A script** → keep the wording, fix only facts.
- **A voiceover mp3** for a planned reel → save as `voice.mp3`, `tools/tts.py reels/reelNN --timing-only`, then
  continue the type guide from its voice step.
Resolve the type (Preferences), then follow the type guide. Check `references/` for a style the user named.

**10 ideas** (commentary, retelling or story): each with a title (5-8 words, curiosity), the hook line (a surprising
fact stated flatly - no setup), three beats, the twist or closing question, spoiler tier or "true / legend", and the
2-3 big visual moments. Good ideas have a visible cause and effect and a payoff in the last line. Mix eras and themes
for stories; for series ideas, find the moments with `subs.py` before offering them.

## 2. Voice (all types)
- `vo.txt` = spoken words only, ElevenLabs v3 tags (`[serious]`, `[curious]`, `[dramatic pause]`), pauses as "...".
  No `<break>` tags. Numbers as words.
- After STOP 1: `tools/tts.py reels/reelNN` → `voice.mp3`, `words.json`, `timing.txt`. Check the phrases match the
  script (tags must not be spoken). `voice: own` → give the script with recording tips and wait for the mp3.

## 3. Publish (all types)
- `post.json` from the brief: title (≤100 chars, hook + main hashtag), caption, 5-10 hashtags, `youtube.privacy`.
- Dry runs: `tools/publish_youtube.py reels/reelNN` and `tools/publish_instagram.py reels/reelNN`.
- **STOP 2:** show title, caption and hashtags; on yes, rerun both with `--confirm`. YouTube stays private until the
  API project is audited - tell the user to switch it in Studio.
- Mark the idea `[x]` in `content_bank.md` with the reel number and the links from `published.json`.

## Reference reels (when the user adds one)
Video in `references/<name>/video.mp4` (or `tools/style.py --url <link> --name <name>` after the user confirms the
download). Run `tools/style.py references/<name>/video.mp4`; read `analysis.json` and `sheet.jpg` once. Write
`style.md` (hook and first-3-s cuts, shot lengths and pace by third, text size/position/colours/emoji/words per card,
motion, SFX/music, ending) and `look.json` (engine settings for commentary: `zoom`, `freeze_zoom`, `card_y`, `bg_blur`,
`bg_dim`, `sfx`, `sfx_db`). For cartoons, apply `style.md` to the shot plan (shot length, camera energy, SFX density).
