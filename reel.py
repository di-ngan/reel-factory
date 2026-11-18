#!/usr/bin/env python3
"""One entry point for every reel kit. The kit is picked from the reel's reel.json ("kit", or the kit that makes its "type").

  reel.py kits                          # list installed kits, the reel types they make, what they need
  reel.py new reel11 story              # new reel folder for a type (any type listed by `reel.py kits`)
  reel.py reel10                        # run the reel's kit (commentary: all stages)
  reel.py reel10 text                   # pass a stage and its arguments to the kit
  reel.py reel11 stills 0,90,180

Reel names are folders in workspace/reels (a full path works too). Kits live in reel_kits/<name>/ - see
reel_kits/README.md to add one.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from core.common import reel_dir
from core.kits import all_kits, kit_for


def list_kits():
    for name, k in all_kits().items():
        print(f"{name}  -  {k['title']}")
        for t, d in k["types"].items():
            print(f"    type {t:<11} {d}")
        print(f"    needs       {'; '.join(k.get('needs', [])) or 'nothing'}")
        if k.get("stages"):
            print(f"    stages      {' | '.join(k['stages'])}")
        print(f"    guide       {(k['dir'] / k['guide']).relative_to(ROOT)}\n")


def new(name, rtype):
    kits = all_kits()
    kit = next((k for k in kits.values() if rtype in k["types"]), None)
    if not kit:
        raise SystemExit(f"No kit makes '{rtype}'. Types: " + ", ".join(t for k in kits.values() for t in k["types"]))
    d = reel_dir(name)
    if (d / "reel.json").exists():
        raise SystemExit(f"{d} already has a reel.json")
    d.mkdir(parents=True, exist_ok=True)
    (d / "reel.json").write_text(json.dumps({"kit": kit["name"], "type": rtype, "title": d.name, "voice": "voice.mp3"}, indent=2) + "\n")
    print(f"created {d} (kit {kit['name']}); next: read {(kit['dir'] / kit['guide']).relative_to(ROOT)}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    if a[0] == "kits":
        return list_kits()
    if a[0] == "new":
        if len(a) != 3:
            raise SystemExit("usage: reel.py new <reel name> <type>")
        return new(a[1], a[2])
    folder = reel_dir(a[0])
    if not folder.is_dir():
        raise SystemExit(f"No reel folder {folder}")
    kit = kit_for(folder)
    cmd = [sys.executable, "-m", f"reel_kits.{kit['name']}.{kit['entry']}", str(folder), *a[1:]]
    raise SystemExit(subprocess.run(cmd, cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
