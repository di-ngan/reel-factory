"""Cue sheet for "The Soldier Who Never Left" (19.72 s). Copy to a reel folder and rewrite the cues for its story.
Run by `reel.py <reel> audio` (cwd = the reel folder, sound.py on the path)."""
from sound import *

F = lambda f: f / 30                     # frames -> seconds
S = Stems(592 / 30)

S.music(march(S.dur, stop=14.15))        # the march stops on the twist line, a drone carries on

S.sfx(whoosh(0.6), F(18), 0.5)           # hook camera pull-back
S.sfx(leaves(2.2), F(62), 0.35)          # the years blow past
S.sfx(thunk(85, 0.35), F(120), 1.0)      # spear stamp on "post"
S.sfx(rumble(2.2), F(176), 0.9)          # empire collapses
S.sfx(crash(1.4), F(186), 0.7)
S.sfx(whoosh(0.5), F(196), 0.35)         # rack to the soldier
S.sfx(cuckoo(), F(255), 0.35)            # "crazy"
S.sfx(whoosh(0.4), F(276), 0.6)          # time-jump flash
for k in range(2):
    S.sfx(snore(1.15), F(286) + k * 1.45, 0.45)
S.sfx(scrape(0.9), F(316), 0.6)          # helmet lifted
S.sfx(ting(), F(392), 0.55)              # the carving glints
S.sfx(sting(), 14.18, 0.85)              # "The bridge is not safe."
S.sfx(creak(0.55, 120), F(464), 0.9); S.sfx(creak(0.5, 160), F(473), 0.7)
S.sfx(whoosh(0.7), F(484), 0.5)          # crane under the deck
S.sfx(water(S.dur - F(484)), F(484), 0.35)
S.sfx(creak(0.8, 90), F(536), 1.0)
S.sfx(snap(), F(548), 0.9)               # brace breaks on "rotting"
S.sfx(splash(1.0), F(580), 0.9)

S.write()
