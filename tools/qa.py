#!/usr/bin/env python3
"""Check a finished reel: length, loudness, peak, frozen/black spans (clip window, or full frame for cartoons), stills sheet.

  qa.py reels/reel09        # checks out/*.mp4, writes work/qa.jpg (1 still per second) and work/qa.json
Exit code 1 if anything fails.
"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import CFG, duration

if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
    raise SystemExit(__doc__)
folder = Path(sys.argv[1])
mp4 = sorted((folder / "out").glob("*.mp4"))[-1]
work = folder / "work"; work.mkdir(exist_ok=True)
r = {"file": str(mp4), "duration": round(duration(mp4), 2)}
e = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
summ = e[e.rindex("Summary:"):]
r["lufs"] = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
r["peak_dbfs"] = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
rj = folder / "reel.json"
kind = json.loads(rj.read_text()).get("type", "commentary") if rj.exists() else "commentary"
# commentary: check the clip window (text and background move anyway); cartoon: the whole frame
area = f"crop=1080:720:0:{CFG['render']['clip_y']}," if kind == "commentary" else ""
e = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-vf",
                    f"{area}freezedetect=n=0.001:d=0.4,blackdetect=d=0.1:pix_th=0.08",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
r["frozen_at"] = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", e)]
r["black_at"] = [float(x) for x in re.findall(r"black_start:([\d.]+)", e)]
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", mp4, "-vf",
                "fps=1,scale=270:-1,tile=10x8", "-frames:v", "1", "-update", "1", work / "qa.jpg"], check=True)
tgt = CFG["render"]["target_lufs"]
fails = []
if abs(r["lufs"] - tgt) > 1: fails.append(f"loudness {r['lufs']} LUFS (target {tgt})")
if r["peak_dbfs"] > -0.5: fails.append(f"peak {r['peak_dbfs']} dBFS")
if r["duration"] > 90: fails.append(f"{r['duration']} s is over 90 s (Reels/Shorts limit to keep)")
# the final hold is allowed to be still: ignore freezes in the last 4 s
late = r["duration"] - 4
if [t for t in r["frozen_at"] if t < late]: fails.append(f"frozen picture at {r['frozen_at']}")
if r["black_at"]: fails.append(f"black frames at {r['black_at']}")
r["fails"] = fails
(work / "qa.json").write_text(json.dumps(r, indent=1))
print(json.dumps(r, indent=1))
print("QA", "FAILED" if fails else "passed", "- stills sheet:", work / "qa.jpg")
sys.exit(1 if fails else 0)
