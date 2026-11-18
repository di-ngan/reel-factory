# reel-factory

Turn an idea into a finished, posted vertical reel: script, AI voiceover, picture, loudness-matched audio, QA,
then upload to **YouTube Shorts** and **Instagram Reels**.

## Reel types

Each style of reel is a **kit** in [`reel_kits/`](reel_kits/). You pick a type when you start a reel or a series, and
can switch any time. The kits included:

| Type | What you get | Needs |
|---|---|---|
| **Commentary** | narrated breakdown over show footage: text cards, meters, stamps, the show's audio under the voice | your episode files |
| **Animated story** | an original cartoon short: 2D bean-head characters in an inked, painted 3D world, gliding cameras, synthesized music and SFX | nothing |
| **Animated retelling** | the cartoon style applied to a series: a scene, rule or debate acted out by an original toon cast | nothing (subtitles help with facts) |

Want another style (slideshow, kinetic text, split-screen reactions...)? A kit is one folder with a `kit.json`, a
guide and a renderer - see [Adding a kit](#adding-a-kit). The voice, QA and posting steps are shared by every kit.

Nothing is tied to one show. Commentary works with any show you have as video files (subtitles help), the animated
types need no footage at all, and with no show in mind Claude writes a bank of original story ideas for you.

## Quick start with Claude Code

Install [Claude Code](https://claude.com/claude-code) (terminal, desktop app or IDE extension), then ask it:

> Clone https://github.com/di-ngan/reel-factory and set it up.

Open the cloned `reel-factory` folder in Claude Code and say **"set up"** (the [`setup`](.claude/skills/setup/SKILL.md)
skill). It checks ffmpeg, Python, Node and fonts on your computer, asks what you want to make, sets up your show
from your episodes folder (or none), and then:

1. **"Make a content bank for <show>"** - the [`content-bank`](.claude/skills/content-bank/SKILL.md) skill researches
   the show into facts, rules, characters, key moments with clip times and 30 reel ideas. No show? It writes
   original story ideas for animated reels.
2. **"Make the next reel"** - the [`make-reel`](.claude/skills/make-reel/SKILL.md) skill takes it from there.

Accounts (ElevenLabs, YouTube, Instagram) are only needed for the step that uses them - see
[Account setup](#account-setup). You can make finished reels with your own recorded voice and no accounts at all.

- **No pre-clipping.** The commentary engine cuts straight from the full episode files (pre-made clips work too).
- **One JSON file per reel.** You describe the edit (cuts, text cards, graphics) in `reel.json`, and the engine renders it.
- **Cuts land on the words.** ElevenLabs returns a timestamp for every word, so each shot changes just as its line starts.
- **Driven by Claude Code, no Claude API key needed.** A [Claude Code](https://claude.com/claude-code) skill runs the whole
  workflow in chat: it fact-checks the script against the subtitles, picks shots from contact sheets, writes `reel.json`,
  renders and checks the reel, and stops for your approval before anything costs money or goes public.
  Every step is also a plain command-line tool you can run yourself.

```
idea ─► script + fact-check ─► voiceover (ElevenLabs) ─► word timings ─► shot picking ─► reel.json
                 (subtitles)        ▲ approval                                              │
                                                                                            ▼
            Instagram Reels ◄─┬─ publish ◄─ approval ◄─ QA (length, LUFS, frozen/black) ◄─ render
            YouTube Shorts  ◄─┘
```

## Output

All types: 1080×1920 at 30 fps, H.264, AAC, **−14 LUFS** with a true-peak limiter, music and effects held at fixed
levels under the voice.

**Commentary**

- 1080×1920 at 30 fps, H.264 (CRF 16), AAC, mixed to **−14 LUFS** with a true-peak limiter.
- The episode fills a 1080×720 window over a blurred, darkened copy of itself, with a slow Ken Burns push on each shot.
- Bold pop-in text cards sit above the clip (stroke, shadow, colour emoji). They can carry counters, a meter
  (e.g. "L's suspicion 1%"), FAKE stamps, arrows and a map-style HUD.
- The show's own audio sits under the voice (original-language track, −18 dB). A key line can play in the clear on the English
  track: the engine opens a gap in the voiceover so the line has room.
- The reel ends on a frozen frame with a slow push-in and a question card, to prompt comments.
- Optional synthesized sound effects (whoosh on each card, hit on stamps, ting on meter drops), mixed 8 dB under the
  voice with peaks capped below it.
- Borrow the pacing and look of a reel you like: see [Reference reels](#reference-reels).

**Animated (story and retelling)**

- 2D cartoon characters drawn on canvas cards (outfits, poses, expressions, blinks, idle motion) in a 3D world built from
  primitives with painted textures, ink outlines, depth of field and graded light (day, golden, night-blue).
- Cameras glide on eased keyframes and curved paths; something always moves; impacts get a kick, the twist a sting.
- Music bed (march, calm piano, drone) and SFX (whoosh, thunk, rumble, crash, ting, sting, creak, snap, splash...) are
  synthesized per reel, music and SFX at 50 % of the voice, effect peaks capped below it.
- Rendered by three.js in headless Chromium - no GPU needed (about 0.5-1.5 s per frame).

## Requirements

| | |
|---|---|
| Python | 3.10+ |
| ffmpeg / ffprobe | with libx264 and AAC (`brew install ffmpeg` / `apt install ffmpeg`) |
| Python packages | `numpy`, `pillow`, `certifi` (everything else is the standard library) |
| Fonts | a heavy sans font for the cards and a colour emoji font. The defaults are the macOS system fonts; on Linux/Windows set your own in `config.local.json` (see [Configuration](#configuration)) |
| Episodes (commentary) | your own video files; best with the original-language audio, an English track and English subtitles (one audio track works too) |
| Node.js 22.6+ (animated) | for the cartoon renderer; `reel.py <reel> setup` installs Playwright's Chromium and fetches three.js once |
| Accounts (optional) | ElevenLabs (voice), Google Cloud (YouTube), Meta developer app (Instagram) |

No footage, subtitles or voices are included in this repository.

## Install

```bash
git clone https://github.com/di-ngan/reel-factory.git
cd reel-factory
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python reel.py doctor    # checks software and fonts, creates .env and your workspace files
```

Add the show you make reels about. Keep whole episodes (no clipping needed) wherever they are, or in
`workspace/media/episodes/` (gitignored - never commit video):

```bash
.venv/bin/python reel.py show new "My Show" --episodes "/path/to/episodes" --tags myshow,anime
.venv/bin/python research/subs.py extract          # subtitle index, used for fact-checks and clip times
```

`show new` numbers the episodes from their file names (`S01E07`, `1x07`, `Episode 7`, `- 07 [1080p]` ...) and finds
the audio and subtitle tracks by language; it prints both so you can check them. Each show gets a folder in
`workspace/shows/` for its settings, content bank and subtitles - start another show any time, and old reels keep
working. No footage? `reel.py show new "Originals"` holds ideas for animated stories.

## Configuration

`config.json` holds the defaults and is committed. Put anything specific to your machine in **`config.local.json`**,
which is gitignored. It overrides `config.json` key by key:

```json
{
  "fonts": {
    "text": "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
    "label": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "emoji": "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "emoji_size": 109
  }
}
```

| Key | What it does |
|---|---|
| `workspace` | folder for your own files (shows, reels, media, references); default `workspace` |
| `clips_dirs` | folders searched when a reel uses a clip file instead of `EPnn` (each show can add its own) |
| `look` | default look for every commentary reel (see [`reel_kits/commentary/README.md`](reel_kits/commentary/README.md)): zoom, card position, background blur/dim, sound effects |
| `fonts` | card font, contact-sheet label font, colour emoji font and its size. Found automatically on macOS, Windows and Linux (fontconfig); set them only to use other fonts |
| `tts` | ElevenLabs model (`eleven_v3`), output format and voice settings |
| `render` | frame size, fps, clip window position, show-audio level, loudness target |
| `youtube` | category (`1` = Film & Animation) and default privacy |
| `instagram` | Graph API version and host (see [Instagram](#instagram)) |

## Making a reel

### With Claude Code (recommended)

Open the project in Claude Code (the CLI, desktop app or IDE extension) and say *"make the next reel"*, paste an idea,
a script or a voiceover, or say *"start a new series about ..."*. (First time: *"set up"*, then *"make a content bank"* -
see [Quick start](#quick-start-with-claude-code).) The [`make-reel`](.claude/skills/make-reel/SKILL.md)
skill then:

1. **Asks the reel type** the first time (and once per new series), and remembers it in `workspace/preferences.json`
   (template: [`preferences.example.json`](workspace/preferences.example.json)). Say *"switch this series to animated"* or
   *"turn sound effects on"* any time.
2. **Takes the idea** from you, or the first unchecked item in the show's content bank
   (`workspace/shows/<show>/content_bank.md`); it can also pitch 10 new ones.
3. **Writes a brief and the voiceover**, fact-checked against the subtitles (or the web for real stories).
   Approval stop 1: nothing costs credits or long renders before you approve.
4. **Generates the voice** (or times your own mp3) and builds the reel with the type's kit:
   - *commentary*: shots from the episodes, `reel.json`, a ~1 minute render;
   - *animated*: shot plan, world, cast, cameras and sound cues, a stills sheet for you to check, then the full render.
5. **Runs QA** and fixes what it finds.
6. **Writes the title, caption and hashtags**. Approval stop 2: you approve them before anything is posted, then it
   uploads to YouTube and publishes to Instagram.

Kit guides: [commentary](reel_kits/commentary/GUIDE.md), [animated](reel_kits/cartoon/GUIDE.md).

### By hand (commentary)

Reels are folders in `workspace/reels/`; every command takes the short name.

```bash
.venv/bin/python reel.py new reel10 commentary           # workspace/reels/reel10/reel.json
$EDITOR workspace/reels/reel10/vo.txt                    # the spoken script (v3 tags like [serious] allowed)

.venv/bin/python voice/tts.py reel10                     # -> voice.mp3, words.json, timing.txt
.venv/bin/python research/sheet.py EP10 240 55           # contact sheet: EP10 from 4:00, 55 s, labelled in seconds
.venv/bin/python research/subs.py show 10 4:00 5:00      # exact line times

$EDITOR workspace/reels/reel10/reel.json                 # the edit (see below)
.venv/bin/python reel.py reel10                          # render -> workspace/reels/reel10/out/<title>.mp4
.venv/bin/python qa/qa.py reel10                         # checks + work/qa.jpg stills sheet

$EDITOR workspace/reels/reel10/post.json                 # title, caption, hashtags
.venv/bin/python publish/youtube.py reel10               # dry run
.venv/bin/python publish/youtube.py reel10 --confirm
.venv/bin/python publish/instagram.py reel10 --confirm
```

Already have a voiceover mp3, recorded yourself or made on the ElevenLabs website? Save it as `voice.mp3` in the reel
folder next to `vo.txt` and run `voice/tts.py reel10 --timing-only`. It aligns the script to the audio (sentence ends
to pauses, words by syllables; typically within 0.1-0.3 s) - no API call.

### reel.json in short

```jsonc
{
  "kit": "commentary",
  "title": "Reel10-My-Title",
  "voice": "voice.mp3",
  "sources": {"e": "EP10"},                 // "EPnn" = full episode, or a clip file name
  "cuts": [                                 // [voice time, source, source start s, ...]
    [0.00, "e", 154.0],
    [2.53, "e", 201.4]
  ],
  "cards": [{"t": 0, "spans": [["THIS IS", "W"], ["AN INTERROGATION", "R"]], "emoji": "🎾"}],
  "freeze": [40.2, "e", 469.0, 472.8, "ja"] // last shot: play, then hold to the end
}
```

Cut times are on the voiceover's timeline: copy them from `timing.txt`, and the engine lands each cut 2 frames early.
The full format (gaps for show lines, slow motion, counters, meters, stamps, arrows, HUD, music) is in
[`reel_kits/commentary/README.md`](reel_kits/commentary/README.md). A complete real reel is in
[`reel_kits/commentary/example/reel09`](reel_kits/commentary/example/reel09).

Re-render only what changed: `reel.py reel10 text|video|audio|finish`.

### By hand (animated)

```bash
.venv/bin/python reel.py new reel11 story                # or: retelling
.venv/bin/python voice/tts.py reel11                     # voice + word timings from vo.txt
.venv/bin/python reel.py reel11 setup                    # engine + example story into the reel's web/
$EDITOR workspace/reels/reel11/web/story.js workspace/reels/reel11/audio.py   # shots, world, cast, cameras; sound cues
.venv/bin/python reel.py reel11 stills 0,60,120,240      # look check -> work/stills.jpg
.venv/bin/python reel.py reel11 render                   # all frames (resumes if interrupted)
.venv/bin/python reel.py reel11 audio                    # stems -> level-locked mix
.venv/bin/python reel.py reel11 finish                   # -> out/<title>.mp4
.venv/bin/python qa/qa.py reel11
```

The worked example is [`reel_kits/cartoon/example/soldier`](reel_kits/cartoon/example/soldier) ("The Soldier Who Never Left").

## Commands

| Command | Purpose |
|---|---|
| `reel.py doctor` | check software, fonts, workspace, shows and accounts; says what to fix |
| `reel.py show new "<name>" [--episodes DIR] [--clips DIR ...] [--tags a,b]` | add a show (numbers the episodes, detects tracks) |
| `reel.py show list` / `use <show>` / `scan [<show>]` | list shows, switch the active one, re-read the episode files |
| `reel.py kits` | list installed kits, the reel types they make and what they need |
| `reel.py new <reel> <type>` | new reel folder in `workspace/reels/` set up for that type's kit |
| `reel.py <reel> [stage ...]` | render with the reel's kit (stages differ per kit) |
| `voice/tts.py <reel> [--voice ID] [--timing-only]` / `--list-voices` | ElevenLabs voiceover with word and phrase timings |
| `research/subs.py extract` / `search "<regex>" [--ep N]` / `show <ep> <m:ss> <m:ss>` | subtitle index for fact-checking and finding lines |
| `research/sheet.py <src> <start s> <dur s> [--fps N] [--out F]` | labelled contact sheet for picking shots |
| `research/style.py <name or video> [--name N]` / `--url <link> --name N` | measure a reference reel's pacing; writes `analysis.json` + a one-still-per-shot sheet |
| `qa/qa.py <reel>` | duration, loudness, peak, frozen and black frames; stills sheet; exits 1 on failure |
| `auth/youtube.py` | sign in to YouTube once (the uploader also does this the first time) |
| `auth/instagram.py` | check the Instagram token and fill in the account ID |
| `publish/youtube.py <reel> [--confirm]` | upload as a Short (dry run without `--confirm`) |
| `publish/instagram.py <reel> [--confirm]` | publish as a Reel (dry run without `--confirm`) |

`published.json` in each reel folder records the links, so a reel can't be posted twice.

## Adding a kit

Everything for a new style goes in one folder, `reel_kits/<name>/`: a `kit.json` (its reel types and needs), a
`GUIDE.md` (how Claude makes it), a `README.md`, the renderer and an example. The renderer's only job is
*reel folder in, `out/<title>.mp4` out* - the voice, QA and posting are shared. `reel.py kits` and the make-reel skill
pick the new types up on their own. The full contract is in [`reel_kits/README.md`](reel_kits/README.md); with Claude
Code you can just describe the style and ask for a new kit.

## Reference reels

Put reels whose editing you like in `workspace/references/` (links in
[`links.md`](workspace/references/links.md), videos as `workspace/references/<name>/video.mp4`). `research/style.py` measures shot lengths, the hook's cut count, pace across the reel and
loudness, and makes a one-still-per-shot sheet. Claude turns that into `style.md` (what to copy) and `look.json`
(engine settings), and a reel uses it with `"style": "<name>"`. Only the style is borrowed, never the content.
Details: [`workspace/references/README.md`](workspace/references/README.md).

## Saving credits

Claude Code usage and ElevenLabs characters are the two costs. The workflow is built to keep both low:

- **Subtitles before images.** Moments are found by searching the subtitles (text is cheap); contact sheets are made
  only for the few seconds still in doubt, and each image is read once.
- **Whole episodes, no pre-clipping.** Hand-clipping doesn't save Claude anything - the clips still have to be looked
  at to pick the exact frames - and it costs you time. Pre-made clips still work if you have them.
- **One voice generation per reel**, after the script is approved. Fixing a self-made mp3 needs only `--timing-only`.
- **Render stages separately**: re-run only `text`, `video`, `audio` or `finish` after a change.
- **Styles are analysed once** and reused as text.

## Account setup

All keys and tokens live in `.env` and `secrets/`, which are both gitignored. The tools never print them.

### ElevenLabs

1. Create an API key with **Text to Speech** access, plus **Voices: read** if you want `--list-voices`.
   Put it in `.env` as `ELEVENLABS_API_KEY`.
2. Put your voice's ID in `ELEVENLABS_VOICE_ID`. You can find it in the voice's menu on the website, or with `voice/tts.py --list-voices`.

> On the free plan, voices from the **Voice Library** are blocked through the API (`402 paid_plan_required`).
> Use one of ElevenLabs' built-in default voices, a voice you created yourself, or a paid plan. Or make the mp3 on
> the website and use `--timing-only`.

### YouTube

1. In [Google Cloud Console](https://console.cloud.google.com), create a project and enable **YouTube Data API v3**.
2. Set up the **OAuth consent screen** (External). Add your Google account as a **test user**, then **Publish app**:
   in Testing mode the sign-in expires every 7 days.
3. Create an OAuth client of type **Desktop app**. Download the JSON to `secrets/youtube_client.json`.
4. Sign in once with `auth/youtube.py`. It opens the browser. On the "unverified app" warning,
   choose *Advanced → Go to …*. The token is saved to `secrets/youtube_token.json`.

> Until Google audits your API project, **every upload made through the API is private**. Switch it to Public (or schedule it)
> in YouTube Studio, or apply for the free *YouTube API Services audit* to upload straight to public.

### Instagram

You need an Instagram **Business or Creator** account linked to a Facebook Page, and a Meta developer app. The
most reliable token for automation comes from a **system user** in a Meta business portfolio, and it never expires:

1. At [business.facebook.com/settings](https://business.facebook.com/settings), make sure the Instagram account and the
   app are in your business portfolio.
2. Under **Users → System users**, add a system user (Admin) and assign it the app, the Instagram account and the Page.
3. Click **Generate new token**. Choose the app, set expiry to **Never**, and tick `instagram_basic` and
   `instagram_content_publish` (`pages_show_list` and `pages_read_engagement` let the helper find the account by itself).
4. Put the token in `.env` as `INSTAGRAM_ACCESS_TOKEN`. If the Page isn't assigned, also paste the Instagram account ID
   from **Accounts → Instagram accounts** as `INSTAGRAM_USER_ID`.
5. Run `auth/instagram.py`. It confirms the account and saves its ID.

An app-dashboard token from *Instagram API → API setup with Unified login → Generate access tokens* also works:
set `"host": "graph.instagram.com"` under `instagram` in your config. Those tokens last 60 days and are renewed every
time you publish.

> Instagram has no private uploads: `--confirm` publishes publicly straight away. Always run the dry run first.

## Project layout

```
reel.py             one entry point: list kits, start a reel, render it with its kit
reel_kits/          one folder per reel style - add a kit here (README.md: the kit contract)
  commentary/       commentary over show footage: engine.py, GUIDE.md, README.md (reel.json format), example/reel09
  cartoon/          animated story + retelling: build.py, three.js toon engine, cast, sound synths, example/soldier
core/               shared code: config, .env, paths, shows (episode numbering, tracks), fonts, kits, doctor
voice/              tts.py - ElevenLabs voice and word timings
research/           subs.py (subtitles), sheet.py (contact sheets), style.py (reference reels)
qa/                 qa.py - checks a finished reel
auth/               youtube.py (sign-in), instagram.py (token check)
publish/            youtube.py, instagram.py - posting
.claude/skills/     setup, content-bank and make-reel: the Claude Code workflow (make-reel hands over to each kit's GUIDE.md)
workspace/          your own files (gitignored except the READMEs and templates):
  shows/            one folder per show: show.json, content_bank.md, subs/ (README.md)
  reels/            one folder per reel (README.md: what's in one, post.json)
  media/            episodes and clips
  references/       reference reels and their style profiles (links.md: your list)
  preferences.json  active show, reel type per series, voice, SFX, style (template preferences.example.json)
config.json         defaults; config.local.json overrides (gitignored)
.env, secrets/      keys and tokens (gitignored)
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `CERTIFICATE_VERIFY_FAILED` | python.org builds of Python ship without CA certificates. `certifi` (in requirements) fixes it, or run *Install Certificates.command* |
| ElevenLabs `402 paid_plan_required` | Voice Library voice on the free plan (see [ElevenLabs](#elevenlabs)) |
| ElevenLabs `401 missing_permissions` | the key lacks Text to Speech or Voices: read access |
| Google "Access blocked … has not completed the verification process" | add your account as a test user, or publish the consent screen |
| YouTube video is private | expected until the API project is audited |
| Instagram `ProcessingFailedError` | Instagram's upload assembly is flaky; the publisher retries with a fresh container automatically |
| Phrases split in the middle of words | breathy voices dip below the silence threshold; with word timings from `tts.py` this is handled |
| Cartoon render: `Executable doesn't exist` | run `.venv/bin/python reel.py <reel> setup` (installs Playwright's Chromium) |
| Emoji missing or huge on Linux | set `fonts.emoji` to Noto Color Emoji and `emoji_size` to 109 |

## License

[MIT](LICENSE). The license covers the code only, not any media you use it with.

Third party: the cartoon cast library `reel_kits/cartoon/vendor/toon.ts` is adapted from
[mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) (MIT, see
[its license](reel_kits/cartoon/vendor/LICENSE-claude-animated-shorts)); [three.js](https://threejs.org) (MIT) and
Playwright (Apache-2.0) are downloaded at setup, not bundled.

## Legal

This repository contains code only. You are responsible for having the right to use any footage, audio and voices
you process with it, and for following each platform's policies. Commentary and criticism may qualify as fair
use or fair dealing where you live, but that depends on how you use the material. This project is not affiliated with
or endorsed by the owners of any series, or by Google/YouTube, Meta/Instagram or ElevenLabs.
