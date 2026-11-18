"""reel.py doctor - check this computer and the project setup, and say exactly what to do about anything missing.
Never prints keys or tokens - only whether they are set. Creates the workspace files that are copied from templates.
Exit code 0 when everything needed for at least one reel type is in place.
"""
import json, os, platform, re, shutil, subprocess, sys
from core.common import CFG, ROOT, WORK, load_env
from core import shows
from core.kits import all_kits

OK, WARN, BAD = "ok  ", "--  ", "XX  "
OSN = {"Darwin": "mac", "Linux": "linux", "Windows": "windows"}.get(platform.system(), "linux")
INSTALL = {
    "ffmpeg": {"mac": "brew install ffmpeg", "linux": "sudo apt install ffmpeg   (or your distro's package)",
               "windows": "winget install Gyan.FFmpeg"},
    "node": {"mac": "brew install node", "linux": "install Node 22 from https://nodejs.org or with nvm",
             "windows": "winget install OpenJS.NodeJS"},
}


def out(mark, what, detail=""):
    print(f"{mark}{what:<26} {detail}")


def version(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0]
    except (OSError, IndexError, subprocess.TimeoutExpired):
        return None


def main(quick=False):
    need_fix = []
    print("Software")
    py = sys.version_info
    out(OK if py >= (3, 10) else BAD, "Python", f"{py.major}.{py.minor} ({sys.executable})")
    if not (ROOT / ".venv").exists():
        out(WARN, "virtual env", "none yet: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    missing = [m for m in ("numpy", "PIL", "certifi") if not _has(m)]
    out(BAD if missing else OK, "Python packages", f"missing {', '.join(missing)}: .venv/bin/pip install -r requirements.txt" if missing else "numpy, pillow, certifi")
    need_fix += missing
    ff = version(["ffmpeg", "-hide_banner", "-encoders"]) is not None and shutil.which("ffprobe")
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout if ff else ""
    if not ff:
        out(BAD, "ffmpeg + ffprobe", "missing: " + INSTALL["ffmpeg"][OSN]); need_fix.append("ffmpeg")
    else:
        out(OK if "libx264" in enc else BAD, "ffmpeg", "with libx264" if "libx264" in enc else "built without libx264 - install a full build")
    nv = version(["node", "--version"])
    nok = bool(nv) and tuple(int(x) for x in re.findall(r"\d+", nv)[:2]) >= (22, 6)
    out(OK if nok else WARN, "Node.js (cartoon kit)", nv if nok else f"{nv or 'missing'} - needs 22.6+ for animated reels: {INSTALL['node'][OSN]}")

    print("\nFonts (found automatically; set your own in config.local.json \"fonts\")")
    for k in ("text", "label", "emoji"):
        p = CFG["fonts"].get(k)
        out(OK if p else BAD, f"{k} font", p or "none found - install a heavy sans / colour emoji font, or set the path")
        if not p:
            need_fix.append(f"{k} font")

    print("\nWorkspace")
    for tpl, dst in (("preferences.example.json", "preferences.json"),):
        if not (WORK / dst).exists():
            shutil.copy(WORK / tpl, WORK / dst)
            out(OK, dst, "created from the template")
        else:
            out(OK, dst, "")
    for d in ("reels", "media/episodes", "media/clips", "references", "shows"):
        (WORK / d).mkdir(parents=True, exist_ok=True)
    if not (ROOT / ".env").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")
        out(OK, ".env", "created from .env.example (fill in keys only when a step needs them)")
    act = shows.active_slug()
    slugs = shows.all_slugs()
    if not slugs:
        out(WARN, "shows", 'none yet - commentary needs one: reel.py show new "<name>" --episodes <folder>. '
                           "Animated stories don't.")
    for slug in slugs:
        s = shows.load(slug)
        eps = s.get("episodes", [])
        here = s.get("episodes_dir") and os.path.isdir(s["episodes_dir"])
        bank = (s["dir"] / "content_bank.md").exists()
        detail = (f"{len(eps)} episodes" if here else ("episodes folder missing: " + s["episodes_dir"]) if s.get("episodes_dir") else "no footage")
        detail += ", content bank" if bank else ", no content bank yet (ask Claude: make a content bank)"
        out(OK if (here or not s.get("episodes_dir")) else BAD, f"show {slug}{' (active)' if slug == act else ''}", detail)

    print("\nKits")
    for name, k in all_kits().items():
        out(OK, name, ", ".join(k["types"]))

    if not quick:
        print("\nAccounts (only needed for the step that uses them; setup steps in README > Account setup)")
        load_env()
        e = lambda k: bool(os.environ.get(k, "").split("#")[0].strip())
        out(OK if e("ELEVENLABS_API_KEY") and e("ELEVENLABS_VOICE_ID") else WARN, "ElevenLabs (voice)",
            "set" if e("ELEVENLABS_API_KEY") and e("ELEVENLABS_VOICE_ID") else "not set - or record your own mp3 (voice/tts.py --timing-only)")
        yc, yt = (ROOT / "secrets" / "youtube_client.json").exists(), (ROOT / "secrets" / "youtube_token.json").exists()
        out(OK if yc and yt else WARN, "YouTube", "signed in" if yt else ("client saved - sign in: auth/youtube.py" if yc else "not set up"))
        ig = e("INSTAGRAM_ACCESS_TOKEN")
        out(OK if ig and e("INSTAGRAM_USER_ID") else WARN, "Instagram", "token and account id set" if ig and e("INSTAGRAM_USER_ID")
            else ("token set - run auth/instagram.py" if ig else "not set up"))

    print("\n" + ("Ready." if not need_fix else "Fix the XX lines above first."))
    return 1 if need_fix else 0


def _has(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False
