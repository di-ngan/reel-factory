#!/usr/bin/env python3
"""Voiceover via the ElevenLabs API, with word timings.

  tts.py --list-voices                 # find your voice id (put it in .env as ELEVENLABS_VOICE_ID)
  tts.py reels/reel10                  # reads vo.txt -> voice.mp3 + words.json + timing.txt
  tts.py reels/reel10 --timing-only    # no API call: time an existing voice.mp3 from pauses

vo.txt is the spoken script; v3 audio tags like [serious] are allowed and are not timed as words.
timing.txt lists every word with its start time, plus each phrase (between pauses) - use these
times as the cut points in reel.json.
"""
import argparse, base64, json, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import CFG, need

API = "https://api.elevenlabs.io/v1"


def call(path, body=None):
    key = need("ELEVENLABS_API_KEY")
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"},
                                 method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:500]
        if "voices_read" in msg:
            msg += ("\nThis key cannot list voices. Either tick Voices > Read on the key at elevenlabs.io > "
                    "Developers > API Keys, or copy the voice ID from the voice page (... > Copy voice ID) into .env.")
        if "paid_plan_required" in msg:
            msg += "\nLibrary voices (like Henry) need a paid ElevenLabs plan for API use. Premade voices work on free."
        raise SystemExit(f"ElevenLabs error {e.code}: {msg}")


def words_from_alignment(al):
    """Character alignment -> [{'w', 'start', 'end'}], skipping [audio tags]."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur, in_tag = [], None, False
    for c, s, e in zip(chars, st, en):
        if c == "[":
            in_tag = True
        if in_tag:
            if c == "]":
                in_tag = False
            continue
        if c.isspace():
            if cur:
                out.append(cur); cur = None
            continue
        if cur is None:
            cur = {"w": c, "start": s, "end": e}
        else:
            cur["w"] += c; cur["end"] = e
    if cur:
        out.append(cur)
    return [w for w in out if re.search(r"\w", w["w"])]


def pauses(mp3, db=-28, d=0.12):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp3), "-af", f"silencedetect=n={db}dB:d={d}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    s = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    e = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(s, e))


def phrases(mp3, words=None):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(mp3)], capture_output=True, text=True).stdout)
    sil = pauses(mp3)
    if words:
        # a real break: long enough, and the next word starts as the silence ends
        # (quiet syllables inside a word also dip below the threshold)
        def next_start(t):
            return next((w["start"] for w in words if w["start"] >= t - 0.02), None)
        sil = [(s, e) for s, e in sil
               if e - s >= 0.18 and (n := next_start(s)) is not None and n <= e + 0.25]
    out, t = [], 0.0
    for s, e in sil:
        if s - t > 0.05:
            out.append((t, s))
        t = e
    if dur - t > 0.05:
        out.append((t, dur))
    return out, dur


def write_timing(folder, words):
    ph, dur = phrases(folder / "voice.mp3", words)
    lines = [f"duration {dur:.2f}s", "", "PHRASES (speech between pauses; cut on the start time)"]
    groups = [[] for _ in ph]
    for w in words:   # each word joins the latest phrase begun by (start + 0.25s)
        k = max([i for i, (a, _) in enumerate(ph) if a <= w["start"] + 0.25] or [0])
        groups[k].append(w["w"])
    for i, (a, b) in enumerate(ph):
        lines.append(f"  {i:2d}  {a:6.2f}-{b:6.2f}  {' '.join(groups[i])}")
    if words:
        lines += ["", "WORDS"] + [f"  {w['start']:6.2f}  {w['w']}" for w in words]
    (folder / "timing.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:len(ph) + 3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--timing-only", action="store_true")
    ap.add_argument("--voice", help="voice id (overrides ELEVENLABS_VOICE_ID)")
    a = ap.parse_args()
    if a.list_voices:
        for v in call("/voices")["voices"]:
            print(f"{v['voice_id']}  {v['name']}  ({v.get('category', '')})")
        return
    folder = Path(a.folder)
    if a.timing_only:
        write_timing(folder, [])
        return
    text = (folder / "vo.txt").read_text().strip()
    t = CFG["tts"]
    body = {"text": text, "model_id": t["model_id"], "voice_settings": t["voice_settings"]}
    vid = a.voice or need("ELEVENLABS_VOICE_ID")
    r = call(f"/text-to-speech/{vid}/with-timestamps?output_format={t['output_format']}", body)
    (folder / "voice.mp3").write_bytes(base64.b64decode(r["audio_base64"]))
    words = words_from_alignment(r.get("alignment") or r.get("normalized_alignment"))
    (folder / "words.json").write_text(json.dumps(words, indent=1))
    print(f"wrote {folder/'voice.mp3'} and {len(words)} word timings")
    write_timing(folder, words)


if __name__ == "__main__":
    main()
