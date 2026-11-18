# Reference reels

Reels whose **editing** you want to borrow: how fast they cut, how the text looks, zooms, sound effects, the ending.
Only the style is used - never their script, footage or wording.

## How to add one

Add a row to the table below:

| Column | What to write |
|---|---|
| **Name** | a short id, lowercase with dashes (`fast-cuts`). It becomes the folder `workspace/references/fast-cuts/` and the style name |
| **Link** | the reel's URL (Instagram, YouTube Shorts, TikTok) |
| **What I like** | the parts to copy, in your words - this tells Claude what to focus on |
| **Use for** | which reels or series should get this style (optional) |
| **Status** | leave `new`; Claude changes it to `analysed` once `style.md` and `look.json` exist |

Then either save the video yourself as `workspace/references/<name>/video.mp4`, or ask Claude
*"analyse the new reference reels"* - it will ask before downloading anything.

To use a style: say *"make the next reel in the fast-cuts style"*, or *"use fast-cuts for the Mind games series"*
(saved in `preferences.json`), or put `"style": "fast-cuts"` in a reel's `reel.json`.

## Examples (replace these with your own)

| Name | Link | What I like | Use for | Status |
|---|---|---|---|---|
| fast-cuts | https://www.instagram.com/reel/EXAMPLE1/ | a cut almost every second, one yellow keyword per card, whoosh on every card, punchy hook in the first second | Mind games series | new |
| calm-explainer | https://youtube.com/shorts/EXAMPLE2 | long slow shots, slow zoom, small text at the top, soft piano, ends on a held frame | lore / hidden-details reels | new |
| meme-edit | https://www.instagram.com/reel/EXAMPLE3/ | freeze frames with a red circle, record-scratch sound, big caption in the middle | potato-chip style meme reels | new |

## My references

| Name | Link | What I like | Use for | Status |
|---|---|---|---|---|
| | | | | |
