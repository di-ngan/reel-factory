"""Find the fonts the cards need on this computer (macOS, Windows, Linux) when config doesn't name them.

  text   a heavy sans for the cards (Arial Black, Impact, DejaVu Sans Bold...)
  label  a bold sans for contact-sheet labels
  emoji  a colour emoji font, with the size it renders at (bitmap emoji fonts have one fixed size)
"""
import os, shutil, subprocess

CANDIDATES = {
    "text": ["/System/Library/Fonts/Supplemental/Arial Black.ttf", "/Library/Fonts/Arial Black.ttf",
             "/System/Library/Fonts/Supplemental/Impact.ttf", "C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/impact.ttf",
             "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf", "/usr/share/fonts/truetype/msttcorefonts/ariblk.ttf"],
    "label": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "emoji": ["/System/Library/Fonts/Apple Color Emoji.ttc", "C:/Windows/Fonts/seguiemj.ttf",
              "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf",
              "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf"],
}
FC = {"text": "sans:weight=black", "label": "sans:bold", "emoji": "emoji:color=true"}
EMOJI_SIZE = {"Apple Color Emoji.ttc": 160, "NotoColorEmoji.ttf": 109, "seguiemj.ttf": 109}


def find(kind):
    for p in CANDIDATES[kind]:
        if os.path.exists(p):
            return p
    if shutil.which("fc-match"):                                  # Linux / BSD: ask fontconfig
        p = subprocess.run(["fc-match", "-f", "%{file}", FC[kind]], capture_output=True, text=True).stdout.strip()
        if p and os.path.exists(p):
            return p
    return None


def fill_fonts(fonts):
    """Keep fonts set in config (if the file exists); find the rest. Missing ones stay None (reel.py doctor says so)."""
    out = dict(fonts)
    for kind in ("text", "label", "emoji"):
        if not (out.get(kind) and os.path.exists(out[kind])):
            out[kind] = find(kind)
    if out["label"] is None:
        out["label"] = out["text"]
    if not fonts.get("emoji_size") or fonts.get("emoji") != out["emoji"]:
        out["emoji_size"] = EMOJI_SIZE.get(os.path.basename(out["emoji"] or ""), 109)
    return out
