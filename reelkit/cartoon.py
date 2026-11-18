#!/usr/bin/env python3
"""Animated reels: a 3D toon world (three.js in headless Chromium) with 2D cartoon characters, synthesized music
and SFX, timed to the voiceover. The creative part of each reel lives in its own folder:

  reels/<id>/reel.json        {"type": "cartoon", "title": "...", "voice": "voice.mp3"}
  reels/<id>/web/story.js     shot plan, cameras, lights, world state, actors  (from kits/cartoon/example)
  reels/<id>/web/main.js      engine; the world section is rewritten per story
  reels/<id>/web/roman.js     cast drawing (outfits, poses, faces); rebuilt into toon.js automatically
  reels/<id>/audio.py         music + SFX cue sheet (kits/cartoon/sound.py)

  python -m reelkit.cartoon reels/<id> setup             # copy the engine + example, fetch three.js, Playwright
  python -m reelkit.cartoon reels/<id> stills 0,90,180   # look check -> work/stills.jpg
  python -m reelkit.cartoon reels/<id> render            # all frames -> frames/ (resumes; GPU=1 to try Metal)
  python -m reelkit.cartoon reels/<id> audio             # audio.py stems -> level-locked mix
  python -m reelkit.cartoon reels/<id> finish            # encode -> out/<title>.mp4 (-14 LUFS)
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import CFG, ROOT, duration, run

KIT = ROOT / "kits" / "cartoon"
SR, FPS = 48000, CFG["render"]["fps"]
THREE = "0.160.0"


def three_js():
    """three.js r160 module build, fetched once into kits/cartoon/lib (gitignored)."""
    dst = KIT / "lib" / "three.module.js"
    if not dst.exists():
        dst.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["npm", "pack", f"three@{THREE}", "--silent"], cwd=d, check=True, capture_output=True)
            subprocess.run(["tar", "xzf", f"three-{THREE}.tgz"], cwd=d, check=True)
            shutil.copy(Path(d) / "package" / "build" / "three.module.js", dst)
    return dst


def playwright():
    if not (KIT / "node_modules" / "playwright").exists():
        print("installing Playwright for the cartoon kit (one time)...")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent"], cwd=KIT, check=True)
        subprocess.run(["npx", "playwright", "install", "chromium"], cwd=KIT, check=True)


class Cartoon:
    def __init__(self, folder):
        self.dir = Path(folder).resolve()
        self.j = json.loads((self.dir / "reel.json").read_text())
        self.web, self.work = self.dir / "web", self.dir / "work"
        self.voice = self.dir / self.j.get("voice", "voice.mp3")
        self.work.mkdir(exist_ok=True)

    @property
    def frames(self):
        return self.j.get("frames") or round((duration(self.voice) + self.j.get("tail", 0.5)) * FPS)

    def setup(self):
        self.web.mkdir(exist_ok=True)
        (self.web / "lib").mkdir(exist_ok=True)
        for f in (KIT / "engine").iterdir():                 # never overwrite a reel's edited engine/cast files
            if not (self.web / f.name).exists():
                shutil.copy(f, self.web / f.name)
        if not (self.web / "story.js").exists():
            shutil.copy(KIT / "example" / "soldier" / "story.js", self.web / "story.js")
        if not (self.dir / "audio.py").exists():
            shutil.copy(KIT / "example" / "soldier" / "audio.py", self.dir / "audio.py")
        shutil.copy(three_js(), self.web / "lib" / "three.module.js")
        playwright()
        self.build_cast()
        print(f"ready: {self.web}\nvoice {duration(self.voice):.2f}s -> TOTAL = {self.frames} frames in story.js")

    def build_cast(self):
        """toon.js = vendor toon.ts (types stripped) + the reel's roman.js."""
        base = self.web / "toonbase.js"
        js = ("const m=require('node:module'),fs=require('fs');"
              f"fs.writeFileSync({json.dumps(str(base))},m.stripTypeScriptTypes(fs.readFileSync("
              f"{json.dumps(str(KIT / 'vendor' / 'toon.ts'))},'utf8'),{{mode:'transform'}}))")
        subprocess.run(["node", "-e", js], check=True, capture_output=True)
        (self.web / "toon.js").write_text(base.read_text() + "\n" + (self.web / "roman.js").read_text())

    def _render(self, out, spec, resume=False):
        self.build_cast()
        env = {**os.environ, "WEB": str(self.web)}
        if resume:
            env["RESUME"] = "1"
        subprocess.run(["node", str(KIT / "render.mjs"), str(out), spec], env=env, check=True)

    def stills(self, spec):
        out = self.work / "stills"
        shutil.rmtree(out, ignore_errors=True)
        self._render(out, spec)
        fs = sorted(out.glob("f*.jpg"))
        tw = 270; th = tw * 16 // 9; cols = min(6, len(fs))
        sheet = Image.new("RGB", (cols * (tw + 4), ((len(fs) + cols - 1) // cols) * (th + 24)), "black")
        d = ImageDraw.Draw(sheet); font = ImageFont.truetype(CFG["fonts"]["label"], 16)
        for i, p in enumerate(fs):
            x, y = (i % cols) * (tw + 4), (i // cols) * (th + 24)
            sheet.paste(Image.open(p).resize((tw, th)), (x, y + 22))
            d.text((x + 3, y + 3), f"f{int(p.stem[1:])}  {int(p.stem[1:]) / FPS:.2f}s", font=font, fill="white")
        sheet.save(self.work / "stills.jpg", quality=85)
        print(self.work / "stills.jpg")

    def render(self):
        self._render(self.dir / "frames", f"0-{self.frames - 1}", resume=True)

    def audio(self):
        env = {**os.environ, "PYTHONPATH": str(KIT)}
        subprocess.run([sys.executable, "audio.py"], cwd=self.dir, env=env, check=True)
        load = lambda p: np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR),
                                                       "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
        n = int(round(self.frames / FPS * SR))
        fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
        v, m, s = fit(load(self.voice)), fit(load(self.work / "music.wav")), fit(load(self.work / "sfx.wav"))
        vr, vp = gated_rms(v), np.abs(v).max()
        mdb, sdb = self.j.get("music_db", -6.0), self.j.get("sfx_db", -6.0)    # 50 % of the voice by default
        if m.any():
            m *= vr / gated_rms(m) * 10 ** (mdb / 20)
        if s.any():
            s *= min(vr / gated_rms(s) * 10 ** (sdb / 20), 0.7 * vp / np.abs(s).max())   # no hit over the narration
        db = lambda x: 20 * np.log10(max(x, 1e-9))
        print(f"music vs voice {db(gated_rms(m) / vr) if m.any() else float('-inf'):+.1f} dB, "
              f"sfx vs voice {db(gated_rms(s) / vr) if s.any() else float('-inf'):+.1f} dB, "
              f"sfx peak/voice peak {np.abs(s).max() / vp:.2f}")
        mix = v + m + s
        np.repeat(mix[:, None], 2, 1).astype("<f4").tofile(self.work / "mix.f32")

    def finish(self):
        j = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", self.work / "mix.f32",
                            "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        gain = CFG["render"]["target_lufs"] - float(json.loads(j[j.rindex("{"):j.rindex("}") + 1])["input_i"])
        out = self.dir / "out" / f"{self.j['title']}.mp4"
        out.parent.mkdir(exist_ok=True)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", self.dir / "frames" / "f%04d.jpg",
             "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", self.work / "mix.f32",
             "-af", f"volume={gain:.3f}dB,alimiter=limit=0.891:level=disabled",
             "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out])
        print(out)


def gated_rms(x):
    w = int(0.05 * SR); r = np.sqrt((x[: len(x) // w * w].reshape(-1, w) ** 2).mean(1) + 1e-12)
    return np.sqrt((r[r > r.max() * 0.01] ** 2).mean())


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    c, step = Cartoon(sys.argv[1]), sys.argv[2]
    if step == "stills":
        c.stills(sys.argv[3] if len(sys.argv) > 3 else "0")
    elif step in ("setup", "render", "audio", "finish"):
        getattr(c, step)()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
