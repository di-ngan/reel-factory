#!/usr/bin/env python3
"""Measure the editing style of a reference reel, so new reels can borrow its pacing and look.

  research/style.py fast-cuts                       # analyse workspace/references/fast-cuts/video.mp4
  research/style.py path/to/video.mp4 --name fast-cuts
  research/style.py --url <link> --name fast-cuts   # download with yt-dlp first (only reels you may save)

Writes workspace/references/<name>/analysis.json (numbers) and sheet.jpg (one still per shot, labelled with time
and shot length). Claude reads those once and writes style.md (what to copy) and look.json (engine
settings, used with "style": "<name>" in reel.json). Copy the editing style, never the content.
"""
import argparse, glob, json, re, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.common import CFG, WORK, duration
from PIL import Image, ImageDraw, ImageFont

REF = WORK / "references"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", str(path)], capture_output=True, text=True)
    s = json.loads(out.stdout)["streams"][0]
    n, d = map(int, s["r_frame_rate"].split("/"))
    return s["width"], s["height"], round(n / d, 2)


def cuts(path, thresh):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", f"select='gt(scene,{thresh})',showinfo",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else None


def sheet(path, shots, out, cols=6, tw=180):
    f = ImageFont.truetype(CFG["fonts"]["label"], 14)
    tiles = []
    tmp = out.parent / "_frames"
    tmp.mkdir(exist_ok=True)
    for i, (a, b) in enumerate(shots[:48]):                     # cap the sheet: one image is enough to read
        p = tmp / f"s{i:03d}.jpg"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{(a + b) / 2:.2f}", "-i", str(path),
                        "-frames:v", "1", "-vf", f"scale={tw}:-2", str(p)], check=True)
        tiles.append((p, a, b - a))
    w, h = Image.open(tiles[0][0]).size
    S = Image.new("RGB", (cols * (w + 4), ((len(tiles) + cols - 1) // cols) * (h + 22)), "black")
    D = ImageDraw.Draw(S)
    for i, (p, a, ln) in enumerate(tiles):
        x, y = (i % cols) * (w + 4), (i // cols) * (h + 22)
        S.paste(Image.open(p), (x, y + 20))
        D.text((x + 2, y + 2), f"{a:.1f}s  {ln:.1f}s", font=f, fill="white")
    S.save(out, quality=85)
    shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?")
    ap.add_argument("--url"); ap.add_argument("--name")
    ap.add_argument("--thresh", type=float, default=0.3, help="scene-change threshold (lower = more cuts)")
    a = ap.parse_args()
    if a.url:
        if not a.name:
            raise SystemExit("--url needs --name")
        if not shutil.which("yt-dlp"):
            raise SystemExit("yt-dlp is not installed. Save the reel yourself into workspace/references/<name>/video.mp4 and pass that path.")
        d = REF / a.name
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["yt-dlp", "-f", "mp4/bv*+ba/b", "--merge-output-format", "mp4", "-o", str(d / "video.%(ext)s"), a.url], check=True)
        video = d / "video.mp4"
    elif a.video:
        video = Path(a.video).resolve()
        if not video.exists() and (REF / a.video / "video.mp4").exists():      # bare reference name
            video = REF / a.video / "video.mp4"
        d = REF / (a.name or (video.parent.name if video.parent.parent == REF else video.stem))
        d.mkdir(parents=True, exist_ok=True)
    else:
        raise SystemExit(__doc__)
    dur = duration(video)
    cs = [0.0] + [c for c in cuts(video, a.thresh) if 0.15 < c < dur - 0.1] + [dur]
    shots = [(x, y) for x, y in zip(cs, cs[1:]) if y - x > 0.05]
    lens = sorted(y - x for x, y in shots)
    w, h, fps = probe(video)
    info = {
        "file": str(video), "duration": round(dur, 2), "size": [w, h], "fps": fps,
        "shots": len(shots), "avg_shot": round(dur / len(shots), 2), "median_shot": round(lens[len(lens) // 2], 2),
        "shortest": round(lens[0], 2), "longest": round(lens[-1], 2),
        "cuts_first_3s": sum(1 for x, _ in shots[1:] if x < 3),
        "pace_by_third": [sum(1 for x, _ in shots[1:] if dur * k / 3 <= x < dur * (k + 1) / 3) for k in range(3)],
        "lufs": loudness(video),
        "shot_starts": [round(x, 2) for x, _ in shots],
    }
    (d / "analysis.json").write_text(json.dumps(info, indent=1))
    sheet(video, shots, d / "sheet.jpg")
    print(json.dumps({k: v for k, v in info.items() if k != "shot_starts"}, indent=1))
    print(f"wrote {d / 'analysis.json'} and {d / 'sheet.jpg'}")


if __name__ == "__main__":
    main()
