#!/usr/bin/env python3
"""Publish a finished reel to Instagram Reels (Instagram Graph API, resumable upload of the local file).

  publish_instagram.py reels/reel09              # dry run
  publish_instagram.py reels/reel09 --confirm    # uploads and publishes

One-time setup (Instagram API with Instagram Login): Business/Creator account; a Meta app with the
Instagram use case; a token from the app dashboard ("Generate access tokens") in .env as
INSTAGRAM_ACCESS_TOKEN, then run tools/ig_token.py to fill INSTAGRAM_USER_ID. The token lasts
60 days and is refreshed automatically each time this script publishes.
"""
import argparse, json, subprocess, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import CFG, need
from ig_token import refresh

V = CFG["instagram"]["graph_version"]


def req(url, data=None, headers=None, method=None, raw=None):
    body = raw if raw is not None else (urllib.parse.urlencode(data).encode() if data else None)
    r = urllib.request.Request(url, data=body, headers=headers or {}, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=900) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Instagram error {e.code}: {e.read().decode()[:800]}")


def ig_copy(mp4, folder):
    """Video stream untouched; drop chapter/data tracks and metadata; AAC 128k (Instagram's audio spec)."""
    out = folder / "work" / "ig.mp4"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4), "-map", "0:v:0", "-map", "0:a:0",
                    "-map_metadata", "-1", "-map_chapters", "-1", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                    "-ar", "48000", "-movflags", "+faststart", str(out)], check=True)
    return out


def upload_chunk(url, body, headers):
    """rupload answers 206 for every chunk but the last, 200 when the file is complete."""
    r = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        if e.code == 206:
            return 206
        body = e.read().decode()[:300]
        if "ProcessingFailedError" in body:
            return False
        raise SystemExit(f"Instagram upload error {e.code}: {body}")
    except (urllib.error.URLError, OSError):
        return False                                # dropped connection: retry with a new container


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    folder = Path(a.folder)
    post = json.loads((folder / "post.json").read_text())
    mp4 = sorted((folder / "out").glob("*.mp4"))[-1]
    ig = post.get("instagram", {})
    caption = ig.get("caption", post.get("caption", "")) + "\n\n" + " ".join(
        "#" + h.lstrip("#") for h in post.get("hashtags", [])[:30])
    log = folder / "published.json"
    done = json.loads(log.read_text()) if log.exists() else {}
    print("caption:\n" + caption + "\nfile:", mp4)
    if "instagram" in done:
        raise SystemExit(f"Already published: {done['instagram']}")
    if not a.confirm:
        print("\nDry run. Add --confirm to publish."); return
    uid, tok = need("INSTAGRAM_USER_ID").split("#")[0].strip(), refresh()
    g = f"https://{CFG['instagram']['host']}/{V}"
    data = ig_copy(mp4, folder).read_bytes()
    n, chunk = len(data), 4 << 20                 # a single 20 MB POST is always rejected; chunks work
    for attempt in range(1, 6):                   # rupload's final assembly fails at random (~50%); a fresh
        cid = req(f"{g}/{uid}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                       "share_to_feed": "true", "access_token": tok})["id"]   # container fixes it
        ok = all(upload_chunk(f"https://rupload.facebook.com/ig-api-upload/{V}/{cid}", data[off:off + chunk],
                              {"Authorization": f"OAuth {tok}", "offset": str(off), "file_size": str(n)})
                 for off in range(0, n, chunk))
        if ok:
            break
        print(f"upload attempt {attempt} failed at Instagram's end; retrying with a new container")
        time.sleep(10)
    else:
        raise SystemExit("Instagram rejected the upload 5 times; nothing was published. Try again later.")
    for _ in range(60):                       # Instagram processes the video before it can be published
        s = req(f"{g}/{cid}?" + urllib.parse.urlencode({"fields": "status_code,status", "access_token": tok}))
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise SystemExit(f"Instagram could not process the video: {s}")
        time.sleep(10)
    else:
        raise SystemExit("Timed out waiting for Instagram to process the video; rerun later.")
    p = req(f"{g}/{uid}/media_publish", {"creation_id": cid, "access_token": tok})
    info = req(f"{g}/{p['id']}?" + urllib.parse.urlencode({"fields": "permalink", "access_token": tok}))
    done["instagram"] = {"id": p["id"], "url": info.get("permalink"), "at": time.strftime("%Y-%m-%d %H:%M")}
    log.write_text(json.dumps(done, indent=1))
    print("Published:", info.get("permalink"))


if __name__ == "__main__":
    main()
