#!/usr/bin/env python3
"""Contact sheet of a source, every frame labelled with its time in seconds - for picking shots.

  sheet.py EP10 240 55             # EP10 from 240 s for 55 s, 2 frames/s -> reels/_sheets/EP10_240.jpg
  sheet.py EP10 240 55 --fps 4 --out reels/reel10/work/s1.jpg
"""
import argparse, glob, os, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import ROOT, source

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("start", type=float); ap.add_argument("dur", type=float)
ap.add_argument("--fps", type=float, default=2); ap.add_argument("--out")
a = ap.parse_args()
out = Path(a.out or ROOT / "reels" / "_sheets" / f"{Path(a.src).stem}_{int(a.start)}.jpg")
out.parent.mkdir(parents=True, exist_ok=True)
d = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(a.start), "-i", source(a.src), "-t", str(a.dur),
                "-vf", f"fps={a.fps},scale=212:-1", f"{d}/f%04d.jpg"], check=True)
fs = sorted(glob.glob(f"{d}/*.jpg")); cols = 10
w, h = Image.open(fs[0]).size
S = Image.new("RGB", (cols * (w + 3), ((len(fs) + cols - 1) // cols) * (h + 3)), "black")
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
D = ImageDraw.Draw(S)
for i, p in enumerate(fs):
    x, y = (i % cols) * (w + 3), (i // cols) * (h + 3)
    S.paste(Image.open(p), (x, y))
    D.rectangle((x, y, x + 46, y + 18), fill="black")
    D.text((x + 3, y + 1), f"{a.start + i / a.fps:.1f}", fill="yellow", font=f)
S.save(out, quality=85)
print(out, len(fs), "frames")
