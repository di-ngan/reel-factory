#!/usr/bin/env python3
"""One entry point for every reel kit. The kit is picked from the reel's reel.json ("kit", or the kit that makes its "type").

  reel.py doctor                        # check this computer: software, fonts, workspace, shows, accounts
  reel.py show new "Name" --episodes DIR [--clips DIR ...] [--tags a,b]   # add a show (no --episodes: no footage)
  reel.py show list | use <show> | scan [<show>]          # list shows, switch the active one, re-read episode files
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


def show_cmd(a):
    import argparse
    from core import shows
    from core.common import WORK
    if not a or a[0] == "list":
        act = shows.active_slug()
        for slug in shows.all_slugs():
            s = shows.load(slug)
            eps = f"{len(s.get('episodes', []))} episodes" if s.get("episodes_dir") else "no footage"
            print(f"{'*' if slug == act else ' '} {slug:<22} {s['name']}  ({eps})")
        if not shows.all_slugs():
            print('No shows yet. Add one: reel.py show new "<name>" --episodes <folder>   (or without --episodes)')
        return
    if a[0] == "new":
        ap = argparse.ArgumentParser(prog="reel.py show new")
        ap.add_argument("name"); ap.add_argument("--episodes"); ap.add_argument("--clips", nargs="*", default=[])
        ap.add_argument("--tags", default="")
        o = ap.parse_args(a[1:])
        s = shows.create(o.name, o.episodes, o.clips, [t.strip().lstrip("#") for t in o.tags.split(",") if t.strip()])
        use(s["slug"])
        return describe(s)
    if a[0] == "use" and len(a) == 2:
        shows.load(a[1]); use(a[1]); return print(f"active show: {a[1]}")
    if a[0] == "scan":
        s = shows.load(a[1] if len(a) > 1 else None)
        if not s or not s.get("episodes_dir"):
            raise SystemExit("That show has no episodes folder.")
        shows.save(shows.rescan(s))
        return describe(s)
    raise SystemExit(__doc__)


def use(slug):
    from core.common import WORK
    p = WORK / "preferences.json"
    src = p if p.exists() else WORK / "preferences.example.json"
    j = json.loads(src.read_text())
    j["show"] = slug
    p.write_text(json.dumps(j, indent=2) + "\n")


def describe(s):
    print(f"show '{s['slug']}' ({s['name']}) -> workspace/shows/{s['slug']}/")
    if s.get("episodes"):
        e = s["episodes"]
        print(f"  {len(e)} episodes: EP1 = {e[0][2]}  ...  EP{e[-1][0]} = {e[-1][2]}")
        print(f"  audio tracks {s['audio_tracks']}; under the voice: {s['under_track']}; lines in the clear: {s['clear_track']}")
        print(f"  subtitles: {'stream ' + str(s['subtitle_stream']) if s.get('subtitle_stream') is not None else 'none in the files'}")
        print("  Check the numbering above. Wrong order or language? Edit show.json, or rename the files and run reel.py show scan.")
    else:
        print("  no footage - good for animated story and retelling reels")


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
    from core.shows import active_slug
    j = {"kit": kit["name"], "type": rtype, "title": d.name, "voice": "voice.mp3"}
    if active_slug() and rtype != "story":          # original stories don't belong to a show
        j["show"] = active_slug()
    (d / "reel.json").write_text(json.dumps(j, indent=2) + "\n")
    print(f"created {d} (kit {kit['name']}); next: read {(kit['dir'] / kit['guide']).relative_to(ROOT)}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    if a[0] == "kits":
        return list_kits()
    if a[0] == "doctor":
        from core.doctor import main as doctor
        raise SystemExit(doctor(quick="--quick" in a))
    if a[0] == "show":
        return show_cmd(a[1:])
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
