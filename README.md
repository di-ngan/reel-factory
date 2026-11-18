# reel-factory

Turn an idea into a finished, posted vertical commentary reel: script, AI voiceover, cuts from the
episodes, on-screen text, loudness-matched audio, QA, then upload to **YouTube Shorts** and **Instagram Reels**.

It was built for Death Note commentary reels, but nothing in the engine is tied to one show: point it at any
series you have as video files with subtitles.

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

- 1080×1920 at 30 fps, H.264 (CRF 16), AAC, mixed to **−14 LUFS** with a true-peak limiter.
- The episode fills a 1080×720 window over a blurred, darkened copy of itself, with a slow Ken Burns push on each shot.
- Bold pop-in text cards sit above the clip (stroke, shadow, colour emoji). They can carry counters, a meter
  (e.g. "L's suspicion 1%"), FAKE stamps, arrows and a map-style HUD.
- The show's own audio sits under the voice (Japanese track, −18 dB). A key line can play in the clear on the English
  track: the engine opens a gap in the voiceover so the line has room.
- The reel ends on a frozen frame with a slow push-in and a question card, to prompt comments.

## Requirements

| | |
|---|---|
| Python | 3.10+ |
| ffmpeg / ffprobe | with libx264 and AAC (`brew install ffmpeg` / `apt install ffmpeg`) |
| Python packages | `numpy`, `pillow`, `certifi` (everything else is the standard library) |
| Fonts | a heavy sans font for the cards and a colour emoji font. The defaults are the macOS system fonts; on Linux/Windows set your own in `config.local.json` (see [Configuration](#configuration)) |
| Episodes | your own video files, ideally with an English audio track, a Japanese audio track and English subtitles |
| Accounts (optional) | ElevenLabs (voice), Google Cloud (YouTube), Meta developer app (Instagram) |

No footage, subtitles or voices are included in this repository.

## Install

```bash
git clone https://github.com/di-ngan/reel-factory.git
cd reel-factory
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env              # API keys go here (never committed)
```

Put your episodes in `media/episodes/` (or point `episodes_dir` at them, see below), then build the subtitle index:

```bash
.venv/bin/python tools/subs.py extract
```

## Configuration

`config.json` holds the defaults and is committed. Put anything specific to your machine in **`config.local.json`**,
which is gitignored. It overrides `config.json` key by key:

```json
{
  "episodes_dir": "/path/to/Death Note",
  "clips_dirs": ["/path/to/my/clips"],
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
| `episodes_dir`, `episode_glob` | where full episodes live and how episode *n* is named (`*S01E{ep:02d}.mkv`). Relative paths start at the project root |
| `clips_dirs` | extra folders searched when a reel uses a clip file instead of `EPnn` |
| `audio_tracks` | which audio stream is English and which is Japanese |
| `fonts` | card font, contact-sheet label font, colour emoji font and the size it renders at (Apple Color Emoji: 160, Noto Color Emoji: 109) |
| `tts` | ElevenLabs model (`eleven_v3`), output format and voice settings |
| `render` | frame size, fps, clip window position, show-audio level, loudness target |
| `youtube` | category (`1` = Film & Animation) and default privacy |
| `instagram` | Graph API version and host (see [Instagram](#instagram)) |

## Making a reel

### With Claude Code (recommended)

Open the project in Claude Code (the CLI, desktop app or IDE extension) and say *"make the next reel"*, or paste an
idea with your beats and clip notes. The [`make-reel`](.claude/skills/make-reel/SKILL.md) skill then:

1. **Takes the idea** from you, or the first unchecked item in `content_bank.md`. Copy
   [`content_bank.example.md`](content_bank.example.md) to `content_bank.md` to keep your own list.
2. **Fact-checks** every claim and quote against the subtitles and writes `script.txt` and `vo.txt`.
   Approval stop 1: you approve the script before any credits are spent.
3. **Generates the voice** with your ElevenLabs voice and saves the word timings.
4. **Picks shots** from contact sheets of the scenes, one per phrase.
5. **Writes `reel.json`**, renders it and runs QA. It looks at the stills and fixes dark shots, cropped faces and
   text covering a face.
6. **Writes the title, caption and hashtags**. Approval stop 2: you approve them before anything is posted, then it
   uploads to YouTube and publishes to Instagram.

### By hand

```bash
mkdir -p reels/reel10 && $EDITOR reels/reel10/vo.txt     # the spoken script (v3 tags like [serious] allowed)

.venv/bin/python tools/tts.py reels/reel10               # -> voice.mp3, words.json, timing.txt
.venv/bin/python tools/sheet.py EP10 240 55              # contact sheet: EP10 from 4:00, 55 s, labelled in seconds
.venv/bin/python tools/subs.py show 10 4:00 5:00         # exact line times

$EDITOR reels/reel10/reel.json                           # the edit (see below)
.venv/bin/python -m reelkit.engine reels/reel10          # render -> reels/reel10/out/<title>.mp4
.venv/bin/python tools/qa.py reels/reel10                # checks + work/qa.jpg stills sheet

$EDITOR reels/reel10/post.json                           # title, caption, hashtags
.venv/bin/python tools/publish_youtube.py reels/reel10           # dry run
.venv/bin/python tools/publish_youtube.py reels/reel10 --confirm
.venv/bin/python tools/publish_instagram.py reels/reel10 --confirm
```

Already have a voiceover mp3, recorded yourself or made on the ElevenLabs website? Save it as `reels/reel10/voice.mp3`
and run `tools/tts.py reels/reel10 --timing-only`. That times the phrases from the pauses, without word timings.

### reel.json in short

```jsonc
{
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
[`reels/README.md`](reels/README.md). A complete real reel is in [`examples/reel09`](examples/reel09).

Re-render only what changed: `python -m reelkit.engine reels/reel10 [text|video|audio|finish]`.

## Tools

| Command | Purpose |
|---|---|
| `tools/subs.py extract` / `search "<regex>" [--ep N]` / `show <ep> <m:ss> <m:ss>` | subtitle index for fact-checking and finding lines |
| `tools/tts.py <reel> [--voice ID] [--timing-only]` / `--list-voices` | ElevenLabs voiceover with word and phrase timings |
| `tools/sheet.py <src> <start s> <dur s> [--fps N] [--out F]` | labelled contact sheet for picking shots |
| `python -m reelkit.engine <reel> [stage]` | render a reel from `reel.json` |
| `tools/qa.py <reel>` | duration, loudness, peak, frozen and black frames; stills sheet; exits 1 on failure |
| `tools/publish_youtube.py <reel> [--confirm]` / `--auth` | upload as a Short (dry run without `--confirm`) |
| `tools/publish_instagram.py <reel> [--confirm]` | publish as a Reel (dry run without `--confirm`) |
| `tools/ig_token.py` | check the Instagram token and fill in the account ID |

`published.json` in each reel folder records the links, so a reel can't be posted twice.

## Account setup

All keys and tokens live in `.env` and `secrets/`, which are both gitignored. The tools never print them.

### ElevenLabs

1. Create an API key with **Text to Speech** access, plus **Voices: read** if you want `--list-voices`.
   Put it in `.env` as `ELEVENLABS_API_KEY`.
2. Put your voice's ID in `ELEVENLABS_VOICE_ID`. You can find it in the voice's menu on the website, or with `tools/tts.py --list-voices`.

> On the free plan, voices from the **Voice Library** are blocked through the API (`402 paid_plan_required`).
> Use one of ElevenLabs' built-in default voices, a voice you created yourself, or a paid plan. Or make the mp3 on
> the website and use `--timing-only`.

### YouTube

1. In [Google Cloud Console](https://console.cloud.google.com), create a project and enable **YouTube Data API v3**.
2. Set up the **OAuth consent screen** (External). Add your Google account as a **test user**, then **Publish app**:
   in Testing mode the sign-in expires every 7 days.
3. Create an OAuth client of type **Desktop app**. Download the JSON to `secrets/youtube_client.json`.
4. Sign in once with `tools/publish_youtube.py --auth`. It opens the browser. On the "unverified app" warning,
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
5. Run `tools/ig_token.py`. It confirms the account and saves its ID.

An app-dashboard token from *Instagram API → API setup with Unified login → Generate access tokens* also works:
set `"host": "graph.instagram.com"` under `instagram` in your config. Those tokens last 60 days and are renewed every
time you publish.

> Instagram has no private uploads: `--confirm` publishes publicly straight away. Always run the dry run first.

## Project layout

```
reelkit/            engine.py (renderer), common.py (config, .env, episode lookup)
tools/              subs, tts, sheet, qa, publish_youtube, publish_instagram, ig_token
.claude/skills/     make-reel: the Claude Code workflow with its two approval stops
examples/reel09/    a complete reel.json, post.json and script
reels/              your reels, one folder each (gitignored except README.md, the format reference)
subs/               extracted subtitles (gitignored)
config.json         defaults; config.local.json overrides (gitignored)
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
| Emoji missing or huge on Linux | set `fonts.emoji` to Noto Color Emoji and `emoji_size` to 109 |

## Legal

This repository contains code only. You are responsible for having the right to use any footage, audio and voices
you process with it, and for following each platform's policies. Commentary and criticism may qualify as fair
use or fair dealing where you live, but that depends on how you use the material. This project is not affiliated with
or endorsed by the owners of any series, or by Google/YouTube, Meta/Instagram or ElevenLabs.
