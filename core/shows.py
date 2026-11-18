"""Shows: the series a channel makes reels about. Each one is a folder in workspace/shows/<slug>/:

  show.json         name, where the episodes are, their numbering, audio/subtitle tracks, hashtags
  content_bank.md   ideas + reference facts (written by the content-bank skill)
  subs/             subtitles extracted from the episodes (research/subs.py extract)

A show needs no footage: animated `story` channels use a show with "episodes_dir": null just to hold the bank.
The active show is `workspace/preferences.json` "show" (or the REEL_SHOW env var); a reel's reel.json "show" wins.

Episode numbers: with one season EPn is episode n; with several, EPn counts in watch order across seasons
(S01E01 = EP1 ... S02E01 = EP13 after a 12-episode season). show.json lists each EPn with its file.
"""
import json, os, re, subprocess
from pathlib import Path
from core.common import CFG, WORK

SHOWS = WORK / "shows"
VIDEO = {".mkv", ".mp4", ".m4v", ".mov", ".avi", ".webm", ".ts"}
PATTERNS = [                                     # tried in order; the first that numbers most files wins
    re.compile(r"[Ss](\d{1,2})[ ._-]*[Ee](\d{1,4})"),          # S01E05, s1e5, S01.E05
    re.compile(r"(\d{1,2})x(\d{1,3})\b"),                       # 1x05
    re.compile(r"(?i)\b(?:ep|episode|e)[ ._-]*(\d{1,4})\b"),    # EP05, Episode 5, E05
    re.compile(r"(?:^|[ ._\[-])(\d{1,4})(?:v\d)?(?=[ ._\]-]|$)"),   # "05 - Title", "[Group] Show - 05 [1080p]"
]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def prefs():
    p = WORK / "preferences.json"
    return json.loads(p.read_text()) if p.exists() else {}


def active_slug():
    s = os.environ.get("REEL_SHOW") or prefs().get("show")
    if s:
        return s
    found = sorted(p.parent.name for p in SHOWS.glob("*/show.json"))
    return found[0] if len(found) == 1 else None


def load(slug=None):
    slug = slug or active_slug()
    if not slug:
        return None
    f = SHOWS / slug / "show.json"
    if not f.exists():
        raise SystemExit(f"No show '{slug}' (expected {f}). Shows: {', '.join(all_slugs()) or 'none'} - "
                         "create one with: reel.py show new \"<name>\" --episodes <folder>")
    s = json.loads(f.read_text())
    s["slug"], s["dir"] = slug, f.parent
    return s


def all_slugs():
    return sorted(p.parent.name for p in SHOWS.glob("*/show.json"))


def save(s):
    d = SHOWS / s["slug"]
    d.mkdir(parents=True, exist_ok=True)
    out = {k: v for k, v in s.items() if k not in ("dir", "slug")}
    (d / "show.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")


def activate(slug=None):
    """Point the shared config (episode lookup, clips, tracks) at a show. Returns the show or None."""
    s = load(slug)
    if not s:
        return None
    CFG["show"] = s
    if s.get("episodes_dir"):
        CFG["episodes_dir"] = s["episodes_dir"]
    CFG["clips_dirs"] = s.get("clips_dirs", []) + [d for d in CFG["clips_dirs"] if d not in s.get("clips_dirs", [])]
    for k in ("audio_tracks", "under_track", "clear_track", "subtitle_stream"):
        if k in s:
            CFG[k] = s[k]
    return s


def for_reel(folder):
    """Activate the reel's show (reel.json "show", else the active show)."""
    rj = Path(folder) / "reel.json"
    slug = json.loads(rj.read_text()).get("show") if rj.exists() else None
    return activate(slug)


# ---------- detection (used when a show is created or rescanned) ----------

def scan(folder):
    """Number the episode files in watch order. Returns [[n, label, file name], ...]."""
    files = sorted(p.name for p in Path(folder).iterdir() if p.suffix.lower() in VIDEO and not p.name.startswith("."))
    best = []
    for rx in PATTERNS:
        keyed = []
        for f in files:
            m = rx.search(Path(f).stem.replace("_", " ") if rx is PATTERNS[3] else f)
            if m:
                g = [int(x) for x in m.groups()]
                keyed.append(((g[0], g[1]) if len(g) == 2 else (1, g[0]), f))
        if len(keyed) > len(best):
            best = keyed
        if len(keyed) == len(files):
            break
    best = sorted(set(best))
    seasons = {k[0] for k, _ in best}
    out = []
    for i, ((se, ep), f) in enumerate(best, 1):       # one season: EPn = episode n; several: watch order
        out.append([i, f"S{se:02d}E{ep:02d}", f] if len(seasons) > 1 else [ep, f"E{ep:02d}", f])
    return out


def tracks(video):
    """Audio and subtitle streams with their language tags."""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:stream_tags=language,title",
                                   "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout)
    a, s = [], []
    for st in j.get("streams", []):
        lang = (st.get("tags", {}).get("language") or "und").lower()[:3]
        (a if st["codec_type"] == "audio" else s if st["codec_type"] == "subtitle" else []).append(lang)
    return a, s


ISO = {"eng": "en", "jpn": "ja", "kor": "ko", "chi": "zh", "zho": "zh", "spa": "es", "fra": "fr", "fre": "fr",
       "ger": "de", "deu": "de", "ita": "it", "por": "pt", "rus": "ru", "hin": "hi", "ara": "ar", "tha": "th"}


def detect_tracks(video, original=None):
    """Name the audio tracks by language and pick the one under the voice (the original language) and the one
    for lines in the clear (English). An untagged track next to a tagged foreign one is taken as English."""
    audio, subs = tracks(video)
    names = {}
    for i, lang in enumerate(audio):
        names.setdefault(ISO.get(lang, lang[:2] if len(lang) == 2 else lang), i)
    if not names:
        names = {"orig": 0}
    foreign = [k for k in names if k not in ("en", "und")]
    if "en" not in names and "und" in names and foreign:
        names["en"] = names.pop("und")
    clear = "en" if "en" in names else next(iter(names))
    under = original if original in names else (foreign[0] if foreign else clear)
    sub = next((i for i, l in enumerate(subs) if ISO.get(l, l) == "en"), 0 if subs else None)
    return {"audio_tracks": names, "under_track": under, "clear_track": clear, "subtitle_stream": sub}


def create(name, episodes=None, clips=(), hashtags=()):
    slug = slugify(name)
    if (SHOWS / slug / "show.json").exists():
        raise SystemExit(f"Show '{slug}' already exists - use: reel.py show scan {slug}")
    s = {"name": name, "slug": slug, "episodes_dir": str(Path(episodes).resolve()) if episodes else None,
         "clips_dirs": [str(Path(c).resolve()) for c in clips], "hashtags": list(hashtags)}
    if episodes:
        rescan(s)
    save(s)
    return s


def rescan(s):
    eps = scan(s["episodes_dir"])
    if not eps:
        raise SystemExit(f"No video files with episode numbers in {s['episodes_dir']}")
    s["episodes"] = eps
    s.update(detect_tracks(Path(s["episodes_dir"]) / eps[0][2], s.get("under_track")))
    return s
