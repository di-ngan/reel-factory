#!/usr/bin/env python3
"""Upload a finished reel to YouTube as a Short (YouTube Data API v3, no extra packages).

  publish/youtube.py reel09                 # dry run: shows what would be uploaded
  publish/youtube.py reel09 --confirm       # uploads (privacy from post.json, default private)

Sign-in and setup: auth/youtube.py (runs by itself the first time you upload).
Note: until Google audits the API project, uploads are locked to private.
"""
import argparse, json, sys, time, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.common import CFG, reel_dir
from auth.youtube import access_token, sign_in

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?"); ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--auth", action="store_true")
    a = ap.parse_args()
    if a.auth:
        sign_in(); return
    if not a.folder:
        raise SystemExit(__doc__)
    folder = reel_dir(a.folder)
    post = json.loads((folder / "post.json").read_text())
    mp4 = sorted((folder / "out").glob("*.mp4"))[-1]
    yt = post.get("youtube", {})
    tags = [h.lstrip("#") for h in post.get("hashtags", [])]
    desc = yt.get("description", post.get("caption", "")) + "\n\n" + " ".join("#" + t for t in tags)
    title = yt.get("title", post["title"])
    if "#shorts" not in (title + desc).lower():
        desc += " #Shorts"
    status = {"privacyStatus": yt.get("privacy", CFG["youtube"]["default_privacy"]), "selfDeclaredMadeForKids": False}
    if yt.get("publish_at"):                      # ISO 8601, e.g. 2026-11-20T12:30:00Z (needs privacy=private)
        status["publishAt"] = yt["publish_at"]
    meta = {"snippet": {"title": title[:100], "description": desc[:5000], "tags": tags[:30],
                        "categoryId": yt.get("category_id", CFG["youtube"]["category_id"])}, "status": status}
    log = folder / "published.json"
    done = json.loads(log.read_text()) if log.exists() else {}
    print(json.dumps(meta, indent=1, ensure_ascii=False), "\nfile:", mp4)
    if "youtube" in done:
        raise SystemExit(f"Already uploaded: {done['youtube']}")
    if not a.confirm:
        print("\nDry run. Add --confirm to upload."); return
    tok = access_token()
    size = mp4.stat().st_size
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    try:
        with urllib.request.urlopen(req) as r:
            up = r.headers["Location"]
        req = urllib.request.Request(up, data=mp4.read_bytes(), method="PUT",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
        with urllib.request.urlopen(req, timeout=900) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"YouTube error {e.code}: {e.read().decode()[:800]}")
    url = f"https://youtube.com/shorts/{res['id']}"
    done["youtube"] = {"id": res["id"], "url": url, "privacy": status["privacyStatus"], "at": time.strftime("%Y-%m-%d %H:%M")}
    log.write_text(json.dumps(done, indent=1))
    print("Uploaded:", url, f"({status['privacyStatus']})")


if __name__ == "__main__":
    main()
