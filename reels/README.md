Each reel lives in its own folder here (`reels/reel10/`). The folders are local work and are not committed;
a complete example is in [`examples/reel09`](../examples/reel09).

# reel.json

```jsonc
{
  "title": "Reel9-This-Tennis-Match-Was-An-Interrogation",   // output file name
  "voice": "voice.mp3",
  "gaps": [[50.8, 1.8]],          // [voice time, seconds of silence to insert] - for show lines in the clear
  "tail": 0.8,                    // seconds of hold after the voice ends
  "sources": {"e": "EP10"},       // key -> "EPnn" (full episode) or a clip file name / path
  "cuts": [                       // [voice time, source, source start s, src length or null, extra dB, "ja"|"en"]
    [0.00, "e", 154.0],           // defaults: natural speed, 0 dB, Japanese track
    [50.33, "e", 381.5, null, 12, "en"],   // English line, lifted 12 dB, plays in the gap
    [0.00, "e", 15.7, 0.6]        // src length = slow-mo: 0.6 s of source stretched to fit the shot
  ],
  "freeze": [64.50, "e", 469.0, 472.8, "ja"],   // last shot: plays s0..s1 then holds to the end
  "cards": [                      // on-screen text, replaced by the next card
    {"t": 0, "spans": [["THIS TENNIS MATCH", "W"], ["INTERROGATION", "R"]], "emoji": "🎾"},
    {"t": 12.0, "spans": [["{n}", "Y"], ["DAYS", "W"]], "count": [0, 780, 45, "{:03.0f}"]},   // counter
    {"t": 20.0, "spans": [["SAVE", "W"], ["<E>", null], ["HIM", "R"]], "emoji": "😱"}         // emoji placed inline
  ],
  "boosts": [[16.45, 17.05, 8]],  // lift the show audio in a window (voice times) by dB
  "orig_db": -18,                 // show audio level vs the voice
  "meter": {"on": 60.5, "off": null, "label": "L’S SUSPICION", "start": 0.0, "color": "R",
            "drops": [[60.7, 0.0, 0.01]]},        // [time, from, to] animated changes; no color = green->red
  "stamps": [12.3, 18.9],         // red FAKE stamp slams at these times (stays until the next card)
  "arrow": {"on": 21.6, "off": 24.3, "tip": [600, 980], "label": "TV!"},
  "hud": {"on": 30, "shrink": 33, "off": 38, "from": "JAPAN", "to": "KANTO", "label": "SEARCH AREA"},
  "music": {"from": 40.0, "db": -13},            // original soft piano bed
  "style": "fast-cuts",           // optional: use references/fast-cuts/look.json
  "look": {"sfx": true, "zoom": 0.08},            // optional overrides of the look (below)
  "sfx": [[33.2, "hit"], [40.0, "ting"]]          // extra sound effects: whoosh | hit | ting
}
```
Look settings (defaults in brackets; precedence: engine < config.json `look` < style < reel `look`):
`zoom` Ken Burns push per shot [0.06] · `freeze_zoom` [0.08] · `card_y` card centre in px [370] ·
`bg_blur` [28] · `bg_dim` [-0.12] · `sfx` automatic whoosh on each new card, hit on stamps, ting on meter drops
[false] · `sfx_db` effects level vs the voice [-8; peaks are always capped below the voice].

Colours: W white, R red, Y yellow, G green, B blue. Frame: 1080x1920, clip window 1080x720 at y=640,
text area above it (cards centre at y=370, or 320 while a meter shows).

# post.json
```json
{"title": "...", "caption": "...", "hashtags": ["DeathNote", "Anime"],
 "youtube": {"privacy": "private", "publish_at": null}, "instagram": {}}
```
`published.json` is written after posting and stops a reel being posted twice.
