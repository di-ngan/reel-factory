"""Synthesized music bed and SFX for cartoon reels. A reel's audio.py builds a cue list with these and calls
write_stems(); build.py then mixes the stems under the voice at locked levels (never mix here).

    from sound import *
    S = Stems(duration_s)
    S.music(march(S.dur, stop=14.15))            # or calm(...), drone(...), or several layers
    S.sfx(whoosh(0.6), 0.6, 0.5)                 # sound, time in s, relative gain
    S.write()                                    # -> work/music.wav, work/sfx.wav
"""
import wave
import numpy as np

SR = 48000
_rng = np.random.default_rng(7)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)


# ---------- building blocks ----------
def _t(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return _rng.standard_normal(int(d * SR)).astype(np.float32)


def lp(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / cutoff) ** 4), len(x)).astype(np.float32)


def hp(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (1 - 1 / (1 + (f / cutoff) ** 4)), len(x)).astype(np.float32)


def env(d, a=0.005, r=0.2):
    t = _t(d)
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def pluck(f, d=0.35, bright=0.5):
    t = _t(d)
    s = sum((bright ** k) * np.sin(2 * np.pi * f * (k + 1) * t) / (k + 1) for k in range(6))
    return (s * env(d, 0.003, d * 0.35)).astype(np.float32)


def brass(fs, d):
    t = _t(d); s = np.zeros(len(t))
    for f in fs:
        ph = 2 * np.pi * f * t + 0.003 * np.sin(2 * np.pi * 5 * t)
        s += sum(np.sin((k + 1) * ph) / (k + 1) ** 1.3 for k in range(8))
    a = np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.15).clip(0)
    return lp((s * a).astype(np.float32), 1800) / len(fs)


def drum(kind):
    if kind == "kick":
        t = _t(0.35); f = 50 + 90 * np.exp(-t * 30)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)
    t = _t(0.18)
    s = _rng.standard_normal(len(t)) * np.exp(-t * 28) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 20) * 0.5
    return hp(s.astype(np.float32), 300)


def place(buf, sig, t0, gain=1.0):
    i = int(t0 * SR); j = min(len(buf), i + len(sig))
    if 0 <= i < len(buf) and j > i:
        buf[i:j] += sig[: j - i] * gain


# ---------- music beds (full-length arrays) ----------
def march(dur, stop=None, bpm=104):
    """Light comic march (kick/snare, plucked bass, brass pad). Stops at `stop` s; a low drone carries on."""
    out = np.zeros(int(dur * SR), np.float32); beat = 60 / bpm; stop = stop or dur
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (55, [55, 59, 62]), (52, [52, 56, 59])]  # Am F G E
    bar, tt = 0, 0.0
    while tt < stop:
        root, ch = prog[bar % 4]
        place(out, brass([midi(m) for m in ch], beat * 4 * 0.98), tt, 0.10)
        for b in range(4):
            tb = tt + b * beat
            if tb >= stop:
                break
            place(out, drum("kick" if b % 2 == 0 else "snare"), tb, 0.55 if b % 2 == 0 else 0.32)
            place(out, pluck(midi(root - 12), 0.4, 0.4), tb, 0.35)
            place(out, pluck(midi(ch[(b + bar) % 3] + 12), 0.22, 0.6), tb + beat / 2, 0.13)
        if bar % 2 == 1:
            for k, m in enumerate(ch):
                place(out, brass([midi(m + 12)], beat * 0.45), tt + 2 * beat + k * beat * 0.5, 0.07)
        bar += 1; tt += beat * 4
    if stop < dur:
        i0 = int((stop - 0.08) * SR); out[i0:] *= np.linspace(1, 0, len(out) - i0) ** 8
        place(out, drone(dur - stop), stop, 0.9)
    return out


def calm(dur, bpm=64):
    """Soft felt-piano and pad bed (Am-F-C-G) for explainers and quiet stories."""
    out = np.zeros(int(dur * SR), np.float32); beat = 60 / bpm
    chords = [(57, 60, 64), (53, 57, 60), (48, 55, 60), (55, 59, 62)]
    mel = [76, 72, 69, 72, 77, 72, 69, 72, 76, 72, 67, 72, 74, 71, 67, 71]
    for i in range(int(dur / (4 * beat)) + 1):
        c = chords[i % 4]; st = i * 4 * beat; d = 4 * beat * 1.15; t = _t(d)
        pad = sum(np.sin(2 * np.pi * midi(m - 12) * t) for m in c) / 3
        place(out, (pad * np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 0.6).clip(0) * 0.12).astype(np.float32), st)
        for j in range(4):
            place(out, pluck(midi(mel[(i * 4 + j) % 16]), 1.6, 0.3), st + j * beat, 0.18 if j else 0.24)
    return lp(out, 2600)


def drone(d, root=55):
    t = _t(d)
    s = (np.sin(2 * np.pi * root * t) + 0.5 * np.sin(2 * np.pi * root * 1.498 * t) + 0.3 * np.sin(2 * np.pi * root * 2.005 * t))
    return lp((s * np.minimum(1, t / 1.2) * 0.1).astype(np.float32), 600)


# ---------- SFX ----------
def whoosh(d=0.5):
    t = _t(d); return (lp(noise(d), 1500) * np.sin(np.pi * t / d) ** 2 * 0.6).astype(np.float32)
def thunk(f0=90, d=0.3):
    t = _t(d)
    return (np.sin(2 * np.pi * f0 * t * (1 + 0.6 * np.exp(-t * 40))) * np.exp(-t * 14) + lp(noise(d), 1200) * np.exp(-t * 30) * 0.5).astype(np.float32)
def rumble(d):
    t = _t(d); return (lp(noise(d), 160) * 3 * np.minimum(1, t / 0.15) * np.exp(-t / (d * 0.45))).astype(np.float32)
def crash(d=1.2):
    t = _t(d); s = np.zeros(len(t), np.float32)
    for _ in range(14):
        place(s, thunk(_rng.uniform(60, 160), 0.35), _rng.uniform(0, d * 0.6), _rng.uniform(0.3, 0.9))
    return s + lp(noise(d), 2500) * np.exp(-t * 3) * 0.25
def ting():
    t = _t(1.2); return (sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(2093, 4), (3136, 6), (4186, 8)]) * 0.3).astype(np.float32)
def sting():
    """Twist hit: low boom + noise + minor brass stab. Stop the music bed here."""
    t = _t(2.0)
    s = np.sin(2 * np.pi * 41 * t) * np.exp(-t * 1.5) * 1.2 + lp(noise(2.0), 900) * np.exp(-t * 6) * 0.8
    stab = brass([midi(45), midi(48), midi(51)], 1.4); s[: len(stab)] += stab * 2.2 * np.exp(-_t(1.4) * 2)
    return s.astype(np.float32)
def creak(d=0.6, f0=140):
    t = _t(d); ph = np.cumsum(f0 * (1 + 0.35 * np.sin(2 * np.pi * 1.3 * t / d))) / SR
    s = lp((np.mod(ph, 1) < 0.08).astype(np.float32) * (0.6 + 0.4 * _rng.random(len(t))).astype(np.float32), 2200) * np.sin(np.pi * t / d)
    return hp(s.astype(np.float32), 200) * 2.5
def snap():
    t = _t(0.5); return (hp(noise(0.5), 800) * np.exp(-t * 18) * 1.4 + np.pad(thunk(120, 0.4), (0, len(t) - int(0.4 * SR))) * 0.6).astype(np.float32)
def splash(d=1.0):
    t = _t(d); return (lp(noise(d), 4000) * np.exp(-t * 4) * np.minimum(1, t / 0.01) + lp(noise(d), 400) * np.exp(-t * 7) * 1.5).astype(np.float32)
def scrape(d=0.8):
    t = _t(d); s = noise(d) * (0.5 + 0.5 * np.sin(2 * np.pi * 13 * t)) * np.sin(np.pi * t / d)
    return (hp(lp(s, 5000), 1500) * 0.6 + np.sin(2 * np.pi * 1870 * t) * np.exp(-t * 3) * 0.2).astype(np.float32)
def snore(d=1.1):
    t = _t(d); buzz = (np.mod(np.cumsum(60 + 25 * np.sin(np.pi * t / d)) / SR, 1) < 0.3).astype(np.float32)
    return (lp(buzz * 0.5 + noise(d) * 0.15, 700) * np.sin(np.pi * t / d) ** 2).astype(np.float32)
def leaves(d):
    t = _t(d); return (hp(lp(noise(d), 6000), 2500) * (0.3 + 0.3 * np.sin(2 * np.pi * 0.7 * t) ** 2) * np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)).astype(np.float32)
def water(d):
    t = _t(d); return (lp(noise(d), 900) * 0.5 + hp(lp(noise(d), 3000), 1200) * 0.15 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t))).astype(np.float32)
def cuckoo():
    parts = []
    for f, d in [(740, 0.16), (587, 0.24)]:
        t = _t(d); parts += [np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.01) * np.exp(-t * 6), np.zeros(int(0.06 * SR))]
    return np.concatenate(parts).astype(np.float32)


# ---------- stems ----------
class Stems:
    def __init__(self, dur):
        self.dur = dur; self.n = int(dur * SR)
        self._m = np.zeros(self.n, np.float32); self._s = np.zeros(self.n, np.float32)

    def music(self, bed, gain=1.0):
        place(self._m, bed, 0, gain)

    def sfx(self, sound, t, gain=1.0):
        place(self._s, sound, t, gain)

    def write(self, folder="work"):
        for name, x in (("music", self._m), ("sfx", self._s)):
            pk = np.abs(x).max() or 1.0
            pcm = (x / pk * 0.9 * 32767).astype(np.int16)          # levels are set later by the mixer
            with wave.open(f"{folder}/{name}.wav", "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        print(f"wrote {folder}/music.wav and {folder}/sfx.wav ({self.dur:.2f}s)")
