---
name: content-bank
description: Research a show (anime, series, film franchise) and write its content bank - reference facts, power system, characters, tier lists, key moments with clip times, trivia, debates and 30 reel ideas in multi-part series - for the make-reel skill to use. With no show, writes a bank of original story ideas for animated reels. Use for "make a content bank", "new show", "research <show>", "I have no content", "add more ideas", or "refresh the bank".
---

# Content bank

The bank is the source of truth for every reel of a show: make-reel takes ideas from it and fact-checks against its
Reference section. One per show: `workspace/shows/<show>/content_bank.md`. Format: `template.md` (keep its headings -
make-reel reads them). Run tools from the project root with `.venv/bin/python`.

## 1. Which show
- `reel.py show list`. A show the user names that isn't there: `reel.py show new "<Name>"` (`--episodes <folder>` if
  they have the files; `--tags a,b` for hashtags). Check the printed numbering and tracks with the user.
- With episodes and subtitles: `research/subs.py extract`. Subtitles are how clip times get verified - without
  them every time is marked `≈`.
- No show at all ("random stories", "I have no content") → the **Originals** bank (section 4).

## 2. Ask once (one question set, then work without stopping)
- Audience: casual fans / hardcore fans / both (and age range or region if they offer it).
- Coverage: anime only / anime + manga (or the book) / everything (novels, films, spin-offs).
- Channel angle: lore and rules, power systems and rankings, character facts, mind games - or a mix.
Skip anything the user already said. Save the answers at the top of the bank.

## 3. Research and write (show)
Research with web search (standard first; extended only when results are thin or the show is niche or recent) and
the subtitles. Look up current news: a new season, an anniversary, an adaptation - it becomes the **Timely video**.

Write the Reference first, then the ideas built on it:
1. **Overview** - creators, release dates, episode/chapter counts, canon map (canon / filler / adaptation-only),
   spoiler tiers by episode range.
2. **Writing and themes** - structure and arcs, core themes, standout techniques, common praise and criticism.
3. **World** - setting, factions, history, lore people miss.
4. **Power system** - every rule and limit, edge cases, loopholes, the misconceptions fans get wrong. Mark rules that
   are "not shown in the anime" (they go in on-screen text, not as a clip).
5. **Tier lists** - power, intelligence, threat; each placement justified by a feat with its episode/chapter;
   mark debated placements.
6. **Main characters** - role, abilities, best feats, arc, hidden details, stats (age, height, birthday) with sources.
7. **Side characters** - the same, briefer.
8. **Key moments to clip** - episode + start-end + the moment + best use.
9. **Trivia and numbers** - name meanings, symbolism, real-world references, production facts, numbers for infographics.
10. **Fan debates** - the most argued topics, both sides.
11. **Ideas** - 30, grouped into 5-7 multi-part series (a series = a recurring format, e.g. "The rules", "Mind games",
    "Power rankings", "Myth busting", "Hidden details", "What-ifs"), safe tiers first. Each idea: title, hook (first
    2 seconds), 3 beats, comment-bait close, on-screen text, and the exact clips.

Rules:
- Label the source of every fact: [anime], [manga]/[novel], [guidebook], [interview], [theory]. A theory is never
  written as canon. Unsure → "(unverified)", never a guess.
- **Clip times**: with subtitles, find each moment with `research/subs.py search "<line>"` and `show <ep> <a> <b>`
  and write the verified episode time. Without subtitles, write `≈` and say the times are unverified. Never make up
  exact seconds. Times are positions in the user's files (EPnn as in show.json), not a streaming site's.
- Short punchy lines: the bank feeds 30-60 s vertical videos.
- Text only - no contact sheets or frame grabs while building the bank (they cost the most); make-reel does that per reel.
- It is long: write the file section by section, not in one message.

## 4. Originals (no show)
For animated `story` reels: `reel.py show new "Originals"` (no episodes), then a bank of 30 original story ideas in
themed series (strange history, science, nature, myths and legends, inventions, everyday mysteries - or the user's
themes). Each idea: title, hook (the absurd fact, no setup), setting (when, where, who, one concrete detail), three
escalating beats, the twist as the last line, **true / legend** with a source link, and the 2-3 big visual moments.
Verify every "true" story with a web search; disputed ones are framed "legend says". The Reference section holds
the sources and the facts per idea. Retelling ideas for a show without footage use the show bank format with
"Scene to act out" instead of clips.

## 5. Finish
- `reel.py doctor` shows the bank next to the show. Tell the user: the series and their idea counts, the timely idea,
  what is unverified, and that `/make-reel` starts with the first `[ ]`.
- Updates later: "add 10 ideas to <series>", "refresh the news" - edit the bank in place, keep `[x]` marks and links.
- A specific video asked for here ("write the script for idea 12") is make-reel's job: hand over to it.
