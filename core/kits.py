"""Reel kits: every folder in reel_kits/ with a kit.json is a kit. Nothing else needs to know a kit's name.

kit.json:
  name      folder name, also what reel.json "kit" says
  types     {type: one-line description} - the reel types this kit makes (the skill offers these)
  needs     what the user must have (shown before choosing the type)
  entry     module run as `python -m reel_kits.<name>.<entry> <reel folder> [args]`
  stages    optional stage names the entry accepts (shown in `reel.py kits`)
  guide     how Claude makes this type (read by the make-reel skill)
  qa        "clip" (check only the footage window) or "full" (whole frame)
  example   a finished example reel inside the kit
"""
import json
from pathlib import Path
from core.common import ROOT

KITS = ROOT / "reel_kits"
DEFAULT = "commentary"          # reels made before kits existed have no "kit" field


def all_kits():
    out = {}
    for f in sorted(KITS.glob("*/kit.json")):
        k = json.loads(f.read_text())
        k["dir"] = f.parent
        out[k["name"]] = k
    return out


def kit_for(reel):
    """The kit that renders a reel: reel.json "kit", else the kit providing its "type", else the default."""
    j = json.loads((Path(reel) / "reel.json").read_text()) if (Path(reel) / "reel.json").exists() else {}
    kits = all_kits()
    if j.get("kit"):
        if j["kit"] not in kits:
            raise SystemExit(f"reel.json asks for kit '{j['kit']}', but reel_kits/{j['kit']}/kit.json does not exist")
        return kits[j["kit"]]
    for k in kits.values():
        if j.get("type") in k["types"] or j.get("type") in k.get("aliases", []):
            return k
    return kits[DEFAULT]
