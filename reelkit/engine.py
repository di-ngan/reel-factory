#!/usr/bin/env python3
"""Render a vertical commentary reel from reels/<id>/reel.json.

  python -m reelkit.engine reels/reel09            # text, video, audio, finish
  python -m reelkit.engine reels/reel09 text       # one stage: text | video | audio | finish

All times in reel.json are in the ORIGINAL voiceover (voice.mp3) timeline; gaps opened for
show lines are applied automatically. See reels/README.md for the reel.json format.
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import CFG, ROOT, source, duration, run

RC = CFG["render"]
FPS, W, H = RC["fps"], RC["width"], RC["height"]
VW, VH, VY = 1080, 720, RC["clip_y"]
TXT_H = 1400
FONT = CFG["fonts"]["text"]
EMOJI = ImageFont.truetype(CFG["fonts"]["emoji"], CFG["fonts"]["emoji_size"])
COL = {"W": (255, 255, 255), "R": (255, 52, 64), "Y": (255, 214, 64), "G": (70, 220, 120), "B": (90, 170, 255)}
INK = (18, 12, 20)
TRACK = {k: v for k, v in CFG["audio_tracks"].items()}
NEVER = 10 ** 9
# Style knobs. Precedence: these defaults < config.json "look" < references/<style>/look.json < reel.json "look".
LOOK = {"zoom": 0.06,          # Ken Burns push per shot (alternating in/out)
        "freeze_zoom": 0.08,   # push on the final hold
        "card_y": 370,         # centre of the text cards (y px); 50 px higher while a meter shows
        "bg_blur": 28, "bg_dim": -0.12,   # blurred background fill
        "sfx": False,          # auto SFX: whoosh on each new card, hit on stamps, ting on meter drops
        "sfx_db": -8}          # SFX level vs the voice (gated RMS); peaks capped below the voice peak


class Reel:
    def __init__(self, folder):
        self.dir = Path(folder).resolve()
        self.j = json.loads((self.dir / "reel.json").read_text())
        j = self.j
        self.gaps = sorted(j.get("gaps", []))
        self.voice_src = self.dir / j.get("voice", "voice.mp3")
        self.vdur = duration(self.voice_src)
        total = self.vdur + sum(g for _, g in self.gaps) + j.get("tail", 0.8)
        self.N = j.get("frames") or round(total * FPS)
        self.srcs = {k: source(v) for k, v in j["sources"].items()}
        self.cuts = j["cuts"]
        self.freeze = j["freeze"]
        self.FA = self.cf(self.freeze[0])
        starts = [self.cf(c[0]) for c in self.cuts] + [self.FA]
        self.segs = []
        for i, c in enumerate(self.cuts):
            t, k, s = c[0], c[1], c[2]
            ln = c[3] if len(c) > 3 else None
            db = c[4] if len(c) > 4 else 0
            tr = TRACK[c[5]] if len(c) > 5 else TRACK["ja"]
            a, b = starts[i], starts[i + 1]
            if b <= a:
                raise SystemExit(f"cut {i} at {t}s has no length - cut times must increase")
            sp = 1.0 if ln is None else ln / ((b - a) / FPS)
            self.segs.append((a, b, k, s, sp, db, tr))
        self.cards = [(self.cf(c["t"]), c) for c in j["cards"]]
        m = j.get("meter")
        self.meter = m
        self.bar_on = self.cf(m["on"]) if m else NEVER
        self.bar_off = self.cf(m["off"]) if m and m.get("off") is not None else NEVER
        self.bar_drops = [(self.cf(t), a, b) for t, a, b in m.get("drops", [])] if m else []
        self.stamps = [self.cf(t) for t in j.get("stamps", [])]
        ar = j.get("arrow")
        self.arrow = ar
        self.ar_on, self.ar_off = (self.cf(ar["on"]), self.cf(ar["off"])) if ar else (NEVER, NEVER)
        hud = j.get("hud")
        self.hud = hud
        self.hud_on, self.hud_shrink, self.hud_off = (self.cf(hud["on"]), self.cf(hud["shrink"]), self.cf(hud["off"])) if hud else (NEVER,) * 3
        self.look = {**LOOK, **CFG.get("look", {})}
        if j.get("style"):
            lf = ROOT / "references" / j["style"] / "look.json"
            if not lf.exists():
                raise SystemExit(f"style '{j['style']}' has no {lf} - run tools/style.py first")
            self.look.update(json.loads(lf.read_text()))
        self.look.update(j.get("look", {}))
        self.work = self.dir / "work"
        self.work.mkdir(exist_ok=True)

    # time mapping ---------------------------------------------------------
    def T(self, t):
        return t + sum(g for at, g in self.gaps if t >= at)

    def cf(self, t):
        return 0 if t == 0 else round(self.T(t) * FPS) - 2

    # text layer -----------------------------------------------------------
    def text(self):
        out = self.dir / "frames_txt"
        out.mkdir(exist_ok=True)
        for p in out.glob("t*.png"):
            p.unlink()
        cache = {}
        for fr in range(self.N):
            i = max(k for k, (st, _) in enumerate(self.cards) if st <= fr)
            st, c = self.cards[i]
            k = fr - st
            spans = [(s, COL.get(col, COL["W"])) for s, col in c["spans"]]
            if "count" in c:                       # {n} counts from a to b over `frames` frames
                a, b, nfr = c["count"][:3]
                fmt = c["count"][3] if len(c["count"]) > 3 else "{:,.0f}"
                e = 1 - (1 - min(1.0, k / max(1, nfr))) ** 3
                val = fmt.format(a + (b - a) * e)
                spans = [(s.replace("{n}", val), col) for s, col in spans]
            key = (i, tuple(spans))
            if key not in cache:
                cache[key] = card_image(spans, c.get("emoji"))
            src = cache[key]
            t = min(k / 7, 1.0)
            sc = 0.72 + 0.28 * back_out(t)
            a = min(k / 3, 1.0)
            layer = Image.new("RGBA", (W, TXT_H), (0, 0, 0, 0))
            im = src.resize((max(1, int(src.width * sc)), max(1, int(src.height * sc))), Image.BICUBIC)
            if a < 1:
                im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            cy = self.look["card_y"] - (50 if self.bar_on <= fr < self.bar_off else 0)
            layer.alpha_composite(im, ((W - im.width) // 2, cy - im.height // 2))
            if self.ar_on <= fr < self.ar_off:
                self.draw_arrow(layer, fr)
            if self.hud_on <= fr < self.hud_off:
                self.draw_hud(layer, fr)
            if self.bar_on <= fr < self.bar_off:
                self.draw_bar(layer, fr)
            for sf in self.stamps:
                if st <= sf <= fr:
                    stamp_on(layer, fr - sf)
            layer.save(out / f"t{fr:04d}.png", compress_level=1)

    def draw_arrow(self, layer, fr):
        ar = self.arrow
        k = fr - self.ar_on
        a = min(1.0, k / 4) * min(1.0, (self.ar_off - fr) / 3)
        bob = 14 * math.sin(k / 3.0)
        tx, ty = ar.get("tip", [600, 980])
        tx, ty = tx + bob * 0.6, ty - bob * 0.8
        im = Image.new("RGBA", (W, TXT_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        sx, sy = tx + 230, ty - 190
        red = COL["R"] + (255,)
        for wdt, col in ((30, INK + (255,)), (16, red)):
            d.line((sx, sy, tx + 26, ty - 22), fill=col, width=wdt)
        ang = math.atan2(ty - sy, tx - sx)
        for sz, col in ((92, INK + (255,)), (70, red)):
            d.polygon([(tx, ty), (tx - sz * math.cos(ang - 0.5), ty - sz * math.sin(ang - 0.5)),
                       (tx - sz * math.cos(ang + 0.5), ty - sz * math.sin(ang + 0.5))], fill=col)
        f = ImageFont.truetype(FONT, 70)
        lab = ar.get("label", "")
        d.text((sx - f.getlength(lab) / 2 + 30, sy - 90), lab, font=f, fill=COL["Y"], stroke_width=8, stroke_fill=INK)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda q: int(q * max(0.0, a))))
        layer.alpha_composite(im)

    def draw_hud(self, layer, fr):
        """Search HUD over the clip: a ring shrinking from `from` to `to` (e.g. JAPAN -> KANTO)."""
        h = self.hud
        k = fr - self.hud_on
        a = min(1.0, k / 6) * min(1.0, (self.hud_off - fr) / 4)
        t = 0.0 if fr < self.hud_shrink else min(1.0, (fr - self.hud_shrink) / 14)
        e = 1 - (1 - t) ** 3
        cx, cy = W // 2, VY + VH // 2 + 10
        r = int(300 - 230 * e)
        im = Image.new("RGBA", (W, TXT_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((0, VY, W, VY + VH), fill=(8, 10, 14, 120))
        for gx in range(0, W, 90):
            d.line((gx, VY, gx, VY + VH), fill=(200, 230, 255, 40), width=1)
        for gy in range(VY, VY + VH, 90):
            d.line((0, gy, W, gy), fill=(200, 230, 255, 40), width=1)
        sweep = (k * 9) % 360
        col = COL["Y"] + (255,) if t < 1 else COL["R"] + (255,)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=7)
        d.ellipse((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26), outline=(255, 255, 255, 70), width=2)
        d.arc((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26), sweep, sweep + 50, fill=col, width=8)
        d.line((cx - r - 60, cy, cx - r + 30, cy), fill=col, width=4); d.line((cx + r - 30, cy, cx + r + 60, cy), fill=col, width=4)
        d.line((cx, cy - r - 60, cx, cy - r + 30), fill=col, width=4); d.line((cx, cy + r - 30, cx, cy + r + 60), fill=col, width=4)
        if t >= 1:
            p = 10 + 4 * abs(((k % 16) / 8) - 1)
            d.ellipse((cx - p, cy - p, cx + p, cy + p), fill=COL["R"] + (255,))
        fs, fb = ImageFont.truetype(FONT, 38), ImageFont.truetype(FONT, 104)
        lab = h.get("label", "SEARCH AREA")
        d.text((cx - fs.getlength(lab) / 2, VY + 26), lab, font=fs, fill=(255, 255, 255, 230), stroke_width=4, stroke_fill=INK)
        word = h["from"] if t < 0.5 else h["to"]
        wc = COL["Y"] if t < 0.5 else COL["R"]
        d.text((cx - fb.getlength(word) / 2, VY + VH - 150), word, font=fb, fill=wc, stroke_width=9, stroke_fill=INK)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda q: int(q * max(0.0, a))))
        layer.alpha_composite(im)

    def bar_value(self, fr):
        v = self.meter.get("start", 1.0)
        for f0, a, b in self.bar_drops:
            if fr >= f0:
                t = min(1.0, (fr - f0) / 16)
                v = a + (b - a) * (1 - (1 - t) ** 3)
        return v

    def draw_bar(self, layer, fr):
        """Meter above the clip: lifespan, suspicion, anything 0-100%."""
        m = self.meter
        v = self.bar_value(fr)
        a = min(1.0, (fr - self.bar_on) / 5)
        x0, y0, bw, bh = 150, 566, 780, 58
        im = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if m.get("color"):
            col = COL[m["color"]]
        else:                                   # green -> amber -> red as it drains
            col = (70, 220, 120) if v > 0.6 else (255, 186, 40) if v > 0.35 else (240, 48, 56)
        shake = 0
        for f0, _, _ in self.bar_drops:
            if 0 <= fr - f0 < 8:
                shake = [0, 8, -7, 6, -4, 3, -2, 1][fr - f0]
        X = x0 + shake
        d.rounded_rectangle((X - 6, 8, X + bw + 6, 14 + bh + 6), radius=18, fill=INK + (230,))
        if v > 0:
            d.rounded_rectangle((X, 14, X + max(int(bw * v), 26), 14 + bh), radius=13, fill=col)
        f = ImageFont.truetype(FONT, 40)
        d.text((X + 18, 20), m.get("label", "LIFESPAN"), font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=INK)
        pct = f"{round(v * 100)}%"
        d.text((X + bw - 18 - f.getlength(pct), 20), pct, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=INK)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda q: int(q * a)))
        layer.alpha_composite(im, (0, y0 - 14))

    # picture --------------------------------------------------------------
    def video(self):
        ins, parts, vlab = [], [], []
        for i, (a, b, k, st, sp, _, _t) in enumerate(self.segs):
            n = b - a
            d = n / FPS * sp
            ins += ["-ss", f"{st:.3f}", "-t", f"{d + 0.6:.3f}", "-i", self.srcs[k]]
            zm = self.look["zoom"]
            z = f"1.0+{zm}*on/{n}" if i % 2 == 0 else f"{1 + zm}-{zm}*on/{n}"
            parts.append(f"[{i}:v]trim=duration={d:.4f},setpts=(PTS-STARTPTS)/{sp:.5f},"
                         f"fps={FPS},crop=720:480,scale={VW*2}:{VH*2},setsar=1,tpad=stop_mode=clone:stop_duration=0.2,"
                         f"trim=end_frame={n},zoompan=z='{z}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={VW}x{VH}:fps={FPS}[v{i}]")
            vlab.append(f"[v{i}]")
        j = len(self.segs)
        _, k, s0, s1 = self.freeze[:4]
        n = self.N - self.FA
        ins += ["-ss", f"{s0:.3f}", "-t", f"{s1 - s0:.3f}", "-i", self.srcs[k]]
        parts.append(f"[{j}:v]setpts=PTS-STARTPTS,fps={FPS},crop=720:480,scale={VW*2}:{VH*2},setsar=1,"
                     f"tpad=stop_mode=clone:stop_duration=10,trim=end_frame={n},"
                     f"zoompan=z='1+{self.look["freeze_zoom"]}*on/{n}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={VW}x{VH}:fps={FPS}[vf]")
        vlab.append("[vf]")
        parts.append(f"{''.join(vlab)}concat=n={len(vlab)}:v=1:a=0,split[m][bgsrc]")
        parts.append(f"[bgsrc]scale=-2:{H},crop={W}:{H},gblur=sigma={self.look["bg_blur"]},eq=brightness={self.look["bg_dim"]}:saturation=0.85[bg]")
        parts.append(f"[bg][m]overlay=0:{VY}[comp]")
        parts.append(f"[comp][{j+1}:v]overlay=0:0:format=auto,format=yuv420p[out]")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins,
             "-framerate", str(FPS), "-i", self.dir / "frames_txt" / "t%04d.png",
             "-filter_complex", ";".join(parts), "-map", "[out]", "-frames:v", str(self.N),
             "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(FPS),
             self.work / "picture.mp4"])

    # sound ----------------------------------------------------------------
    def voice_with_gaps(self):
        """voice.mp3 with silence opened at each gap -> work/voice.f32 (48k stereo float)."""
        sr = 48000
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", self.voice_src, "-ac", "2",
                              "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        v = np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)
        pieces, last = [], 0
        for at, g in self.gaps:
            i = int(at * sr)
            pieces += [v[last:i], np.zeros((int(g * sr), 2))]
            last = i
        pieces.append(v[last:])
        return np.concatenate(pieces)

    def audio(self):
        sr = 48000
        ins, parts, lab, offs = [], [], [], []
        f = self.freeze
        ftr = TRACK[f[4]] if len(f) > 4 else TRACK["ja"]
        allsegs = list(self.segs) + [(self.FA, self.N, f[1], f[2], 1.0, 0, ftr)]
        for i, (a, b, k, st, sp, db, tr) in enumerate(allsegs):
            d = (b - a) / FPS
            tempo = f"atempo={sp:.5f}," if abs(sp - 1) > 1e-3 and sp >= 0.5 else ""
            ins += ["-ss", f"{st:.3f}", "-t", f"{d * (sp if tempo else 1) + 0.5:.3f}", "-i", self.srcs[k]]
            parts.append(f"[{i}:a:{tr}]{tempo}atrim=duration={d:.4f},asetpts=PTS-STARTPTS,aresample={sr},apad=whole_dur={d:.4f},"
                         f"afade=t=in:d=0.012,afade=t=out:st={d-0.015:.4f}:d=0.015[a{i}]")
            lab.append(f"[a{i}]")
            offs.append((a, b, db))
        parts.append(f"{''.join(lab)}concat=n={len(lab)}:v=0:a=1[o]")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(parts),
             "-map", "[o]", "-ac", "2", "-ar", str(sr), "-f", "f32le", self.work / "orig.f32"])
        o = np.fromfile(self.work / "orig.f32", dtype="<f4").reshape(-1, 2).astype(np.float64)
        v = self.voice_with_gaps()
        n = int(round(self.N / FPS * sr))
        v = np.pad(v, ((0, max(0, n - len(v))), (0, 0)))[:n]
        o = np.pad(o, ((0, max(0, n - len(o))), (0, 0)))[:n]
        o *= gated_rms(v) / gated_rms(o) * 10 ** (self.j.get("orig_db", RC["orig_db"]) / 20)
        env = np.ones(n)
        for a, b, db in offs:
            if db:
                env[int(a / FPS * sr):min(n, int(b / FPS * sr))] = 10 ** (db / 20)
        for t0, t1, db in self.j.get("boosts", []):
            env[int(self.T(t0) * sr):int(self.T(t1) * sr)] *= 10 ** (db / 20)
        k = int(0.06 * sr)
        env = np.convolve(env, np.ones(k) / k, mode="same")
        o *= env[:, None]
        mix = v + o
        mu = self.j.get("music")
        if mu:
            m = music(n, sr, self.T(mu["from"]))
            m *= gated_rms(v) / gated_rms(m) * 10 ** (mu.get("db", -13) / 20)
            mix += m
        fx = self.sfx(n, sr)
        if fx is not None:
            fx *= gated_rms(v) / gated_rms(fx) * 10 ** (self.look["sfx_db"] / 20)
            cap = 0.7 * np.abs(v).max()                    # no hit pokes out over the narration
            if np.abs(fx).max() > cap:
                fx *= cap / np.abs(fx).max()
            mix += fx
        mix.astype("<f4").tofile(self.work / "mix.f32")

    def sfx(self, n, sr):
        """Synth SFX track: look.sfx adds the automatic cues; reel.json "sfx": [[voice time, kind], ...] adds more."""
        ev = [(self.cf(t), kind) for t, kind in self.j.get("sfx", [])]
        if self.look["sfx"]:
            ev += [(st, "whoosh") for st, _ in self.cards[1:]]
            ev += [(f, "hit") for f in self.stamps]
            ev += [(f, "ting") for f, _, _ in self.bar_drops]
        if not ev:
            return None
        out = np.zeros((n, 2))
        for f, kind in ev:
            snd = SFX[kind](sr)
            i = max(0, int(f / FPS * sr) - (int(0.12 * sr) if kind == "whoosh" else 0))   # whoosh peaks on the cut
            e = min(n, i + len(snd))
            out[i:e] += snd[:e - i, None]
        return out

    def finish(self):
        j = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", self.work / "mix.f32",
                            "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        I = float(json.loads(j[j.rindex("{"):j.rindex("}") + 1])["input_i"])
        gain = RC["target_lufs"] - I
        out = self.dir / "out" / f"{self.j['title']}.mp4"
        out.parent.mkdir(exist_ok=True)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", self.work / "picture.mp4",
             "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", self.work / "mix.f32",
             "-af", f"volume={gain:.3f}dB,alimiter=limit=0.891:level=disabled",
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
             "-movflags", "+faststart", "-shortest", out])
        print(out)
        return out


# drawing helpers ----------------------------------------------------------
def card_image(spans, emoji):
    """Centred card: phrases wrap whole, shrink to fit 4 lines / 520 px / 960 px; '<E>' places the emoji."""
    for size in range(120, 60, -4):
        f = ImageFont.truetype(FONT, size)
        sw = max(6, size // 9)
        space = f.getlength(" ")
        ew = int(size * 0.95) if emoji else 0
        items = [(w, c, ew if w == "<E>" else f.getlength(w)) for w, c in spans]
        if emoji and not any(w == "<E>" for w, _ in spans):
            items.append(("<E>", None, ew))
        lines, cur, cw = [], [], 0
        for it in items:
            add = it[2] + (space if cur else 0)
            if cur and cw + add > 940:
                lines.append((cur, cw)); cur, cw = [], 0; add = it[2]
            cur.append(it); cw += add
        lines.append((cur, cw))
        lh = int(size * 1.12)
        if len(lines) <= 4 and lh * len(lines) <= 520 and max(lw for _, lw in lines) <= 960:
            break
    img = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(sh)
    y = 30
    for line, lw in lines:
        x = (W - lw) / 2
        for w, c, wl in line:
            if w == "<E>":
                e = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
                ImageDraw.Draw(e).text((0, 0), emoji, font=EMOJI, embedded_color=True)
                e = e.crop(e.getbbox()).resize((ew, ew), Image.LANCZOS)
                img.alpha_composite(e, (int(x), int(y + (lh - ew) / 2 - size * 0.02)))
            else:
                ds.text((x, y + 9), w, font=f, fill=(0, 0, 0, 150), stroke_width=sw, stroke_fill=(0, 0, 0, 150))
                d.text((x, y), w, font=f, fill=c, stroke_width=sw, stroke_fill=INK)
            x += wl + space
        y += lh
    sh.alpha_composite(img)
    return sh


def back_out(t, s=2.2):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


_STAMP = None
def stamp_on(layer, k, word="FAKE"):
    """Red rubber stamp slammed onto the top-right of the clip."""
    global _STAMP
    if _STAMP is None:
        f = ImageFont.truetype(FONT, 132)
        tw, pad = int(f.getlength(word)), 34
        im = Image.new("RGBA", (tw + 2 * pad + 20, 230), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        red = (226, 28, 40, 255)
        d.rounded_rectangle((8, 8, im.width - 8, im.height - 8), radius=22, fill=(255, 244, 236, 235), outline=red, width=14)
        d.text((pad + 10, 22), word, font=f, fill=red)
        _STAMP = im.rotate(14, expand=True, resample=Image.BICUBIC)
    st = _STAMP
    sc = 1.9 - 0.96 * (k / 4) if k < 4 else 0.94 + 0.06 * ((k - 4) / 3) if k < 7 else 1.0
    a = min(1.0, (k + 1) / 2) * 0.97
    im = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC)
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    dx = [0, 0, 0, 0, 9, -7, 4, -2][k] if k < 8 else 0
    layer.alpha_composite(im, (W // 2 - im.width // 2 + 250 + dx, 745 - im.height // 2))


def _whoosh(sr, d=0.38):
    t = np.arange(int(d * sr)) / sr
    noise = np.random.default_rng(3).standard_normal(len(t))
    env = np.sin(np.pi * t / d) ** 2 * np.exp(-2 * t)
    a = np.exp(-2 * np.pi * (300 + 2600 * np.sin(np.pi * t / d)) / sr)   # sweeping low-pass
    y, out = 0.0, np.empty_like(noise)
    for i, x in enumerate(noise):
        y = (1 - a[i]) * x + a[i] * y; out[i] = y
    return out * env


def _hit(sr, d=0.45):
    t = np.arange(int(d * sr)) / sr
    body = np.sin(2 * np.pi * (48 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 9)
    click = np.random.default_rng(5).standard_normal(len(t)) * np.exp(-t * 120) * 0.4
    return body + click


def _ting(sr, d=0.7):
    t = np.arange(int(d * sr)) / sr
    return (np.sin(2 * np.pi * 1760 * t) + 0.5 * np.sin(2 * np.pi * 2640 * t)) * np.exp(-t * 7) * np.minimum(1, t / 0.003)


SFX = {"whoosh": _whoosh, "hit": _hit, "ting": _ting}


def gated_rms(x):
    win = 2400
    m = x.mean(1) if x.ndim > 1 else x
    blocks = m[: len(m) // win * win].reshape(-1, win)
    r = np.sqrt((blocks ** 2).mean(1) + 1e-12)
    keep = r[20 * np.log10(r) > 20 * np.log10(r.max()) - 40]
    return np.sqrt((keep ** 2).mean())


def music(n, sr, start):
    """Original soft bed: slow Am-F-C-G pad with a felt-piano line, 64 BPM, from `start` seconds."""
    out = np.zeros((n, 2))
    t0 = int(start * sr)
    beat = 60 / 64
    chords = [(57, 60, 64), (53, 57, 60), (48, 55, 60), (55, 59, 62)]
    mel = [76, 72, 69, 72, 77, 72, 69, 72, 76, 72, 67, 72, 74, 71, 67, 71]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    rng = np.random.default_rng(7)
    bar = 4 * beat
    for i in range(int((n - t0) / sr / bar) + 2):
        c = chords[i % 4]
        st = t0 + int(i * bar * sr)
        L = int(bar * 1.15 * sr)
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 1.2) * np.minimum(1, (bar * 1.15 - tt) / 0.6).clip(0, 1)
        pad = sum(np.sin(2 * np.pi * hz(m - 12) * tt + rng.uniform(0, 6)) * 0.5
                  + np.sin(2 * np.pi * hz(m - 12) * 1.003 * tt) * 0.3 for m in c) / 3
        seg = pad * env * 0.35
        e = min(n, st + L)
        if st < n:
            out[st:e, 0] += seg[:e - st]; out[st:e, 1] += seg[:e - st] * 0.92
        for jn in range(4):
            ns = st + int(jn * beat * sr)
            if ns >= n:
                break
            fq = hz(mel[(i * 4 + jn) % 16])
            tn = np.arange(int(2.2 * sr)) / sr
            note = np.sin(2 * np.pi * fq * tn) + 0.35 * np.sin(4 * np.pi * fq * tn) + 0.12 * np.sin(6 * np.pi * fq * tn)
            note *= np.exp(-tn * 2.4) * np.minimum(1, tn / 0.006) * (0.5 if jn else 0.62)
            e = min(n, ns + len(tn))
            out[ns:e, 0] += note[:e - ns] * 0.9; out[ns:e, 1] += note[:e - ns]
    fi = int(2.0 * sr); out[t0:t0 + fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(2.5 * sr); out[n - fo:] *= np.linspace(1, 0, fo)[:, None]
    a = math.exp(-2 * math.pi * 2500 / sr)          # one-pole low-pass for warmth
    from itertools import accumulate
    for ch in range(2):
        col = out[t0:, ch]
        out[t0:, ch] = list(accumulate(col, lambda y, x: (1 - a) * x + a * y, initial=0.0))[1:]
    return out


def main():
    folder = sys.argv[1]
    step = sys.argv[2] if len(sys.argv) > 2 else "all"
    r = Reel(folder)
    print(f"{r.j['title']}: {r.N} frames ({r.N / FPS:.2f}s), {len(r.segs)} cuts")
    if step in ("text", "all"):
        r.text()
    if step in ("video", "all"):
        r.video()
    if step in ("audio", "all"):
        r.audio()
    if step in ("finish", "all"):
        r.finish()


if __name__ == "__main__":
    main()
