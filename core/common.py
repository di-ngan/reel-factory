"""Shared helpers for every kit and tool: project paths, config, .env, reel folders, episode lookup."""
import json, os, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_config():
    """config.json, overridden key by key by config.local.json (gitignored: your own paths and fonts)."""
    cfg = json.loads((ROOT / "config.json").read_text())
    local = ROOT / "config.local.json"
    if local.exists():
        for k, v in json.loads(local.read_text()).items():
            cfg[k] = {**cfg[k], **v} if isinstance(v, dict) and isinstance(cfg.get(k), dict) else v
    resolve = lambda p: str(p if os.path.isabs(p) else ROOT / p)      # relative paths are from the project root
    cfg["episodes_dir"] = resolve(cfg.get("episodes_dir", "workspace/media/episodes"))
    cfg["clips_dirs"] = [resolve(d) for d in cfg.get("clips_dirs", [])]
    cfg["workspace"] = resolve(cfg.get("workspace", "workspace"))
    from core.fonts import fill_fonts
    cfg["fonts"] = fill_fonts(cfg.get("fonts") or {})           # missing fonts are found on this system
    return cfg


CFG = _load_config()
WORK = Path(CFG["workspace"])        # your own files: reels/, media/, references/, subs/, content bank, preferences
REELS = WORK / "reels"


def reel_dir(arg):
    """'reel10', 'reels/reel10' or a full path -> the reel folder. Short names live in workspace/reels."""
    p = Path(arg)
    if p.exists():
        return p.resolve()
    if len(p.parts) == 1 or (len(p.parts) == 2 and p.parts[0] == "reels"):
        return (REELS / p.name).resolve()
    return p.resolve()


def load_env():
    """Read ROOT/.env into os.environ (without overriding real env vars)."""
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.split("#", 1)[0].strip() if not line.strip().startswith("#") else ""
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def need(name):
    load_env()
    v = os.environ.get(name, "")
    if not v:
        raise SystemExit(f"{name} is not set. Add it to {ROOT / '.env'} (see .env.example).")
    return v


def show():
    """The show in use (reel.json "show" after shows.for_reel(), else the active show), or None."""
    if "show" not in CFG:
        from core import shows
        CFG["show"] = shows.activate()
    return CFG["show"]


def episodes():
    """[[n, label, path], ...] of the show's episodes in watch order."""
    s = show()
    if not s or not s.get("episodes_dir"):
        raise SystemExit("No episodes set up. Add a show with: reel.py show new \"<name>\" --episodes <folder>")
    return [[n, lab, os.path.join(s["episodes_dir"], f)] for n, lab, f in s.get("episodes", [])]


def episode(ep):
    """Episode number (10 or 'EP10', watch order) -> path of the full episode file."""
    n = int(str(ep).upper().replace("EP", ""))
    hit = next((p for i, _, p in episodes() if i == n), None)
    if not hit or not os.path.exists(hit):
        raise SystemExit(f"Episode {n} not found in show '{show()['name']}' - check the folder or run: reel.py show scan")
    return hit


def source(spec):
    """'EP10' -> episode file; anything else is a path (absolute, or a file name in the clips dirs)."""
    if re.fullmatch(r"EP\d+", str(spec).upper()):
        return episode(spec)
    if os.path.isabs(spec):
        return spec
    show()                                    # the show's clip folders come first
    for d in CFG["clips_dirs"]:
        p = os.path.join(d, spec)
        if os.path.exists(p):
            return p
    raise SystemExit(f"Source not found: {spec}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def run(cmd, quiet=False):
    if not quiet:
        print(" ".join(str(c) for c in cmd)[:240], flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def _install_https_certs():
    """python.org builds of Python ship without CA certificates; use certifi's bundle for all urllib calls."""
    import ssl, urllib.request
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)))


_install_https_certs()
