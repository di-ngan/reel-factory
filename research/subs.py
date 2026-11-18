#!/usr/bin/env python3
"""Subtitle index for fact-checking and finding moments.

  subs.py extract                 # extract any missing subtitles from the active show's episodes
  subs.py search "one percent"    # every line matching (regex, case-insensitive), all episodes
  subs.py search "kira" --ep 10   # one episode
  subs.py show 10 2:20 3:10       # all lines of EP10 between 2:20 and 3:10
"""
import argparse, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.common import CFG, episodes, show



def parse(path):
    rows = []
    for block in re.split(r"\n\s*\n", path.read_text(errors="ignore").replace("\r", "")):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = [t.strip() for t in lines[1].split("-->")]
            txt = re.sub(r"<[^>]+>", "", " ".join(lines[2:]))
            rows.append((sec(a), sec(b), txt))
    return rows


def sec(ts):
    h, m, s = ts.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def tsec(s):
    p = [float(x) for x in s.split(":")]
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))


def main():
    ap = argparse.ArgumentParser(epilog="Subtitles live in workspace/shows/<show>/subs. --show picks a show other than the active one.")
    ap.add_argument("--show")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("extract")
    s = sp.add_parser("search"); s.add_argument("pattern"); s.add_argument("--ep", type=int)
    sh = sp.add_parser("show"); sh.add_argument("ep", type=int); sh.add_argument("start"); sh.add_argument("end")
    a = ap.parse_args()
    if a.show:
        from core.shows import activate
        CFG["show"] = activate(a.show)
    if not show():
        raise SystemExit("No show set up yet - run: reel.py show new \"<name>\" --episodes <folder>")
    SUBS = show()["dir"] / "subs"
    SUBS.mkdir(exist_ok=True)
    if a.cmd == "extract":
        if CFG.get("subtitle_stream") is None:
            raise SystemExit("These episodes have no subtitle track. Put .srt files in " + str(SUBS) + " as EP01.srt, EP02.srt ...")
        for n, label, path in episodes():
            out = SUBS / f"EP{n:02d}.srt"
            if not out.exists():
                r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path,
                                    "-map", f"0:s:{CFG['subtitle_stream']}", str(out)])
                print(("extracted" if r.returncode == 0 else "no subtitles in"), out.name, f"({label})")
        return
    if a.cmd == "search":
        rx = re.compile(a.pattern, re.I)
        for p in sorted(SUBS.glob("EP*.srt")):
            n = int(p.stem[2:])
            if a.ep and n != a.ep:
                continue
            for t0, t1, txt in parse(p):
                if rx.search(txt):
                    print(f"EP{n:02d} {fmt(t0)}-{fmt(t1)} ({t0:.2f}s)  {txt}")
    if a.cmd == "show":
        t0, t1 = tsec(a.start), tsec(a.end)
        for s0, s1, txt in parse(SUBS / f"EP{a.ep:02d}.srt"):
            if s1 >= t0 and s0 <= t1:
                print(f"{fmt(s0)} ({s0:.2f}s)  {txt}")


if __name__ == "__main__":
    main()
