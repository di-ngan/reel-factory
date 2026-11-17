#!/usr/bin/env python3
"""Upload a finished reel to YouTube as a Short (YouTube Data API v3, no extra packages).

  publish_youtube.py reels/reel09                 # dry run: shows what would be uploaded
  publish_youtube.py reels/reel09 --confirm       # uploads (privacy from post.json, default private)
  publish_youtube.py --auth                       # just sign in once and save the token

One-time setup: Google Cloud console -> new project -> enable "YouTube Data API v3" ->
OAuth consent screen (External, add yourself as a test user) -> Credentials -> OAuth client ID ->
"Desktop app" -> download JSON to secrets/youtube_client.json.
Note: until Google audits the project, uploads through the API are locked to private.
"""
import argparse, http.server, json, secrets, sys, time, urllib.parse, urllib.request, urllib.error, webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelkit.common import ROOT, CFG

CLIENT = ROOT / "secrets" / "youtube_client.json"
TOKEN = ROOT / "secrets" / "youtube_token.json"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def client():
    if not CLIENT.exists():
        raise SystemExit(f"Missing {CLIENT} - see the setup notes at the top of this script.")
    c = json.loads(CLIENT.read_text())
    return c.get("installed") or c.get("web")


def sign_in():
    c = client()
    state, code = secrets.token_urlsafe(16), {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                code["v"] = q.get("code", [""])[0]
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Signed in. You can close this tab.")
        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening the Google sign-in page. If it does not open, visit:\n" + url)
    webbrowser.open(url)
    while "v" not in code:
        srv.handle_request()
    tok = post_form(c["token_uri"], {"code": code["v"], "client_id": c["client_id"], "client_secret": c["client_secret"],
                                     "redirect_uri": redirect, "grant_type": "authorization_code"})
    TOKEN.parent.mkdir(exist_ok=True)
    TOKEN.write_text(json.dumps(tok))
    TOKEN.chmod(0o600)
    print("Saved", TOKEN)


def access_token():
    if not TOKEN.exists():
        sign_in()
    tok = json.loads(TOKEN.read_text())
    c = client()
    new = post_form(c["token_uri"], {"refresh_token": tok["refresh_token"], "client_id": c["client_id"],
                                     "client_secret": c["client_secret"], "grant_type": "refresh_token"})
    return new["access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?"); ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--auth", action="store_true")
    a = ap.parse_args()
    if a.auth:
        sign_in(); return
    folder = Path(a.folder)
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
