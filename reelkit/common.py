"""Shared helpers: project paths, config, .env, episode lookup."""
import glob, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text())


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


def episode(ep):
    """Episode number (10 or 'EP10') -> path of the full episode file."""
    n = int(str(ep).upper().replace("EP", ""))
    hits = glob.glob(os.path.join(CFG["episodes_dir"], CFG["episode_glob"].format(ep=n)))
    if not hits:
        raise SystemExit(f"Episode {n} not found in {CFG['episodes_dir']}")
    return hits[0]


def source(spec):
    """'EP10' -> episode file; anything else is a path (absolute, or a file name in the clips dirs)."""
    if str(spec).upper().startswith("EP"):
        return episode(spec)
    if os.path.isabs(spec):
        return spec
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
